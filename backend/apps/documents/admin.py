from django.contrib import admin
from .models import Document, DocumentAccessLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'document_type', 'file_size', 'is_encrypted', 'is_verified', 'created_at')
    list_filter = ('document_type', 'is_encrypted', 'is_verified')
    search_fields = ('user__email', 'title')
    readonly_fields = ('file_size', 'mime_type', 'is_encrypted', 'created_at', 'last_used_at')


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'action', 'ip_address', 'timestamp')
    list_filter = ('action',)
    readonly_fields = ('document', 'user', 'action', 'ip_address', 'user_agent', 'timestamp')
    search_fields = ('document__title', 'user__email')
