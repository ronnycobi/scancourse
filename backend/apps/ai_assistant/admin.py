from django.contrib import admin
from .models import ChatSession, ChatMessage, MotivationLetter


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'created_at')
    search_fields = ('user__email', 'title')
    inlines = [ChatMessageInline]


@admin.register(MotivationLetter)
class MotivationLetterAdmin(admin.ModelAdmin):
    list_display = ('user', 'course_name', 'institution_name', 'tone', 'language', 'revision_count', 'is_finalised', 'updated_at')
    list_filter = ('tone', 'language', 'is_finalised')
    search_fields = ('user__email', 'course_name', 'institution_name')
    readonly_fields = ('content', 'revision_count', 'created_at', 'updated_at')
