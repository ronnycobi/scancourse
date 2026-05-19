from django.contrib import admin
from .models import WhatsAppSession, WhatsAppMessage


class WhatsAppMessageInline(admin.TabularInline):
    model = WhatsAppMessage
    extra = 0
    readonly_fields = ('direction', 'body', 'media_url', 'twilio_sid', 'created_at')
    can_delete = False


@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user', 'state', 'last_message_at')
    list_filter = ('state',)
    search_fields = ('phone_number', 'user__email')
    inlines = [WhatsAppMessageInline]


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'direction', 'body_preview', 'created_at')
    list_filter = ('direction',)
    search_fields = ('session__phone_number', 'body')

    def body_preview(self, obj):
        return obj.body[:80]
    body_preview.short_description = 'Body'
