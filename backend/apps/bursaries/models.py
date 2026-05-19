from django.db import models

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
    ('any', 'Any Field'),
]

PROVINCE_CHOICES = [
    ('GP', 'Gauteng'), ('WC', 'Western Cape'), ('KZN', 'KwaZulu-Natal'),
    ('EC', 'Eastern Cape'), ('MP', 'Mpumalanga'), ('LP', 'Limpopo'),
    ('NW', 'North West'), ('NC', 'Northern Cape'), ('FS', 'Free State'),
    ('ALL', 'All Provinces'),
]


class Bursary(models.Model):
    FUNDING_TYPE_CHOICES = [
        ('full', 'Full Bursary'),
        ('partial', 'Partial Bursary'),
        ('loan', 'Study Loan'),
        ('nsfas', 'NSFAS'),
        ('scholarship', 'Scholarship'),
    ]

    name = models.CharField(max_length=300)
    provider = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    field = models.CharField(max_length=30, choices=FIELD_CHOICES, default='any')
    funding_type = models.CharField(max_length=20, choices=FUNDING_TYPE_CHOICES)
    coverage = models.JSONField(default=list, blank=True, help_text='What is covered (tuition, accommodation, etc.)')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    province = models.CharField(max_length=3, choices=PROVINCE_CHOICES, default='ALL')
    eligibility = models.TextField(blank=True)
    min_grade_average = models.PositiveSmallIntegerField(null=True, blank=True)
    max_household_income = models.PositiveIntegerField(null=True, blank=True)
    application_url = models.URLField()
    application_deadline = models.DateField(null=True, blank=True)
    logo = models.ImageField(upload_to='bursaries/logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True, help_text='Remote CDN URL for the logo.')
    is_active = models.BooleanField(default=True)

    # Sponsored placement (computed by sponsorship app)
    is_sponsored = models.BooleanField(default=False, help_text='Has an active sponsorship')
    sponsor_priority = models.PositiveSmallIntegerField(default=0, help_text='Higher = more prominent placement')
    sponsor_name = models.CharField(max_length=200, blank=True)
    featured_until = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bursaries'
        ordering = ['application_deadline', 'name']
        verbose_name_plural = 'Bursaries'

    def __str__(self):
        return self.name
