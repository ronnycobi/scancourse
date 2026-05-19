from django.contrib import admin
from .models import ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'source_type', 'institution_short_name', 'status', 'course_count', 'saved_count', 'created_at')
    list_filter = ('status', 'source_type', 'institution_short_name')
    search_fields = ('source_url', 'source_filename')
    readonly_fields = ('parsed_courses', 'saved_course_ids', 'error_message', 'created_at', 'updated_at')
