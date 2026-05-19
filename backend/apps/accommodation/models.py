from django.db import models
from apps.institutions.models import Institution


class Accommodation(models.Model):
    ROOM_TYPE_CHOICES = [
        ('single', 'Single Room'),
        ('sharing', 'Sharing Room'),
        ('bachelor', 'Bachelor Flat'),
        ('one_bed', '1 Bedroom'),
        ('two_bed', '2 Bedroom'),
    ]

    name = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    address = models.TextField()
    province = models.CharField(max_length=3)
    city = models.CharField(max_length=100)
    nearby_institution = models.ForeignKey(
        Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='nearby_accommodation'
    )
    distance_km = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    price_per_month = models.DecimalField(max_digits=8, decimal_places=2)
    nsfas_accredited = models.BooleanField(default=False)
    features = models.JSONField(default=list, blank=True)
    contact_name = models.CharField(max_length=100, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'accommodation'
        ordering = ['price_per_month']

    def __str__(self):
        return f'{self.name} - {self.city}'


class AccommodationImage(models.Model):
    accommodation = models.ForeignKey(Accommodation, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='accommodation/images/')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'accommodation_images'
        ordering = ['order']
