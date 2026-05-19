from django.db import models
from django.conf import settings
from apps.institutions.models import Institution
from apps.courses.models import Course


class Application(models.Model):
    """An application a student is making to a specific course at a specific institution."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('conditional_offer', 'Conditional Offer'),
        ('firm_offer', 'Firm Offer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
        ('waitlisted', 'Waitlisted'),
    ]

    STATUS_PROGRESS = {
        'draft': 5, 'in_progress': 25, 'submitted': 50, 'under_review': 65,
        'conditional_offer': 80, 'firm_offer': 90, 'accepted': 100,
        'rejected': 100, 'withdrawn': 100, 'waitlisted': 75,
    }

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='applications')
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default='draft')
    application_reference = models.CharField(max_length=100, blank=True, help_text='Reference number from institution')
    application_url = models.URLField(blank=True)
    deadline = models.DateField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_priority = models.BooleanField(default=False, help_text='Star this as a top-choice application')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'applications'
        ordering = ['-is_priority', 'deadline', '-created_at']
        unique_together = [('user', 'institution', 'course')]

    def __str__(self):
        target = f'{self.course.name} at ' if self.course else ''
        return f'{self.user.email} → {target}{self.institution.name} [{self.status}]'

    @property
    def progress_percent(self) -> int:
        return self.STATUS_PROGRESS.get(self.status, 0)

    @property
    def days_until_deadline(self) -> int | None:
        if not self.deadline:
            return None
        from django.utils import timezone
        return (self.deadline - timezone.now().date()).days


class ApplicationDocument(models.Model):
    """A document required for an application — links to documents.Document if uploaded."""

    DOCUMENT_TYPES = [
        ('id_copy', 'ID Document'),
        ('matric_certificate', 'Matric Certificate'),
        ('nsc_results', 'NSC Results'),
        ('proof_of_residence', 'Proof of Residence'),
        ('parent_income', 'Parent Income / Affidavit'),
        ('motivation_letter', 'Motivation Letter'),
        ('cv', 'CV'),
        ('reference_letter', 'Reference Letter'),
        ('proof_of_payment', 'Proof of Payment'),
        ('other', 'Other'),
    ]

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='required_documents')
    document_type = models.CharField(max_length=32, choices=DOCUMENT_TYPES)
    is_required = models.BooleanField(default=True)
    is_uploaded = models.BooleanField(default=False)
    document = models.ForeignKey(
        'documents.Document', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='application_uses',
    )
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'application_documents'
        unique_together = [('application', 'document_type')]

    def save(self, *args, **kwargs):
        self.is_uploaded = self.document_id is not None
        super().save(*args, **kwargs)


class ApplicationEvent(models.Model):
    """Timeline of events for an application."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    event_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'application_events'
        ordering = ['-event_date']
