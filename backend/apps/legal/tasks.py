import logging
from celery import shared_task
from django.utils import timezone
from .models import AccountDeletionRequest

logger = logging.getLogger(__name__)


@shared_task
def execute_pending_deletions():
    """Run via Celery Beat — deletes accounts whose grace period has expired."""
    due = AccountDeletionRequest.objects.filter(
        status='pending',
        scheduled_for__lte=timezone.now(),
    ).select_related('user')

    for req in due:
        try:
            user = req.user
            email = user.email
            user.delete()
            req.status = 'completed'
            req.completed_at = timezone.now()
            req.save()
            logger.info(f'Executed account deletion for {email}')
        except Exception as e:
            logger.exception(f'Failed to delete account {req.user_id}: {e}')

    return {'deleted': due.count()}
