from django.db import models
from django.conf import settings


class ConsentRecord(models.Model):
    """POPIA-compliant record of user consents."""

    CONSENT_TYPES = [
        ('terms_of_service', 'Terms of Service'),
        ('privacy_policy', 'Privacy Policy'),
        ('marketing_email', 'Marketing emails'),
        ('marketing_sms', 'Marketing SMS / WhatsApp'),
        ('data_sharing_partners', 'Data sharing with bursary partners'),
        ('cookies_analytics', 'Analytics cookies'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=40, choices=CONSENT_TYPES)
    granted = models.BooleanField()
    version = models.CharField(max_length=20, blank=True, help_text='Version of the policy/terms accepted')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'consent_records'
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.email} - {self.consent_type} - {"granted" if self.granted else "revoked"}'


class DataExportRequest(models.Model):
    """User-requested data export (POPIA right of access)."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('expired', 'Expired'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='data_exports')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    download_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        db_table = 'data_export_requests'
        ordering = ['-requested_at']


class AccountDeletionRequest(models.Model):
    """User-initiated account deletion (POPIA right to erasure)."""

    STATUS_CHOICES = [
        ('pending', 'Pending — 30-day grace period'),
        ('cancelled', 'Cancelled by user'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deletion_requests')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(help_text='When the deletion will actually run (after grace period)')
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'account_deletion_requests'
        ordering = ['-requested_at']
