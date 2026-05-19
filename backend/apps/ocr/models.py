from django.db import models
from django.conf import settings


class Report(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('verified', 'Verified'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports')
    file = models.FileField(upload_to='reports/%Y/%m/')
    file_type = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    raw_text = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    grade = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=10, blank=True)
    school_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'reports'
        ordering = ['-created_at']

    def __str__(self):
        return f'Report {self.id} - {self.user.email}'


class Subject(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=100)
    normalized_name = models.CharField(max_length=100, blank=True)
    mark = models.PositiveSmallIntegerField()
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_life_orientation = models.BooleanField(default=False)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return f'{self.name}: {self.mark}%'


class APSResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aps_results')
    report = models.OneToOneField(Report, on_delete=models.CASCADE, related_name='aps_result', null=True, blank=True)
    total_aps = models.PositiveSmallIntegerField()
    subjects_data = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'aps_results'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} - APS: {self.total_aps}'
