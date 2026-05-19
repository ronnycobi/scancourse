"""
Django signals — auto-index models on save, remove on delete.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender='courses.Course')
def reindex_course(sender, instance, **kwargs):
    from .tasks import reindex_course_async
    reindex_course_async.delay(instance.id)


@receiver(post_save, sender='institutions.Institution')
def reindex_institution(sender, instance, **kwargs):
    from .tasks import reindex_institution_async
    reindex_institution_async.delay(instance.id)


@receiver(post_save, sender='bursaries.Bursary')
def reindex_bursary(sender, instance, **kwargs):
    from .tasks import reindex_bursary_async
    reindex_bursary_async.delay(instance.id)


@receiver(post_delete, sender='courses.Course')
def remove_course(sender, instance, **kwargs):
    from . import client
    try:
        client.remove_from_index('courses', instance.id)
    except Exception as e:
        logger.warning(f'Failed to remove course {instance.id}: {e}')


@receiver(post_delete, sender='institutions.Institution')
def remove_institution(sender, instance, **kwargs):
    from . import client
    try:
        client.remove_from_index('institutions', instance.id)
    except Exception as e:
        logger.warning(f'Failed to remove institution {instance.id}: {e}')


@receiver(post_delete, sender='bursaries.Bursary')
def remove_bursary(sender, instance, **kwargs):
    from . import client
    try:
        client.remove_from_index('bursaries', instance.id)
    except Exception as e:
        logger.warning(f'Failed to remove bursary {instance.id}: {e}')
