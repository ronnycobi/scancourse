from django.db import models
from django.conf import settings


class ImportJob(models.Model):
    """One scrape/upload — tracks the source, raw extracted data, and status."""

    SOURCE_CHOICES = [
        ('url', 'URL'),
        ('pdf', 'PDF Upload'),
        ('text', 'Pasted Text'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('parsing', 'Parsing'),
        ('ready', 'Ready for review'),
        ('saved', 'Saved to database'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='import_jobs',
    )
    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    source_url = models.URLField(blank=True)
    source_filename = models.CharField(max_length=300, blank=True)
    source_pdf = models.FileField(upload_to='import_jobs/pdfs/%Y/%m/', null=True, blank=True)
    institution_short_name = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    parsed_courses = models.JSONField(default=list, blank=True)
    saved_course_ids = models.JSONField(default=list, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_import_jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f'Import {self.id} [{self.source_type}] - {self.status}'

    @property
    def course_count(self) -> int:
        return len(self.parsed_courses)

    @property
    def saved_count(self) -> int:
        return len(self.saved_course_ids)
