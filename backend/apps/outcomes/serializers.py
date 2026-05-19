from rest_framework import serializers
from .models import (
    CourseOutcome, CourseSectorBreakdown, CourseTopEmployer,
    JobRole, EmploymentSector, Employer, DataSource,
)


class DataSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataSource
        fields = ('id', 'name', 'publisher', 'url', 'publication_date', 'sample_size', 'is_primary')


class EmploymentSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmploymentSector
        fields = '__all__'


class EmployerSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)

    class Meta:
        model = Employer
        fields = (
            'id', 'name', 'sector_name', 'is_jse_listed',
            'headquarters_city', 'employee_count_range', 'logo', 'website',
        )


class SectorBreakdownSerializer(serializers.ModelSerializer):
    sector_name = serializers.CharField(source='sector.name', read_only=True)
    sector_emoji = serializers.CharField(source='sector.icon_emoji', read_only=True)

    class Meta:
        model = CourseSectorBreakdown
        fields = ('sector_name', 'sector_emoji', 'percentage', 'rank')


class TopEmployerSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)

    class Meta:
        model = CourseTopEmployer
        fields = ('employer', 'rank', 'grad_count_estimate')


class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = ('title', 'rank', 'median_monthly_salary_zar', 'description')


class CourseOutcomeDetailSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_field = serializers.CharField(source='course.field', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True, allow_null=True)
    employment_level = serializers.CharField(read_only=True)
    sector_breakdown = SectorBreakdownSerializer(many=True, read_only=True)
    top_employers = TopEmployerSerializer(many=True, read_only=True)
    job_roles = JobRoleSerializer(many=True, read_only=True)
    sources = DataSourceSerializer(many=True, read_only=True)

    salary_growth = serializers.SerializerMethodField()
    summary_card = serializers.SerializerMethodField()

    class Meta:
        model = CourseOutcome
        fields = (
            'id', 'course', 'course_name', 'course_field', 'institution', 'institution_name',
            'data_year', 'cohort_size',
            'employment_rate_6m', 'employment_rate_12m', 'further_study_rate',
            'self_employed_rate', 'unemployment_rate', 'employment_level',
            'salary_entry_p25', 'salary_entry_median', 'salary_entry_p75',
            'salary_5yr_p25', 'salary_5yr_median', 'salary_5yr_p75',
            'salary_10yr_median',
            'avg_time_to_first_job_months', 'job_satisfaction_score', 'field_match_rate',
            'sector_breakdown', 'top_employers', 'job_roles', 'sources', 'notes',
            'salary_growth', 'summary_card', 'updated_at',
        )

    def get_salary_growth(self, obj):
        """Compute multipliers — useful for the salary trajectory chart."""
        entry = obj.salary_entry_median
        five = obj.salary_5yr_median
        ten = obj.salary_10yr_median
        if not entry:
            return None
        return {
            'entry': entry,
            'five_year': five,
            'ten_year': ten,
            'five_year_multiplier': round(five / entry, 2) if five else None,
            'ten_year_multiplier': round(ten / entry, 2) if ten else None,
        }

    def get_summary_card(self, obj):
        """Compact summary for the course detail screen."""
        return {
            'employment_rate': float(obj.employment_rate_12m) if obj.employment_rate_12m else None,
            'employment_level': obj.employment_level,
            'entry_salary_median': obj.salary_entry_median,
            'time_to_first_job_months': obj.avg_time_to_first_job_months,
            'data_year': obj.data_year,
            'is_national': obj.institution_id is None,
        }


class CourseOutcomeListSerializer(serializers.ModelSerializer):
    """Lightweight version for list endpoints."""
    course_name = serializers.CharField(source='course.name', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True, allow_null=True)
    employment_level = serializers.CharField(read_only=True)

    class Meta:
        model = CourseOutcome
        fields = (
            'id', 'course', 'course_name', 'institution', 'institution_name',
            'data_year', 'employment_rate_12m', 'employment_level',
            'salary_entry_median', 'salary_5yr_median',
        )


class CompareOutcomesSerializer(serializers.Serializer):
    """For 2-3 way course comparison."""
    course_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        max_length=4,
    )
