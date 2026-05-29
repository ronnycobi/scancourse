import json as _json
import logging
import re as _re
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.conf import settings
from .models import Course, CourseOffering, CourseInteraction
from .serializers import CourseListSerializer, CourseDetailSerializer
from .matcher import match_courses, match_summary
from .recommender import recommend_courses
from apps.ocr.models import APSResult
from apps.ocr import gemini_vision

logger = logging.getLogger(__name__)


class CourseListView(generics.ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ('field', 'level')
    search_fields = ('name', 'description', 'career_opportunities')
    ordering_fields = ('name', 'fees_per_year')

    def get_queryset(self):
        qs = Course.objects.filter(is_active=True)
        province = self.request.query_params.get('province')
        institution_type = self.request.query_params.get('institution_type')
        min_aps = self.request.query_params.get('min_aps')
        max_aps = self.request.query_params.get('max_aps')

        if province:
            qs = qs.filter(offerings__institution__province=province)
        if institution_type:
            qs = qs.filter(offerings__institution__institution_type=institution_type)
        if min_aps:
            qs = qs.filter(offerings__min_aps__gte=min_aps)
        if max_aps:
            qs = qs.filter(offerings__min_aps__lte=max_aps)

        return qs.distinct()


class CourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Course.objects.filter(is_active=True)


class CourseMatchView(APIView):
    """
    GET /api/courses/match/

    Returns all active CourseOfferings ranked by match quality against the
    student's most recent APS result.

    Query params (all optional):
        province            – e.g. 'GP', 'WC'
        field               – e.g. 'engineering', 'health'
        institution_type    – 'university' | 'university_of_technology' | 'tvet' | 'private'
        level               – 'degree' | 'diploma' | 'certificate' | …
        category            – filter to one bucket: 'eligible' | 'subject_gap' | 'aps_gap' | 'not_qualified'
        include_not_qualified – 'true' to include clearly out-of-range offerings (default: false)
        limit               – max results (default 200)

    Response:
        {
          "aps": 32,
          "subjects": [...],
          "summary": {"eligible": 12, "subject_gap": 4, "aps_gap": 20, "not_qualified": 0},
          "results": [
            {
              "offering_id": 1,
              "course_name": "BSc Computer Science",
              "institution_name": "UCT",
              ...
              "match": {
                "category": "eligible",
                "aps_surplus": 4,
                "missing_subjects": [],
                "low_subjects": [],
                "maths_lit_blocked": false,
                "score": 82
              }
            }, ...
          ]
        }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        # Use best-marks-across-all-reports (the way SA universities compute APS).
        from apps.ocr.aggregator import best_aps_for_user
        merged = best_aps_for_user(request.user)
        if merged['report_count'] == 0:
            return Response(
                {'error': 'No APS result found. Please scan your results first.'},
                status=400,
            )

        user_aps = merged['total_aps']
        user_subjects = merged['subjects']

        # Filters
        province = request.query_params.get('province')
        field = request.query_params.get('field')
        institution_type = request.query_params.get('institution_type')
        level = request.query_params.get('level')
        category = request.query_params.get('category')
        search = (request.query_params.get('search') or '').strip().lower()
        include_not_qualified = (
            request.query_params.get('include_not_qualified', 'false').lower() == 'true'
        )
        include_placeholders = (
            request.query_params.get('include_placeholders', 'false').lower() == 'true'
        )
        try:
            limit = int(request.query_params.get('limit', 200))
        except (TypeError, ValueError):
            limit = 200

        user = request.user
        # Honour ALL of the student's chosen preferences (multi-select in
        # onboarding), falling back to the legacy singular fields.
        preferred_fields = list(getattr(user, 'preferred_fields', None) or [])
        if not preferred_fields and getattr(user, 'preferred_field', None):
            preferred_fields = [user.preferred_field]
        careers = list(getattr(user, 'dream_careers', None) or [])
        if not careers and getattr(user, 'dream_career', None):
            careers = [user.dream_career]
        preferred_provinces = list(
            getattr(user, 'preferred_study_provinces', None) or []
        )
        if not preferred_provinces and getattr(user, 'preferred_study_province', None):
            preferred_provinces = [user.preferred_study_province]

        # Evaluate broadly (the matcher iterates every offering anyway) so
        # the per-category caps below aren't starved. Without this, a global
        # `limit` filled by eligible matches (which sort first) would leave
        # the Subject-Gap / APS-Gap tabs empty even when such courses exist.
        results = match_courses(
            user_aps=user_aps,
            user_subjects=user_subjects,
            province=province,
            field=field,
            institution_type=institution_type,
            level=level,
            preferred_fields=preferred_fields,
            careers=careers,
            preferred_provinces=preferred_provinces,
            search=search or None,
            include_not_qualified=include_not_qualified,
            include_placeholders=include_placeholders,
            limit=max(limit, 5000),
        )

        # Summary reflects the true counts across everything matched.
        summary = match_summary(results)

        if category and category in ('eligible', 'subject_gap', 'aps_gap', 'not_qualified'):
            # Single-category request → just that bucket, capped to `limit`.
            results = [
                r for r in results if r['match']['category'] == category
            ][:limit]
        else:
            # No category filter (the app fetches all tabs at once) → cap
            # EACH category to `limit` so no tab starves the others.
            counts: dict[str, int] = {}
            capped = []
            for r in results:
                c = r['match']['category']
                if counts.get(c, 0) < limit:
                    capped.append(r)
                    counts[c] = counts.get(c, 0) + 1
            results = capped

        return Response({
            'aps': user_aps,
            'subjects': user_subjects,
            'summary': summary,
            'results': results,
        })


class CourseRecommendView(APIView):
    """
    GET /api/courses/recommend/

    Returns personalised + collaborative-filtered course recommendations
    for the authenticated user.

    Query params:
        limit  – max recommendations (default 20, capped at 100)
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            limit = min(int(request.query_params.get('limit', 20)), 100)
        except (TypeError, ValueError):
            limit = 20
        results = recommend_courses(request.user, limit=limit)
        return Response({'count': len(results), 'results': results})


class CourseInteractionView(APIView):
    """
    POST /api/courses/<id>/interact/  body: {"kind": "view"|"save"|"apply"}

    Records a user-course signal used by the recommender.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        kind = (request.data.get('kind') or 'view').lower()
        if kind not in dict(CourseInteraction.KIND_CHOICES):
            return Response({'error': 'invalid kind'}, status=400)
        if not Course.objects.filter(pk=pk, is_active=True).exists():
            return Response({'error': 'course not found'}, status=404)
        CourseInteraction.objects.create(
            user=request.user, course_id=pk, kind=kind,
        )
        return Response({'ok': True}, status=201)


class ExplainGapView(APIView):
    """
    GET /api/v1/courses/<id>/explain-gap/

    Plain-English "why didn't I qualify" paragraph powered by Gemini,
    grounded in the user's actual marks and the course's actual requirements.
    """
    permission_classes = (permissions.IsAuthenticated,)
    throttle_scope = 'ai_explain'

    def get(self, request, pk):
        try:
            course = Course.objects.prefetch_related('offerings').get(pk=pk, is_active=True)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found.'}, status=404)

        from apps.ocr.aggregator import best_aps_for_user
        merged = best_aps_for_user(request.user)
        if merged['total_aps'] == 0:
            return Response(
                {'detail': 'Add your marks first so we can compare.'},
                status=400,
            )

        # Pick the offering with the lowest APS requirement — that's the
        # one most likely the user would target.
        offerings = sorted(
            course.offerings.all(),
            key=lambda o: o.min_aps or 9999,
        )
        if not offerings:
            return Response(
                {'detail': 'No offerings recorded for this course.'},
                status=400,
            )
        offering = offerings[0]

        payload = {
            'course': course.name,
            'institution': offering.institution.name if offering.institution_id else None,
            'min_aps_required': offering.min_aps,
            'subject_requirements': offering.subject_requirements or [],
            'user_aps': merged['total_aps'],
            'user_subjects': [
                {'name': s.get('name'), 'mark': s.get('mark'), 'pts': s.get('aps_points')}
                for s in merged['subjects']
            ],
        }
        result = _gemini_explain_gap(payload)
        return Response(result)


def _gemini_explain_gap(payload: dict) -> dict:
    """Returns {explanation: str, action_items: [str], verdict: str}."""
    fallback = {
        'verdict': 'unknown',
        'explanation': 'AI coach is offline right now — please try again later.',
        'action_items': [],
    }
    if not gemini_vision.is_available():
        return fallback

    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    prompt = f"""You are a South African study coach helping a Grade 11/12 learner understand whether they qualify for a university course, in plain English.

The data:
{_json.dumps(payload, ensure_ascii=False, indent=2)}

Return ONLY this JSON:

{{
  "verdict": "<one of: qualify, subject_gap, aps_gap, both>",
  "explanation": "<2-3 sentences in friendly, plain English. Use 'you' / 'your'. Mention specific marks and subjects from their data. No jargon.>",
  "action_items": [
    "<short, specific action, max 100 chars — e.g. 'Push Maths from 55% to 65% for +1 APS'>",
    "<another, max 3 total>"
  ]
}}

Rules:
- If they qualify, the explanation should celebrate that and mention how much APS surplus they have.
- If they're short on APS, name the exact gap (e.g. "you need 30 APS, you have 28 — short by 2").
- If they're short on a required subject, name which one and the required level.
- Never invent marks they don't have.
- Output ONLY JSON, no markdown fences.
"""
    try:
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config={'response_mime_type': 'application/json'},
        )
        resp = model.generate_content(prompt)
        raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '',
                      (resp.text or '').strip(), flags=_re.IGNORECASE)
        data = _json.loads(raw)
        return {
            'verdict': str(data.get('verdict') or 'unknown')[:30],
            'explanation': str(data.get('explanation') or '')[:600],
            'action_items': [
                str(a)[:120] for a in (data.get('action_items') or [])[:3]
            ],
        }
    except Exception as e:
        logger.warning('Gap explainer failed: %s', e)
        return fallback
