from django.db import models
from django.conf import settings
from apps.institutions.models import Institution


class RoommateProfile(models.Model):
    """A student's lifestyle profile for matching with potential roommates."""

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-binary'),
        ('prefer_not', 'Prefer not to say'),
    ]

    SLEEP_CHOICES = [('early', 'Early bird (before 10pm)'), ('average', 'Average (10pm–12am)'), ('night_owl', 'Night owl (after 12am)')]
    CLEANLINESS_CHOICES = [('very_clean', 'Very clean'), ('clean', 'Clean'), ('average', 'Average'), ('relaxed', 'Relaxed')]
    SOCIAL_CHOICES = [('introvert', 'Introvert'), ('balanced', 'Balanced'), ('extrovert', 'Extrovert')]
    STUDY_CHOICES = [('quiet', 'Need quiet space'), ('flexible', 'Flexible'), ('library', 'Study elsewhere')]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='roommate_profile')
    is_active = models.BooleanField(default=True, help_text='Show me to potential roommates')

    # Identity
    bio = models.TextField(blank=True, max_length=500)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=12, choices=GENDER_CHOICES, blank=True)

    # Where & when
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    target_city = models.CharField(max_length=100, blank=True)
    move_in_month = models.DateField(null=True, blank=True, help_text='Earliest move-in date')

    # Budget
    budget_min = models.PositiveIntegerField(null=True, blank=True)
    budget_max = models.PositiveIntegerField(null=True, blank=True)

    # Lifestyle
    sleep_schedule = models.CharField(max_length=12, choices=SLEEP_CHOICES, blank=True)
    cleanliness = models.CharField(max_length=12, choices=CLEANLINESS_CHOICES, blank=True)
    social_level = models.CharField(max_length=12, choices=SOCIAL_CHOICES, blank=True)
    study_habits = models.CharField(max_length=12, choices=STUDY_CHOICES, blank=True)

    # Preferences (multi-select stored as flags)
    smokes = models.BooleanField(default=False)
    drinks = models.BooleanField(default=False)
    has_pets = models.BooleanField(default=False)
    is_vegetarian = models.BooleanField(default=False)

    # Roommate preferences
    prefers_same_gender = models.BooleanField(default=False)
    prefers_non_smoker = models.BooleanField(default=True)
    prefers_no_pets = models.BooleanField(default=False)
    age_range_min = models.PositiveSmallIntegerField(default=17)
    age_range_max = models.PositiveSmallIntegerField(default=30)

    # Languages
    languages = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'roommate_profiles'

    def __str__(self):
        return f'{self.user.email} (active={self.is_active})'


class RoommateMatch(models.Model):
    """Mutual interest tracker — when both users 'like' each other, it's a match."""

    STATUS_CHOICES = [
        ('liked', 'Liked'),       # one-way like
        ('matched', 'Matched'),    # mutual like
        ('passed', 'Passed'),
        ('blocked', 'Blocked'),
    ]

    from_profile = models.ForeignKey(RoommateProfile, on_delete=models.CASCADE, related_name='likes_sent')
    to_profile = models.ForeignKey(RoommateProfile, on_delete=models.CASCADE, related_name='likes_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='liked')
    score = models.FloatField(default=0.0, help_text='Compatibility score 0-1')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roommate_matches'
        unique_together = [('from_profile', 'to_profile')]


class RoommateMessage(models.Model):
    """In-app DM between matched roommates."""

    sender = models.ForeignKey(RoommateProfile, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(RoommateProfile, on_delete=models.CASCADE, related_name='received_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roommate_messages'
        ordering = ['-created_at']
