import logging
from celery import shared_task
from . import client

logger = logging.getLogger(__name__)


@shared_task
def reindex_course_async(course_id: int):
    try:
        client.index_course(course_id)
    except Exception as e:
        logger.exception(f'Course reindex failed {course_id}: {e}')


@shared_task
def reindex_institution_async(inst_id: int):
    try:
        client.index_institution(inst_id)
    except Exception as e:
        logger.exception(f'Institution reindex failed {inst_id}: {e}')


@shared_task
def reindex_bursary_async(bursary_id: int):
    try:
        client.index_bursary(bursary_id)
    except Exception as e:
        logger.exception(f'Bursary reindex failed {bursary_id}: {e}')


@shared_task
def reindex_all():
    """Full re-sync — useful after a data import or schema change."""
    from apps.courses.models import Course
    from apps.institutions.models import Institution
    from apps.bursaries.models import Bursary

    client.ensure_indexes()
    for c in Course.objects.filter(is_active=True):
        client.index_course(c)
    for i in Institution.objects.filter(is_active=True):
        client.index_institution(i)
    for b in Bursary.objects.filter(is_active=True):
        client.index_bursary(b)
    logger.info('Full reindex complete.')
