from django.contrib import admin
from .models import RoommateProfile, RoommateMatch, RoommateMessage


@admin.register(RoommateProfile)
class RoommateProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'target_city', 'budget_max', 'is_active', 'created_at')
    list_filter = ('is_active', 'institution__province')
    search_fields = ('user__email', 'target_city')


@admin.register(RoommateMatch)
class RoommateMatchAdmin(admin.ModelAdmin):
    list_display = ('from_profile', 'to_profile', 'status', 'score', 'created_at')
    list_filter = ('status',)


@admin.register(RoommateMessage)
class RoommateMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'is_read', 'created_at')
    list_filter = ('is_read',)
