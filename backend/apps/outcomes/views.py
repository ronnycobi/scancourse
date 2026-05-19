from django.db.models import Avg, F, Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import (
    CourseOutcome, EmploymentSector, Employer, DataSource,
)
from .serializers import (
    CourseOutcomeDetailSerializer, CourseOutcomeListSerializer,
    EmploymentSectorSerializer, EmployerSerializer,
    DataSourceSerializer, CompareOutcomesSerializer,
)


# ════════════════════════════════════════════════════════════════
# Course-specific outcomes
# ════════════════════════════════════════════════════════════════

class CourseOutcomeView(APIView):
    """
    GET /api/v1/courses/:course_id/outcomes/
    Returns the most recent national outcome for the course, plus institution-specific ones.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, course_id):
        outcomes = CourseOutcome.objects.filter(
            course_id=course_id
        ).select_related('course', 'institution').prefetch_related(
            'sector_breakdown__sector', 'top_employers__employer__sector', 'job_roles', 'sources',
        ).order_by('-data_year')

        if not outcomes:
            return Response(
                {'detail': 'No outcomes data available yet for this course.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Pick the most recent national (institution=None) outcome as primary
        primary = outcomes.filter(institution__isnull=True).first() or outcomes.first()
        institution_outcomes = outcomes.filter(institution__isnull=False).order_by('institution__name')

        return Response({
            'primary': CourseOutcomeDetailSerializer(primary).data,
            'by_institution': CourseOutcomeListSerializer(institution_outcomes, many=True).data,
        })


class OutcomeDetailView(generics.RetrieveAPIView):
    """GET /api/v1/outcomes/:id/ — full detail of one outcome record."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = CourseOutcomeDetailSerializer
    queryset = CourseOutcome.objects.select_related(
        'course', 'institution',
    ).prefetch_related(
        'sector_breakdown__sector', 'top_employers__employer__sector', 'job_roles', 'sources',
    )


# ════════════════════════════════════════════════════════════════
# Field-level aggregates
# ════════════════════════════════════════════════════════════════

class FieldAggregateView(APIView):
    """
    GET /api/v1/outcomes/aggregate/?field=ict
    Returns aggregate stats across all courses in a study field.
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        field = request.query_params.get('field')
        if not field:
            return Response({'detail': 'Provide ?field=...'}, status=400)

        qs = CourseOutcome.objects.filter(
            course__field=field, institution__isnull=True,
        )
        if not qs.exists():
            return Response({'detail': 'No data for that field yet.'}, status=404)

        agg = qs.aggregate(
            avg_employment_12m=Avg('employment_rate_12m'),
            avg_entry_salary=Avg('salary_entry_median'),
            avg_5yr_salary=Avg('salary_5yr_median'),
            avg_field_match=Avg('field_match_rate'),
            avg_satisfaction=Avg('job_satisfaction_score'),
        )

        # Convert Decimals to float
        result = {k: (float(v) if v is not None else None) for k, v in agg.items()}
        result['field'] = field
        result['course_count'] = qs.count()
        result['top_courses'] = list(
            qs.order_by('-employment_rate_12m').values(
                'course_id', 'course__name', 'employment_rate_12m', 'salary_entry_median',
            )[:5]
        )
        return Response(result)


# ════════════════════════════════════════════════════════════════
# Course comparison
# ════════════════════════════════════════════════════════════════

class CompareOutcomesView(APIView):
    """
    POST /api/v1/outcomes/compare/  body: {"course_ids": [1, 2, 3]}
    Side-by-side comparison of 2-4 courses.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = CompareOutcomesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_ids = serializer.validated_data['course_ids']

        outcomes = CourseOutcome.objects.filter(
            course_id__in=course_ids, institution__isnull=True,
        ).select_related('course').order_by('-data_year')

        # One per course (most recent)
        seen = set()
        primary_per_course = []
        for o in outcomes:
            if o.course_id not in seen:
                seen.add(o.course_id)
                primary_per_course.append(o)

        return Response({
            'comparison': [
                {
                    'course_id': o.course_id,
                    'course_name': o.course.name,
                    'field': o.course.field,
                    'employment_rate_12m': float(o.employment_rate_12m) if o.employment_rate_12m else None,
                    'salary_entry_median': o.salary_entry_median,
                    'salary_5yr_median': o.salary_5yr_median,
                    'salary_10yr_median': o.salary_10yr_median,
                    'avg_time_to_first_job_months': o.avg_time_to_first_job_months,
                    'field_match_rate': float(o.field_match_rate) if o.field_match_rate else None,
                    'job_satisfaction_score': float(o.job_satisfaction_score) if o.job_satisfaction_score else None,
                    'data_year': o.data_year,
                }
                for o in primary_per_course
            ],
            'missing_courses': list(set(course_ids) - seen),
        })


# ════════════════════════════════════════════════════════════════
# Reference data
# ════════════════════════════════════════════════════════════════

class SectorListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmploymentSectorSerializer
    queryset = EmploymentSector.objects.all()


class EmployerListView(generics.ListAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EmployerSerializer
    queryset = Employer.objects.select_related('sector')

    def get_queryset(self):
        qs = super().get_queryset()
        sector = self.request.query_params.get('sector')
        if sector:
            qs = qs.filter(sector__name__iexact=sector)
        return qs


class DataSourceListView(generics.ListAPIView):
    """Public — show users where the data comes from (trust signal)."""
    permission_classes = (permissions.AllowAny,)
    serializer_class = DataSourceSerializer
    queryset = DataSource.objects.all()


# ════════════════════════════════════════════════════════════════
# Salary explorer (career-style endpoint for landing pages)
# ════════════════════════════════════════════════════════════════

class TopPayingCoursesView(APIView):
    """GET /api/v1/outcomes/top-paying/?level=entry&limit=10"""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        level = request.query_params.get('level', '5yr')
        limit = min(int(request.query_params.get('limit', 10)), 25)

        sort_field = {
            'entry': '-salary_entry_median',
            '5yr': '-salary_5yr_median',
            '10yr': '-salary_10yr_median',
        }.get(level, '-salary_5yr_median')

        outcomes = (
            CourseOutcome.objects
            .filter(institution__isnull=True)
            .select_related('course')
            .order_by(sort_field)[:limit]
        )

        return Response([
            {
                'course_id': o.course_id,
                'course_name': o.course.name,
                'field': o.course.field,
                'salary_entry_median': o.salary_entry_median,
                'salary_5yr_median': o.salary_5yr_median,
                'salary_10yr_median': o.salary_10yr_median,
                'employment_rate_12m': float(o.employment_rate_12m) if o.employment_rate_12m else None,
            }
            for o in outcomes
        ])
