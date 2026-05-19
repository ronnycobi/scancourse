"""Celery tasks for the bursaries app."""
import logging
from io import StringIO

from celery import shared_task
from django.core.management import call_command

log = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=False, max_retries=2, default_retry_delay=300)
def refresh_bursaries_task(self):
    """
    Re-apply the bursary seed scripts and scan zabursaries.co.za for
    headlines we don't already track. Schedule weekly via Celery beat.
    """
    out = StringIO()
    try:
        call_command('refresh_bursaries', stdout=out)
    except Exception as exc:
        log.exception('refresh_bursaries failed')
        raise self.retry(exc=exc)
    summary = out.getvalue()
    log.info('refresh_bursaries finished:\n%s', summary)
    return summary
