from django.contrib import admin
from .models import Report, Subject, APSResult


class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 0


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file_type', 'status', 'grade', 'academic_year', 'created_at')
    list_filter = ('status', 'file_type', 'grade')
    search_fields = ('user__email', 'school_name')
    inlines = [SubjectInline]


@admin.register(APSResult)
class APSResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_aps', 'created_at')
    search_fields = ('user__email',)
