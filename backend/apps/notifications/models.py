from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('deadline', 'Application Deadline'),
        ('bursary', 'Bursary Deadline'),
        ('new_course', 'New Course Available'),
        ('accommodation', 'Accommodation Alert'),
        ('aps', 'APS Update'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.user.email} - {self.title}'
