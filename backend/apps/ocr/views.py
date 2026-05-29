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

        # "Edit Marks" / manual entry is the user's single authoritative
        # hand-entered record. Replace any prior manual entry (report is
        # null) so repeated edits don't pile up — and so an edit that
        # LOWERS a mark actually takes effect instead of an old, higher
        # manual row winning the best-mark merge.
        APSResult.objects.filter(
            user=request.user, report__isnull=True
        ).delete()
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


class APSJourneyView(APIView):
    """
    GET /api/v1/ocr/aps/journey/

    Returns the user's APS progression over time, plus growth metrics
    and an "unlocked courses" count comparing their first APS to their
    latest. Used by the APS Journey screen.

    Response shape:
      {
        "current_aps": 34,
        "growth": {
          "first_aps": 28,
          "latest_aps": 34,
          "delta": 6,
          "delta_label": "+6 APS",
          "since": "2026-02-12T...",
        },
        "timeline": [
          {"date": "...", "total_aps": 28, "source_id": 1},
          {"date": "...", "total_aps": 31, "source_id": 2},
          ...
        ],
        "subject_movers": [
          {"subject": "Mathematics", "old_mark": 55, "new_mark": 70, "delta": 15},
          ...top 3
        ],
        "courses_unlocked": {
          "first_count": 312,
          "latest_count": 487,
          "delta": 175,
        }
      }
    """
    def get(self, request):
        # Only real APS results — a total_aps of 0 means OCR couldn't read
        # marks, not an actual score. Including them would start the line
        # chart at a misleading 0 and inflate the growth delta.
        results = list(
            APSResult.objects.filter(user=request.user, total_aps__gt=0)
            .order_by('created_at')
        )
        if not results:
            return Response({
                'current_aps': 0,
                'timeline': [],
                'growth': None,
                'subject_movers': [],
                'courses_unlocked': None,
            })

        first = results[0]
        latest = results[-1]

        # Timeline
        timeline = [
            {
                'date': r.created_at.isoformat(),
                'total_aps': r.total_aps,
                'source_id': r.id,
            }
            for r in results
        ]

        # Growth
        growth = {
            'first_aps': first.total_aps,
            'latest_aps': latest.total_aps,
            'delta': latest.total_aps - first.total_aps,
            'delta_label': self._delta_label(latest.total_aps - first.total_aps),
            'since': first.created_at.isoformat(),
        }

        # Subject movers — compare first report's subjects to latest's
        subject_movers = self._compute_subject_movers(first, latest)

        # Courses unlocked — how many more they qualify for now
        from apps.courses.models import CourseOffering
        first_count = CourseOffering.objects.filter(
            min_aps__lte=first.total_aps).count()
        latest_count = CourseOffering.objects.filter(
            min_aps__lte=latest.total_aps).count()
        unlocked = {
            'first_count': first_count,
            'latest_count': latest_count,
            'delta': latest_count - first_count,
        }

        return Response({
            'current_aps': latest.total_aps,
            'growth': growth if len(results) > 1 else None,
            'timeline': timeline,
            'subject_movers': subject_movers,
            'courses_unlocked': unlocked if len(results) > 1 else None,
        })

    @staticmethod
    def _delta_label(delta: int) -> str:
        if delta > 0:
            return f'+{delta} APS'
        if delta < 0:
            return f'{delta} APS'
        return 'No change'

    @staticmethod
    def _compute_subject_movers(first, latest):
        """Top 3 subjects with the biggest mark improvement between the
        first and latest APS result."""
        def name_to_mark(result):
            out = {}
            for s in (result.subjects_data or []):
                if not isinstance(s, dict):
                    continue
                name = (s.get('normalized_name') or s.get('name') or '').strip()
                mark = s.get('mark')
                try:
                    mark = int(mark)
                except (TypeError, ValueError):
                    continue
                if name and 0 <= mark <= 100:
                    out[name] = mark
            return out

        first_subjects = name_to_mark(first)
        latest_subjects = name_to_mark(latest)
        movers = []
        for name, latest_mark in latest_subjects.items():
            old = first_subjects.get(name)
            if old is None:
                continue
            delta = latest_mark - old
            if delta > 0:
                movers.append({
                    'subject': name,
                    'old_mark': old,
                    'new_mark': latest_mark,
                    'delta': delta,
                })
        movers.sort(key=lambda m: m['delta'], reverse=True)
        return movers[:3]


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
            grade=getattr(user, 'grade', '') or '',
        )
        return Response({
            'total_aps': merged['total_aps'],
            'grade': getattr(user, 'grade', '') or '',
            'plan': plan,
        })


def _gemini_improvement_plan(
    subjects, total_aps, dream_career, preferred_field, saved_courses,
    grade='',
):
    """Returns: {actions: [{title, description, impact}], summary: str}

    `grade` ('grade_10', 'grade_11', 'grade_12', 'gap_year', 'other', '')
    changes the kind of advice: pre-matric students get
    mark-improvement guidance, matrics get application strategy."""
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
        'grade': grade,
    }
    marks_locked = grade in ('grade_12', 'gap_year', 'other')

    if marks_locked:
        # Final NSC marks — coach pivots to APPLICATION strategy, not
        # "study harder". Telling a matric to improve their maths is
        # patronising and unactionable.
        prompt = f"""You are a friendly South African student advisor helping a learner who has FINISHED matric (final NSC marks are set — they CANNOT improve them now).

Their profile:
{_json.dumps(payload, ensure_ascii=False, indent=2)}

Generate exactly 3 specific, actionable next steps in this JSON shape:

{{
  "summary": "<one warm sentence acknowledging their APS and what stage they're at>",
  "actions": [
    {{"title": "Apply now", "description": "<which 2-3 SA universities/programmes they should apply to FIRST, given their APS and dream career>", "impact": "<e.g. 'Apply this week — deadlines close soon'>"}},
    {{"title": "Bursaries to chase", "description": "<2 specific bursaries that fit their APS + field — NSFAS first if APS qualifies, plus one private/corporate>", "impact": "<e.g. 'Could cover full tuition + accommodation'>"}},
    {{"title": "Backup pathway", "description": "<if their dream needs higher APS than they got: realistic alternative — diploma → bridging course → degree, OR a TVET NC(V) route, OR consider supplementary exam>", "impact": "<e.g. 'Diploma → BCom in 4-5 years'>"}}
  ]
}}

Rules:
- DO NOT tell them to study harder or improve any subject mark. Their marks are FINAL.
- Be concrete. Name actual universities, bursaries, programmes when possible.
- Each description max 240 chars.
- South African context only (NSC, APS, NSFAS, TVET, supplementary exams).
- Output ONLY the JSON, no markdown fences.
"""
    else:
        # Still in school (or grade unknown) — original "improve your marks" plan.
        prompt = f"""You are a friendly South African study coach helping a Grade 10/11 learner improve their APS BEFORE matric.

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
