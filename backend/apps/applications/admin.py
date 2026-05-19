from django.contrib import admin
from .models import Application, ApplicationDocument, ApplicationEvent


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0


class ApplicationEventInline(admin.TabularInline):
    model = ApplicationEvent
    extra = 0
    readonly_fields = ('event_date',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'course', 'status', 'deadline', 'is_priority', 'created_at')
    list_filter = ('status', 'is_priority', 'institution__province')
    search_fields = ('user__email', 'institution__name', 'application_reference')
    inlines = [ApplicationDocumentInline, ApplicationEventInline]
