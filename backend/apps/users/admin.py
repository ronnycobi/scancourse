from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SavedItem


# Only this account can promote others to staff/superuser, change permissions,
# or assign group membership. Every other staff account sees those fields as
# read-only in the admin form, AND can't add or delete other staff/superusers.
OWNER_EMAIL = 'info@scancourse.co.za'


def _is_owner(user) -> bool:
    return bool(user and user.is_authenticated and user.email == OWNER_EMAIL)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'email', 'username', 'grade', 'province', 'onboarding_completed',
        'is_active', 'is_staff', 'is_superuser', 'created_at',
    )
    list_filter = ('grade', 'province', 'onboarding_completed', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Student Info', {'fields': ('grade', 'province', 'preferred_field', 'preferred_study_province', 'dream_career')}),
        ('App Data', {'fields': ('profile_picture', 'phone_number', 'onboarding_completed', 'fcm_token')}),
    )

    # ── Permission lock-down ──────────────────────────────────────────
    # Privileged fields: only the owner may modify these.
    _PRIVILEGED_FIELDS = ('is_staff', 'is_superuser', 'groups', 'user_permissions')

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not _is_owner(request.user):
            ro.extend(self._PRIVILEGED_FIELDS)
        return tuple(ro)

    def has_add_permission(self, request):
        # Only the owner can create accounts from the admin UI.
        # Regular signups via the mobile app still work — they go through
        # the REST API, not this admin form.
        if not _is_owner(request.user):
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Never let anyone — even the owner — delete the owner account itself.
        if obj and obj.email == OWNER_EMAIL:
            return False
        # Only the owner can delete other staff/superusers.
        if obj and (obj.is_superuser or obj.is_staff) and not _is_owner(request.user):
            return False
        return super().has_delete_permission(request, obj)

    def save_model(self, request, obj, form, change):
        # Belt-and-braces: even if a non-owner bypasses the form (e.g. via
        # devtools posting a privileged field), restore the original values
        # before saving.
        if change and not _is_owner(request.user) and obj.pk:
            try:
                original = User.objects.get(pk=obj.pk)
                obj.is_staff = original.is_staff
                obj.is_superuser = original.is_superuser
            except User.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        # M2Ms (groups, user_permissions) are persisted here.
        # Non-owners get their privileged M2M changes silently dropped.
        if change and not _is_owner(request.user):
            for formset in formsets:
                formset.save()
            return
        super().save_related(request, form, formsets, change)


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_type', 'item_id', 'saved_at')
    list_filter = ('item_type',)
