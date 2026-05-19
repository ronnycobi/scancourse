"""
Meilisearch client wrapper. Indexes: courses, institutions, bursaries.
"""
import logging
from django.conf import settings
import meilisearch

logger = logging.getLogger(__name__)


def get_client() -> meilisearch.Client:
    return meilisearch.Client(settings.MEILISEARCH_URL, settings.MEILISEARCH_MASTER_KEY)


INDEXES = ['courses', 'institutions', 'bursaries']

INDEX_SETTINGS = {
    'courses': {
        'searchableAttributes': ['name', 'description', 'career_opportunities', 'field'],
        'filterableAttributes': ['field', 'level', 'min_aps', 'institution_provinces'],
        'sortableAttributes': ['min_aps', 'fees_per_year', 'name'],
        'rankingRules': ['words', 'typo', 'proximity', 'attribute', 'sort', 'exactness'],
    },
    'institutions': {
        'searchableAttributes': ['name', 'short_name', 'city', 'description'],
        'filterableAttributes': ['institution_type', 'province', 'nsfas_accredited', 'application_open'],
        'sortableAttributes': ['name', 'min_aps', 'application_deadline'],
    },
    'bursaries': {
        'searchableAttributes': ['name', 'provider', 'description', 'eligibility', 'field'],
        'filterableAttributes': ['field', 'province', 'funding_type'],
        'sortableAttributes': ['application_deadline', 'amount', 'name'],
    },
}


def ensure_indexes():
    """Idempotent — create indexes and apply settings if not present."""
    client = get_client()
    for index_name in INDEXES:
        try:
            client.create_index(index_name, {'primaryKey': 'id'})
        except meilisearch.errors.MeilisearchApiError:
            pass  # already exists

        idx = client.index(index_name)
        idx.update_settings(INDEX_SETTINGS[index_name])

    logger.info('Meilisearch indexes ensured.')


def index_course(course):
    from apps.courses.models import Course
    if isinstance(course, int):
        course = Course.objects.get(id=course)

    institution_provinces = list(course.offerings.values_list('institution__province', flat=True).distinct())
    min_aps = course.offerings.aggregate_or_none = course.offerings.order_by('min_aps').values_list('min_aps', flat=True).first() or 0

    doc = {
        'id': course.id,
        'name': course.name,
        'field': course.field,
        'level': course.level,
        'description': course.description or '',
        'career_opportunities': course.career_opportunities or '',
        'duration_years': float(course.duration_years) if course.duration_years else None,
        'fees_per_year': float(course.fees_per_year) if course.fees_per_year else None,
        'min_aps': min_aps,
        'institution_provinces': institution_provinces,
    }
    get_client().index('courses').add_documents([doc])


def index_institution(inst):
    from apps.institutions.models import Institution
    if isinstance(inst, int):
        inst = Institution.objects.get(id=inst)

    doc = {
        'id': inst.id,
        'name': inst.name,
        'short_name': inst.short_name,
        'institution_type': inst.institution_type,
        'province': inst.province,
        'city': inst.city,
        'description': inst.description or '',
        'min_aps': inst.min_aps,
        'application_open': inst.application_open,
        'application_deadline': inst.application_deadline.isoformat() if inst.application_deadline else None,
        'nsfas_accredited': inst.nsfas_accredited,
    }
    get_client().index('institutions').add_documents([doc])


def index_bursary(bursary):
    from apps.bursaries.models import Bursary
    if isinstance(bursary, int):
        bursary = Bursary.objects.get(id=bursary)

    doc = {
        'id': bursary.id,
        'name': bursary.name,
        'provider': bursary.provider,
        'description': bursary.description or '',
        'eligibility': bursary.eligibility or '',
        'field': bursary.field,
        'province': bursary.province,
        'funding_type': bursary.funding_type,
        'amount': float(bursary.amount) if bursary.amount else None,
        'application_deadline': bursary.application_deadline.isoformat() if bursary.application_deadline else None,
    }
    get_client().index('bursaries').add_documents([doc])


def remove_from_index(index_name: str, doc_id: int):
    try:
        get_client().index(index_name).delete_document(doc_id)
    except Exception as e:
        logger.warning(f'Failed to remove {index_name}#{doc_id}: {e}')


def search(index_name: str, query: str, filters: str | None = None, limit: int = 20) -> dict:
    """Generic search across one index."""
    if index_name not in INDEXES:
        raise ValueError(f'Unknown index: {index_name}')
    params = {'limit': limit, 'attributesToHighlight': ['name', 'description']}
    if filters:
        params['filter'] = filters
    return get_client().index(index_name).search(query, params)


def multi_search(query: str, limit: int = 10) -> dict:
    """Search all indexes at once — returns combined results."""
    client = get_client()
    queries = [
        {'indexUid': idx, 'q': query, 'limit': limit, 'attributesToHighlight': ['name']}
        for idx in INDEXES
    ]
    return client.multi_search(queries)
