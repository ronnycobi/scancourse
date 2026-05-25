import os
import tempfile
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Report, Subject, APSResult
from .serializers import (
    ReportUploadSerializer, ReportSerializer, SubjectUpdateSerializer,
    APSResultSerializer, ManualEntrySerializer,
)
from .tasks import process_report
from .aps_calculator import calculate_aps
from . import gemini_vision


class ReportUploadView(generics.CreateAPIView):
    serializer_class = ReportUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    throttle_scope = 'ocr_upload'

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        process_report.delay(report.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        report = Report.objects.get(id=serializer.instance.id)
        return Response(ReportSerializer(report).data, status=status.HTTP_202_ACCEPTED)


class ReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).prefetch_related('subjects', 'aps_result')


class ReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)


class SubjectVerifyView(APIView):
    def patch(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        subjects_data = request.data.get('subjects', [])
        for item in subjects_data:
            try:
                subj = report.subjects.get(id=item['id'])
                subj.name = item.get('name', subj.name)
                subj.mark = item.get('mark', subj.mark)
                subj.is_verified = True
                subj.save()
            except Subject.DoesNotExist:
                continue

        # Recalculate APS after verification
        all_subjects = [{'name': s.name, 'mark': s.mark} for s in report.subjects.all()]
        aps_data = calculate_aps(all_subjects)
        APSResult.objects.update_or_create(
            report=report,
            defaults={
                'user': request.user,
                'total_aps': aps_data['total_aps'],
                'subjects_data': aps_data['subjects'],
            }
        )

        report.status = 'verified'
        report.save(update_fields=['status'])

        return Response(ReportSerializer(report).data)


class ManualEntryView(APIView):
    def post(self, request):
        serializer = ManualEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subjects = serializer.validated_data['subjects']
        aps_data = calculate_aps(subjects)

        aps_result = APSResult.objects.create(
            user=request.user,
            total_aps=aps_data['total_aps'],
            subjects_data=aps_data['subjects'],
        )

        return Response(APSResultSerializer(aps_result).data, status=status.HTTP_201_CREATED)


class APSHistoryView(generics.ListAPIView):
    serializer_class = APSResultSerializer

    def get_queryset(self):
        return APSResult.objects.filter(user=self.request.user)


class LatestAPSView(APIView):
    """
    Returns the user's BEST-MARKS-ACROSS-ALL-REPORTS snapshot.

    SA universities calculate APS from the highest mark for each subject
    across every sitting (NSC + supp + upgrades). This endpoint does the
    same so the app always reflects the strongest possible profile.
    """
    def get(self, request):
        from .aggregator import best_aps_for_user
        merged = best_aps_for_user(request.user)
        return Response({
            'id': None,
            'total_aps': merged['total_aps'],
            'subjects_data': merged['subjects'],
            'report_count': merged['report_count'],
            'source_reports': merged['source_reports'],
            'is_merged': merged['report_count'] > 1,
            'created_at': None,
        })


class ImagePrecheckView(APIView):
    """
    Fast Gemini quality check BEFORE the user commits to an upload.
    Saves users from waiting 20s for OCR only to be told the photo was unusable.
    """
    parser_classes = (MultiPartParser, FormParser)
    throttle_scope = 'ocr_precheck'

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        if f.size > 20 * 1024 * 1024:
            return Response({'detail': 'File too large.'}, status=400)
        ext = (f.name.rsplit('.', 1)[-1] or '').lower()
        if ext not in ('pdf', 'jpg', 'jpeg', 'png', 'heic', 'webp'):
            return Response({'detail': 'Unsupported file type.'}, status=400)

        # Save to a temp file so Gemini can read it.
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
            for chunk in f.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        try:
            result = gemini_vision.precheck_image(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        # Derive a single "should upload" verdict for the client.
        result['should_upload'] = (
            result['is_report'] and result['marks_readable']
            and result['quality'] in ('good', 'glare')  # glare alone we still try
        )
        return Response(result)


class ImprovementPlanView(APIView):
    """
    Asks Gemini for a 3-action plan to close the user's APS gaps, grounded in
    their actual subject marks + saved/recommended courses.
    """
    throttle_scope = 'ai_plan'

    def get(self, request):
        from .aggregator import best_aps_for_user
        from apps.courses.models import Course

        merged = best_aps_for_user(request.user)
        if merged['total_aps'] == 0:
            return Response(
                {'detail': 'Upload a report or enter marks first.'},
                status=400,
            )

        # Look at the top APS-gap courses the user has shown interest in
        # (saved or interacted with), capped to keep the prompt small.
        from apps.users.models import SavedItem
        saved_ids = list(
            SavedItem.objects
            .filter(user=request.user, item_type='course')
            .values_list('item_id', flat=True)[:5]
        )
        saved_courses = Course.objects.filter(id__in=saved_ids).values(
            'name', 'min_aps', 'field'
        )[:5]

        user = request.user
        plan = _gemini_improvement_plan(
            subjects=merged['subjects'],
            total_aps=merged['total_aps'],
            dream_career=getattr(user, 'dream_career', '') or '',
            preferred_field=getattr(user, 'preferred_field', '') or '',
            saved_courses=list(saved_courses),
        )
        return Response({
            'total_aps': merged['total_aps'],
            'plan': plan,
        })


def _gemini_improvement_plan(
    subjects, total_aps, dream_career, preferred_field, saved_courses
):
    """Returns: {actions: [{title, description, impact}], summary: str}"""
    import json as _json
    import logging
    logger = logging.getLogger(__name__)

    fallback = {
        'actions': [],
        'summary': 'AI coach is offline — try again later.',
    }
    if not gemini_vision.is_available():
        return fallback

    import google.generativeai as genai
    from django.conf import settings
    genai.configure(api_key=settings.GEMINI_API_KEY)

    payload = {
        'aps': total_aps,
        'subjects': [
            {'name': s.get('name'), 'mark': s.get('mark'), 'pts': s.get('aps_points')}
            for s in subjects
        ],
        'dream_career': dream_career,
        'preferred_field': preferred_field,
        'goal_courses': list(saved_courses),
    }
    prompt = f"""You are a friendly South African study coach helping a Grade 11/12 learner improve their APS.

Their profile:
{_json.dumps(payload, ensure_ascii=False, indent=2)}

Generate exactly 3 specific, actionable suggestions in this JSON shape:

{{
  "summary": "<one warm, encouraging sentence about where they stand>",
  "actions": [
    {{"title": "Easiest APS gain", "description": "<concrete: which subject, current mark → target mark, why it's easiest>", "impact": "<e.g. '+1 APS'>"}},
    {{"title": "Biggest impact", "description": "<concrete: which subject swing would unlock the most courses or hit their goal_courses>", "impact": "<e.g. '+3 APS, unlocks 12 more courses'>"}},
    {{"title": "Backup pathway", "description": "<if their dream is out of reach, an alternative SA route — diploma/NCV → bridging → degree, or a related field>", "impact": "<e.g. 'Diploma → BCom in 4-5 years'>"}}
  ]
}}

Rules:
- Be concrete. Use their actual subject names and marks.
- Each description max 240 chars.
- South African context only (NSC, APS, NSFAS, TVET).
- Output ONLY the JSON, no markdown fences.
"""
    try:
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config={'response_mime_type': 'application/json'},
        )
        resp = model.generate_content(prompt)
        import re as _re
        raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '',
                      (resp.text or '').strip(), flags=_re.IGNORECASE)
        data = _json.loads(raw)
        return {
            'summary': str(data.get('summary') or '')[:280],
            'actions': [
                {
                    'title': str(a.get('title') or '')[:60],
                    'description': str(a.get('description') or '')[:280],
                    'impact': str(a.get('impact') or '')[:80],
                }
                for a in (data.get('actions') or [])[:3]
            ],
        }
    except Exception as e:
        logger.warning('Improvement plan failed: %s', e)
        return fallback
