"""
Auto-sync bursary promotion fields whenever a Sponsorship is saved or deleted.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Sponsorship
from .promotion import sync_bursary_promotion


@receiver(post_save, sender=Sponsorship)
def on_sponsorship_save(sender, instance, **kwargs):
    if instance.bursary_id:
        sync_bursary_promotion(instance.bursary)


@receiver(post_delete, sender=Sponsorship)
def on_sponsorship_delete(sender, instance, **kwargs):
    if instance.bursary_id:
        sync_bursary_promotion(instance.bursary)
