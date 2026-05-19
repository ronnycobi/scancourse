from django.contrib import admin
from .models import (
    CourseOutcome, CourseSectorBreakdown, CourseTopEmployer,
    JobRole, EmploymentSector, Employer, DataSource,
)


class SectorBreakdownInline(admin.TabularInline):
    model = CourseSectorBreakdown
    extra = 1


class TopEmployerInline(admin.TabularInline):
    model = CourseTopEmployer
    extra = 1


class JobRoleInline(admin.TabularInline):
    model = JobRole
    extra = 1


@admin.register(CourseOutcome)
class CourseOutcomeAdmin(admin.ModelAdmin):
    list_display = (
        'course', 'institution', 'data_year',
        'employment_rate_12m', 'salary_entry_median', 'salary_5yr_median',
        'cohort_size', 'updated_at',
    )
    list_filter = ('data_year', 'course__field', 'institution__province')
    search_fields = ('course__name', 'institution__name')
    inlines = [SectorBreakdownInline, TopEmployerInline, JobRoleInline]
    filter_horizontal = ('sources',)
    fieldsets = (
        ('Identification', {
            'fields': ('course', 'institution', 'data_year', 'cohort_size'),
        }),
        ('Employment', {
            'fields': (
                'employment_rate_6m', 'employment_rate_12m',
                'further_study_rate', 'self_employed_rate', 'unemployment_rate',
                'avg_time_to_first_job_months', 'field_match_rate',
            ),
        }),
        ('Salary (ZAR/month)', {
            'fields': (
                ('salary_entry_p25', 'salary_entry_median', 'salary_entry_p75'),
                ('salary_5yr_p25', 'salary_5yr_median', 'salary_5yr_p75'),
                'salary_10yr_median',
            ),
        }),
        ('Quality', {
            'fields': ('job_satisfaction_score',),
        }),
        ('Provenance', {
            'fields': ('sources', 'notes'),
        }),
    )


@admin.register(EmploymentSector)
class EmploymentSectorAdmin(admin.ModelAdmin):
    list_display = ('name', 'sasic_code', 'icon_emoji')
    search_fields = ('name',)


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ('name', 'sector', 'is_jse_listed', 'headquarters_city')
    list_filter = ('sector', 'is_jse_listed')
    search_fields = ('name',)


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'publisher', 'publication_date', 'is_primary', 'sample_size')
    list_filter = ('publisher', 'is_primary')
    search_fields = ('name', 'publisher')
