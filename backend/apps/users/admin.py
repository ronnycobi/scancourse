from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SavedItem


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'grade', 'province', 'onboarding_completed', 'is_active', 'created_at')
    list_filter = ('grade', 'province', 'onboarding_completed', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-created_at',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Student Info', {'fields': ('grade', 'province', 'preferred_field', 'preferred_study_province', 'dream_career')}),
        ('App Data', {'fields': ('profile_picture', 'phone_number', 'onboarding_completed', 'fcm_token')}),
    )


@admin.register(SavedItem)
class SavedItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_type', 'item_id', 'saved_at')
    list_filter = ('item_type',)
