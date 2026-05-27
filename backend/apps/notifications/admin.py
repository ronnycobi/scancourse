from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from .models import Notification
from .tasks import _fire


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'sent_at')
    list_filter = ('notification_type', 'is_read', 'sent_at')
    search_fields = ('user__email', 'title', 'body')
    date_hierarchy = 'sent_at'
    actions = ['mark_as_read', 'fire_test_push']

    @admin.action(description='Mark selected as read')
    def mark_as_read(self, request, queryset):
        n = queryset.update(is_read=True)
        self.message_user(request, f'{n} notification(s) marked as read.')

    @admin.action(description='🔔 Send a TEST push to the recipient (FCM)')
    def fire_test_push(self, request, queryset):
        """Re-fires the same push for each selected notification.
        Use it to verify FCM is wired up end-to-end."""
        sent = 0
        for notif in queryset.select_related('user'):
            if not notif.user.fcm_token:
                continue
            _fire(notif.user, notif.notification_type,
                  f'[TEST] {notif.title}', notif.body, notif.data)
            sent += 1
        if sent:
            self.message_user(request,
                f'Test push fired for {sent} notification(s). Check the device.',
                level=messages.SUCCESS)
        else:
            self.message_user(request,
                'No selected users have an FCM token — install the app and sign in first.',
                level=messages.WARNING)


# Custom admin actions accessible on the User list for ad-hoc pings.
@admin.action(description='🔔 Send a test push to selected users')
def send_test_push_to_users(modeladmin, request, queryset):
    sent = 0
    for user in queryset:
        if not user.fcm_token:
            continue
        _fire(user, 'general', 'Scancourse',
              'This is a test notification from Admin. 👋',
              {'admin_test': '1'})
        sent += 1
    modeladmin.message_user(request,
        f'Fired {sent} test push(es). Check device(s).',
        level=messages.SUCCESS if sent else messages.WARNING)


@admin.action(description='📧 Send a test weekly-digest EMAIL to selected users')
def send_test_digest_email(modeladmin, request, queryset):
    from .digest import send_digest
    sent = 0
    skipped = 0
    for user in queryset:
        if not user.email:
            skipped += 1
            continue
        if send_digest(user):
            sent += 1
        else:
            skipped += 1
    if sent:
        modeladmin.message_user(request,
            f'Sent test digest to {sent} user(s). '
            f'{skipped} skipped (no email or no content).',
            level=messages.SUCCESS)
    else:
        modeladmin.message_user(request,
            'Nothing sent — selected users had no email or no content for this week.',
            level=messages.WARNING)


# Bolt the actions onto the User admin (registered in apps/users/admin.py)
User = get_user_model()
try:
    user_admin = admin.site._registry[User]
    user_admin.actions = list(getattr(user_admin, 'actions', []) or []) + [
        send_test_push_to_users,
        send_test_digest_email,
    ]
except KeyError:
    pass
