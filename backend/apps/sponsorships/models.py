from django.db import models
from django.conf import settings
from apps.bursaries.models import Bursary
from apps.institutions.models import Institution


class Sponsor(models.Model):
    """A company / institution paying for sponsored placements."""

    SPONSOR_TYPE = [
        ('bursary_provider', 'Bursary Provider'),
        ('institution', 'Institution'),
        ('partner', 'Other Partner'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200)
    sponsor_type = models.CharField(max_length=20, choices=SPONSOR_TYPE)
    contact_name = models.CharField(max_length=200)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    company_registration = models.CharField(max_length=50, blank=True, help_text='SA company reg number')
    vat_number = models.CharField(max_length=20, blank=True)
    billing_address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='sponsors/logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sponsors'
        ordering = ['name']

    def __str__(self):
        return self.name


class SponsorshipPlan(models.Model):
    """Pricing tiers — Bronze / Silver / Gold / Platinum."""

    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    ]

    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    monthly_price_zar = models.DecimalField(max_digits=10, decimal_places=2)
    annual_price_zar = models.DecimalField(max_digits=10, decimal_places=2)
    priority_boost = models.PositiveSmallIntegerField(default=10, help_text='Higher = more prominent placement')
    max_listings = models.PositiveSmallIntegerField(default=1)
    has_featured_card = models.BooleanField(default=False)
    has_homepage_banner = models.BooleanField(default=False)
    has_analytics = models.BooleanField(default=False)
    has_direct_messaging = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'sponsorship_plans'

    def __str__(self):
        return f'{self.name} (R{self.monthly_price_zar}/mo)'


class Sponsorship(models.Model):
    """An active sponsorship deal — sponsor X buys plan Y for some duration on a specific bursary or institution."""

    STATUS_CHOICES = [
        ('pending', 'Pending Payment'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('paused', 'Paused'),
    ]

    sponsor = models.ForeignKey(Sponsor, on_delete=models.CASCADE, related_name='sponsorships')
    plan = models.ForeignKey(SponsorshipPlan, on_delete=models.PROTECT)
    bursary = models.ForeignKey(Bursary, on_delete=models.CASCADE, null=True, blank=True, related_name='sponsorships')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, null=True, blank=True, related_name='sponsorships')

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    amount_paid_zar = models.DecimalField(max_digits=10, decimal_places=2)
    invoice_number = models.CharField(max_length=50, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'sponsorships'
        ordering = ['-created_at']

    def __str__(self):
        target = self.bursary.name if self.bursary else (self.institution.name if self.institution else 'general')
        return f'{self.sponsor.name} → {target} ({self.status})'

    @property
    def is_currently_active(self) -> bool:
        from django.utils import timezone
        now = timezone.now()
        return self.status == 'active' and self.starts_at <= now <= self.ends_at


class SponsorshipImpression(models.Model):
    """Every time a sponsored item is shown — tracked for analytics."""

    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='impressions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    placement = models.CharField(max_length=50, help_text='Where on the app it was shown — e.g. "bursary_list_top"')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sponsorship_impressions'
        indexes = [
            models.Index(fields=['sponsorship', 'timestamp']),
        ]


class SponsorshipClick(models.Model):
    """Every time a user taps a sponsored item or its 'Apply Now' link."""

    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, default='view', help_text='view | apply | save')
    referrer = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sponsorship_clicks'
        indexes = [
            models.Index(fields=['sponsorship', 'timestamp']),
        ]
