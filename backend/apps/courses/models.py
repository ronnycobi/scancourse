from django.db import models
from apps.institutions.models import Institution


FIELD_CHOICES = [
    ('engineering', 'Engineering & Technology'),
    ('health', 'Health Sciences'),
    ('business', 'Business & Commerce'),
    ('law', 'Law'),
    ('humanities', 'Humanities & Social Sciences'),
    ('science', 'Natural Sciences'),
    ('education', 'Education'),
    ('arts', 'Arts & Design'),
    ('agriculture', 'Agriculture'),
    ('ict', 'Information & Communication Technology'),
    ('built_environment', 'Built Environment'),
    ('other', 'Other'),
]


class Course(models.Model):
    LEVEL_CHOICES = [
        ('certificate', 'Certificate'),
        ('diploma', 'Diploma'),
        ('advanced_diploma', 'Advanced Diploma'),
        ('degree', 'Bachelor\'s Degree'),
        ('honours', 'Honours'),
        ('masters', 'Masters'),
        ('phd', 'PhD'),
        ('n1_n6', 'N1-N6 (TVET)'),
        ('nc_v', 'NC(V) (TVET)'),
    ]

    name = models.CharField(max_length=300)
    field = models.CharField(max_length=30, choices=FIELD_CHOICES)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True)
    duration_years = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    fees_per_year = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    career_opportunities = models.TextField(blank=True)
    modules = models.JSONField(default=list, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return self.name


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='offerings')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='course_offerings')
    min_aps = models.PositiveSmallIntegerField()
    campus = models.CharField(max_length=100, blank=True, help_text='Campus or campus code, e.g. "APK", "Soweto"')
    programme_code = models.CharField(max_length=20, blank=True, help_text='Institution-specific code (e.g. UJ\'s B34A5Q)')
    application_deadline = models.DateField(null=True, blank=True)
    application_url = models.URLField(blank=True)
    special_requirements = models.JSONField(default=list, blank=True)
    subject_requirements = models.JSONField(default=list, blank=True)
    available_spaces = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'course_offerings'
        unique_together = ('course', 'institution', 'campus')

    def __str__(self):
        return f'{self.course.name} @ {self.institution.name}'


class SubjectRequirement(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='subject_reqs')
    subject_name = models.CharField(max_length=100)
    min_level = models.PositiveSmallIntegerField(default=4)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        db_table = 'subject_requirements'


class CourseInteraction(models.Model):
    """Tracks user interest signals on a course for collaborative filtering."""
    KIND_CHOICES = [
        ('view',  'Viewed'),     # weight 1
        ('save',  'Saved'),      # weight 3
        ('apply', 'Applied'),    # weight 5
    ]
    user = models.ForeignKey(
        'users.User', on_delete=models.CASCADE, related_name='course_interactions',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='interactions')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='view')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_interactions'
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['course', 'kind']),
        ]
