from django.db import models
from django.utils.text import slugify


class Institution(models.Model):
    TYPE_CHOICES = [
        ('university', 'University'),
        ('university_of_technology', 'University of Technology'),
        ('tvet', 'TVET College'),
        ('private', 'Private College'),
    ]

    PROVINCE_CHOICES = [
        ('GP', 'Gauteng'), ('WC', 'Western Cape'), ('KZN', 'KwaZulu-Natal'),
        ('EC', 'Eastern Cape'), ('MP', 'Mpumalanga'), ('LP', 'Limpopo'),
        ('NW', 'North West'), ('NC', 'Northern Cape'), ('FS', 'Free State'),
    ]

    name = models.CharField(max_length=300)
    short_name = models.CharField(max_length=20, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    institution_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    province = models.CharField(max_length=3, choices=PROVINCE_CHOICES)
    city = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='institutions/logos/', null=True, blank=True)
    logo_url = models.URLField(blank=True, help_text='Remote CDN URL for the logo (used when no upload).')
    cover_image = models.ImageField(upload_to='institutions/covers/', null=True, blank=True)
    cover_image_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    application_open = models.BooleanField(default=False)
    application_deadline = models.DateField(null=True, blank=True)
    application_url = models.URLField(blank=True)
    nsfas_accredited = models.BooleanField(default=False)
    min_aps = models.PositiveSmallIntegerField(default=0)
    uses_extended_aps = models.BooleanField(
        default=False,
        help_text=(
            "True when the institution calculates APS using more than 6 subjects "
            "(e.g. includes Life Orientation) or uses a non-standard points scale. "
            "UP includes LO → max 49. Wits uses its own Faculty Points Score."
        ),
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'institutions'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
