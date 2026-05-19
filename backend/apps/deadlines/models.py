from django.db import models
from apps.institutions.models import Institution


class Deadline(models.Model):
    TYPE_CHOICES = [
        ('application', 'Application Deadline'),
        ('bursary', 'Bursary Deadline'),
        ('nsfas', 'NSFAS Deadline'),
        ('late_application', 'Late Application'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=300)
    deadline_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    institution = models.ForeignKey(
        Institution, on_delete=models.CASCADE, related_name='deadlines', null=True, blank=True
    )
    deadline_date = models.DateField()
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'deadlines'
        ordering = ['deadline_date']

    def __str__(self):
        return f'{self.title} - {self.deadline_date}'
