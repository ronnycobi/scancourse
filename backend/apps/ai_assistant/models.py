from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sessions'
        ordering = ['-updated_at']

    def __str__(self):
        return f'Session {self.id} - {self.user.email}'


class ChatMessage(models.Model):
    ROLE_CHOICES = [('user', 'User'), ('assistant', 'Assistant')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.role}: {self.content[:50]}'


class MotivationLetter(models.Model):
    """Saved drafts of AI-generated motivation letters."""

    TONE_CHOICES = [
        ('professional', 'Professional'),
        ('warm', 'Warm & Personal'),
        ('confident', 'Confident'),
        ('humble', 'Humble & Earnest'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='motivation_letters')
    title = models.CharField(max_length=200, blank=True)
    course_name = models.CharField(max_length=200)
    institution_name = models.CharField(max_length=200)
    student_background = models.TextField()
    key_achievements = models.TextField(blank=True)
    why_this_course = models.TextField(blank=True)
    why_this_institution = models.TextField(blank=True)
    additional_info = models.TextField(blank=True)
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default='professional')
    language = models.CharField(max_length=5, default='en')

    content = models.TextField(blank=True, help_text='The generated letter')
    revision_count = models.PositiveSmallIntegerField(default=0)
    is_finalised = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'motivation_letters'
        ordering = ['-updated_at']

    def __str__(self):
        return f'{self.user.email} → {self.course_name} @ {self.institution_name}'
