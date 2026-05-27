from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    GRADE_CHOICES = [
        ('grade_10', 'Grade 10'),
        ('grade_11', 'Grade 11'),
        ('grade_12', 'Grade 12'),
        ('gap_year', 'Gap Year'),
        ('other', 'Other'),
    ]

    PROVINCE_CHOICES = [
        ('GP', 'Gauteng'),
        ('WC', 'Western Cape'),
        ('KZN', 'KwaZulu-Natal'),
        ('EC', 'Eastern Cape'),
        ('MP', 'Mpumalanga'),
        ('LP', 'Limpopo'),
        ('NW', 'North West'),
        ('NC', 'Northern Cape'),
        ('FS', 'Free State'),
    ]

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    grade = models.CharField(max_length=20, choices=GRADE_CHOICES, blank=True)
    province = models.CharField(max_length=3, choices=PROVINCE_CHOICES, blank=True)
    # Singular fields kept for backwards compat with matcher/recommender
    # code that still reads them directly. New code should read the plural
    # JSON lists below — sync helpers ensure both stay aligned.
    preferred_field = models.CharField(max_length=100, blank=True)
    preferred_study_province = models.CharField(max_length=3, choices=PROVINCE_CHOICES, blank=True)
    dream_career = models.CharField(max_length=200, blank=True)
    # Plural fields — users can pick multiple. Stored as JSON list of strings.
    preferred_fields = models.JSONField(default=list, blank=True)
    preferred_study_provinces = models.JSONField(default=list, blank=True)
    dream_careers = models.JSONField(default=list, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    fcm_token = models.TextField(blank=True)
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('zu', 'isiZulu'),
        ('xh', 'isiXhosa'),
        ('af', 'Afrikaans'),
        ('st', 'Sesotho'),
    ]
    preferred_language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email


class SavedItem(models.Model):
    ITEM_TYPES = [
        ('course', 'Course'),
        ('bursary', 'Bursary'),
        ('accommodation', 'Accommodation'),
        ('institution', 'Institution'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_items')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_id = models.PositiveIntegerField()
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'saved_items'
        unique_together = ('user', 'item_type', 'item_id')

    def __str__(self):
        return f'{self.user.email} - {self.item_type}:{self.item_id}'
