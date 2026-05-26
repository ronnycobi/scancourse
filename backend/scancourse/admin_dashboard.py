"""
Stats injected into the Jazzmin admin index page.

We wrap Django's default `AdminSite.index` so the existing app/model list
keeps rendering, and we add a `stats` dict to the context that the
templates/admin/index.html override reads.
"""
from datetime import timedelta
import json
import logging

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from django.utils import timezone

logger = logging.getLogger(__name__)
_original_index = admin.site.index


def _compute_stats():
    """Returns the dict consumed by templates/admin/index.html."""
    User = get_user_model()
    today = timezone.now().date()
    week_ago = timezone.now() - timedelta(days=7)

    stats = {
        'users_total': 0,
        'users_week': 0,
        'reports_total': 0,
        'aps_avg': '—',
        'courses_total': 0,
        'institutions_total': 0,
        'bursaries_total': 0,
        'applications_total': 0,
        'top_fields': [],
        'recent_users': [],
        'chart_labels_json': '[]',
        'chart_data_json': '[]',
        'week_ago_iso': week_ago.date().isoformat(),
    }

    try:
        stats['users_total'] = User.objects.count()
        stats['users_week'] = User.objects.filter(date_joined__gte=week_ago).count()
        stats['recent_users'] = list(
            User.objects.order_by('-date_joined')[:8]
        )
    except Exception as e:
        logger.warning('Dashboard: users count failed: %s', e)

    # Reports + average APS
    try:
        from apps.ocr.models import Report, APSResult
        stats['reports_total'] = Report.objects.count()
        agg = APSResult.objects.aggregate(avg=Avg('total_aps'))
        if agg['avg']:
            stats['aps_avg'] = round(agg['avg'], 1)
    except Exception as e:
        logger.warning('Dashboard: report stats failed: %s', e)

    # Courses + top fields
    try:
        from apps.courses.models import Course
        qs = Course.objects.filter(is_active=True)
        stats['courses_total'] = qs.count()
        stats['top_fields'] = list(
            qs.values('field').annotate(count=Count('id')).order_by('-count')[:8]
        )
    except Exception as e:
        logger.warning('Dashboard: course stats failed: %s', e)

    try:
        from apps.institutions.models import Institution
        stats['institutions_total'] = Institution.objects.count()
    except Exception as e:
        logger.warning('Dashboard: institutions failed: %s', e)

    try:
        from apps.bursaries.models import Bursary
        stats['bursaries_total'] = Bursary.objects.count()
    except Exception as e:
        logger.warning('Dashboard: bursaries failed: %s', e)

    try:
        from apps.applications.models import Application
        stats['applications_total'] = Application.objects.count()
    except Exception as e:
        logger.warning('Dashboard: applications failed: %s', e)

    # Build last-14-days signup chart data
    try:
        days = 14
        labels = []
        data = []
        for i in range(days - 1, -1, -1):
            d = today - timedelta(days=i)
            labels.append(d.strftime('%-d %b'))
            cnt = User.objects.filter(
                date_joined__date=d,
            ).count()
            data.append(cnt)
        stats['chart_labels_json'] = json.dumps(labels)
        stats['chart_data_json'] = json.dumps(data)
    except Exception as e:
        logger.warning('Dashboard: chart series failed: %s', e)

    return stats


def patched_index(request, extra_context=None):
    extra_context = dict(extra_context or {})
    try:
        extra_context['stats'] = _compute_stats()
    except Exception as e:
        # Never let the dashboard break the admin — empty stats are fine.
        logger.warning('Dashboard: compute_stats crashed: %s', e)
        extra_context['stats'] = {}
    return _original_index(request, extra_context=extra_context)


def install():
    """Monkey-patch admin.site.index so it injects our stats."""
    admin.site.index = patched_index
