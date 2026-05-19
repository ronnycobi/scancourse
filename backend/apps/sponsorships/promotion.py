"""
Sync the `is_sponsored`, `sponsor_priority`, `sponsor_name`, `featured_until`
fields on Bursary based on active sponsorships.
"""
from django.utils import timezone
from .models import Sponsorship


def sync_bursary_promotion(bursary):
    """Update a single bursary's sponsorship fields based on its active sponsorships."""
    now = timezone.now()
    active = (
        Sponsorship.objects
        .filter(bursary=bursary, status='active', starts_at__lte=now, ends_at__gte=now)
        .select_related('plan', 'sponsor')
        .order_by('-plan__priority_boost')
        .first()
    )

    if active:
        bursary.is_sponsored = True
        bursary.sponsor_priority = active.plan.priority_boost
        bursary.sponsor_name = active.sponsor.name
        bursary.featured_until = active.ends_at
    else:
        bursary.is_sponsored = False
        bursary.sponsor_priority = 0
        bursary.sponsor_name = ''
        bursary.featured_until = None

    bursary.save(update_fields=['is_sponsored', 'sponsor_priority', 'sponsor_name', 'featured_until'])


def sync_all_bursary_promotion():
    """Run for every bursary — useful as a periodic Celery task."""
    from apps.bursaries.models import Bursary
    for bursary in Bursary.objects.all():
        sync_bursary_promotion(bursary)
