import logging
from celery import shared_task
from django.utils import timezone
from .models import Sponsorship
from .promotion import sync_all_bursary_promotion

logger = logging.getLogger(__name__)


@shared_task
def expire_old_sponsorships():
    """Run hourly via Celery Beat — flips ended sponsorships to 'expired' and re-syncs bursaries."""
    now = timezone.now()
    ended = Sponsorship.objects.filter(status='active', ends_at__lt=now)
    count = ended.update(status='expired')

    sync_all_bursary_promotion()
    logger.info(f'Expired {count} sponsorships and re-synced bursary promotion.')
    return {'expired': count}
