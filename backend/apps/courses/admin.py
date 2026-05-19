from django.contrib import admin
from .models import Course, CourseOffering, SubjectRequirement


class SubjectRequirementInline(admin.TabularInline):
    model = SubjectRequirement
    extra = 1


class CourseOfferingInline(admin.TabularInline):
    model = CourseOffering
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'field', 'level', 'duration_years', 'fees_per_year', 'offerings_count', 'is_active')
    list_filter = ('field', 'level', 'is_active')
    search_fields = ('name', 'description', 'career_opportunities')
    list_editable = ('is_active',)
    list_per_page = 50
    inlines = [CourseOfferingInline]
    fieldsets = (
        ('Basic info', {
            'fields': ('name', 'field', 'level', 'duration_years', 'is_active'),
        }),
        ('Details', {
            'fields': ('description', 'career_opportunities', 'modules'),
        }),
        ('Money', {
            'fields': ('fees_per_year', 'salary_min', 'salary_max'),
        }),
    )

    def offerings_count(self, obj):
        return obj.offerings.count()
    offerings_count.short_description = '# offerings'


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = (
        'course', 'institution', 'campus', 'programme_code',
        'min_aps', 'application_deadline', 'is_active',
    )
    list_filter = (
        'institution__short_name', 'institution__province',
        'institution__institution_type', 'campus', 'is_active',
    )
    search_fields = (
        'course__name', 'institution__name', 'institution__short_name',
        'campus', 'programme_code',
    )
    list_editable = ('is_active',)
    list_per_page = 100
    autocomplete_fields = ('course', 'institution')
    inlines = [SubjectRequirementInline]
