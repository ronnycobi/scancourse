from django.contrib import admin
from .models import ConsentRecord, DataExportRequest, AccountDeletionRequest


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'consent_type', 'granted', 'version', 'timestamp')
    list_filter = ('consent_type', 'granted')
    search_fields = ('user__email',)
    readonly_fields = ('user', 'consent_type', 'granted', 'version', 'ip_address', 'user_agent', 'timestamp')


@admin.register(DataExportRequest)
class DataExportRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'completed_at')
    list_filter = ('status',)


@admin.register(AccountDeletionRequest)
class AccountDeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'requested_at', 'scheduled_for', 'completed_at')
    list_filter = ('status',)
    actions = ['execute_deletion']

    def execute_deletion(self, request, queryset):
        from django.utils import timezone
        for req in queryset.filter(status='pending'):
            user = req.user
            user.delete()
            req.status = 'completed'
            req.completed_at = timezone.now()
            req.save()
        self.message_user(request, f'Deleted {queryset.count()} account(s).')
    execute_deletion.short_description = 'Execute deletion (irreversible)'
