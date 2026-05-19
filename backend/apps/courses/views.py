from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Course, CourseOffering, CourseInteraction
from .serializers import CourseListSerializer, CourseDetailSerializer
from .matcher import match_courses, match_summary
from .recommender import recommend_courses
from apps.ocr.models import APSResult


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
        preferred_field = getattr(user, 'preferred_field', None) or None
        career = getattr(user, 'dream_career', None) or None

        results = match_courses(
            user_aps=user_aps,
            user_subjects=user_subjects,
            province=province,
            field=field,
            institution_type=institution_type,
            level=level,
            preferred_field=preferred_field,
            career=career,
            search=search or None,
            include_not_qualified=include_not_qualified,
            include_placeholders=include_placeholders,
            limit=limit,
        )

        # Optional post-filter by single category (after sorting, so order is preserved)
        if category and category in ('eligible', 'subject_gap', 'aps_gap', 'not_qualified'):
            results = [r for r in results if r['match']['category'] == category]

        summary = match_summary(results)

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
