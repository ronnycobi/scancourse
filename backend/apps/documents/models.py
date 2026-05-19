import os
import uuid
from django.db import models
from django.conf import settings


def encrypted_upload_path(instance, filename):
    """Per-user, opaque-named storage path."""
    ext = filename.split('.')[-1].lower()
    return f'vault/{instance.user_id}/{uuid.uuid4().hex}.{ext}.enc'


class Document(models.Model):
    """A document a student has uploaded to their vault — encrypted at rest."""

    DOCUMENT_TYPES = [
        ('id_copy', 'ID Document'),
        ('passport', 'Passport'),
        ('matric_certificate', 'Matric Certificate'),
        ('nsc_results', 'NSC Results / Report Card'),
        ('proof_of_residence', 'Proof of Residence'),
        ('parent_income', 'Parent Income / Affidavit'),
        ('motivation_letter', 'Motivation Letter'),
        ('cv', 'CV / Resume'),
        ('reference_letter', 'Reference Letter'),
        ('proof_of_payment', 'Proof of Payment'),
        ('birth_certificate', 'Birth Certificate'),
        ('photo', 'Passport Photo'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=32, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to=encrypted_upload_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False, help_text='Manually verified for authenticity')
    is_encrypted = models.BooleanField(default=True)
    expires_at = models.DateField(null=True, blank=True, help_text='When this document needs to be re-uploaded (e.g. proof of residence)')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'documents'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.user.email})'

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        from django.utils import timezone
        return self.expires_at < timezone.now().date()

    def delete_file(self):
        """Securely remove the underlying file from disk/S3."""
        if self.file and self.file.storage.exists(self.file.name):
            try:
                self.file.delete(save=False)
            except Exception:
                pass


class DocumentAccessLog(models.Model):
    """Audit trail of every document access (POPIA compliance)."""

    ACTION_CHOICES = [
        ('view', 'View'),
        ('download', 'Download'),
        ('attach', 'Attach to application'),
        ('delete', 'Delete'),
    ]

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_access_logs'
        ordering = ['-timestamp']
