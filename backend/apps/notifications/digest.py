"""
Weekly digest builder + sender.

Per-user content shape:
  {
    "user": <User>,
    "name": "Thandi",
    "headline": "Your week on Scancourse",
    "current_aps": 32,
    "aps_delta": 4,                  # vs previous APSResult (0 if none)
    "saved_bursaries_closing": [     # ≤ 14 days
        {"name": "...", "days": 7, "id": 12}, ...
    ],
    "saved_courses_closing": [...],
    "new_matches_count": 7,          # courses added in last 7 days the user qualifies for
    "tip": "Scan a fresh report each term…",
    "view_link": "https://scancourse.co.za",
  }

Use `build_digest(user)` to get one user's payload, and `send_digest(user)`
to email it. Or `send_weekly_digests_for_all()` for the cron.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── Build ───────────────────────────────────────────────────────────

def build_digest(user) -> dict | None:
    """Compute everything that goes in the email. Returns None if the
    user has nothing meaningful to say hello to this week."""
    from apps.users.models import SavedItem
    from apps.bursaries.models import Bursary
    from apps.courses.models import CourseOffering
    from apps.ocr.models import APSResult

    today = timezone.now().date()
    horizon = today + timedelta(days=14)

    # APS
    aps_qs = APSResult.objects.filter(user=user).order_by('-created_at')[:2]
    latest = aps_qs[0] if aps_qs else None
    prev = aps_qs[1] if len(aps_qs) > 1 else None
    current_aps = latest.total_aps if latest else 0
    aps_delta = (latest.total_aps - prev.total_aps) if (latest and prev) else 0

    # Saved bursaries closing soon
    saved_bursary_ids = list(SavedItem.objects.filter(
        user=user, item_type='bursary'
    ).values_list('item_id', flat=True))
    saved_bursaries_closing = []
    if saved_bursary_ids:
        for b in Bursary.objects.filter(
            id__in=saved_bursary_ids,
            application_deadline__gte=today,
            application_deadline__lte=horizon,
        ).order_by('application_deadline')[:5]:
            days = (b.application_deadline - today).days
            saved_bursaries_closing.append({
                'id': b.id, 'name': b.name, 'days': days,
                'provider': b.provider,
            })

    # Saved courses closing soon
    saved_course_ids = list(SavedItem.objects.filter(
        user=user, item_type='course'
    ).values_list('item_id', flat=True))
    saved_courses_closing = []
    if saved_course_ids:
        offerings = (CourseOffering.objects
                     .filter(course_id__in=saved_course_ids,
                             application_deadline__gte=today,
                             application_deadline__lte=horizon)
                     .select_related('course', 'institution')
                     .order_by('application_deadline')[:5])
        for o in offerings:
            days = (o.application_deadline - today).days
            inst = ''
            if o.institution_id:
                inst = o.institution.short_name or o.institution.name
            saved_courses_closing.append({
                'id': o.course_id, 'name': o.course.name, 'institution': inst,
                'days': days,
            })

    # New course matches in the last 7 days
    new_matches_count = 0
    if latest and hasattr(CourseOffering, 'created_at'):
        cutoff = timezone.now() - timedelta(days=7)
        try:
            new_matches_count = CourseOffering.objects.filter(
                min_aps__lte=latest.total_aps,
                created_at__gte=cutoff,
            ).count()
        except Exception:
            new_matches_count = 0

    # Rotating evergreen tip
    tips = [
        'Scan a fresh report each term — your APS updates the second we read new marks.',
        'Bookmark courses you like — they move into "My Applications" with deadline alerts.',
        'Want a better motivation letter? Our AI helper writes the first draft.',
        'Fill in your dream careers — Scan AI uses them to find courses you\'ll love.',
        'Compare yourself to peers with the same APS — it helps you plan smarter.',
    ]
    tip = tips[(today.toordinal() + (user.id or 0)) % len(tips)]

    # ── Don't email empty digests ───────────────────────────────────
    has_content = (
        current_aps > 0 or
        bool(saved_bursaries_closing) or
        bool(saved_courses_closing) or
        new_matches_count > 0
    )
    if not has_content:
        return None

    return {
        'user': user,
        'name': (user.first_name or user.email.split('@')[0] or 'there'),
        'headline': 'Your week on Scancourse',
        'current_aps': current_aps,
        'aps_delta': aps_delta,
        'saved_bursaries_closing': saved_bursaries_closing,
        'saved_courses_closing': saved_courses_closing,
        'new_matches_count': new_matches_count,
        'tip': tip,
        'view_link': 'https://scancourse.co.za',
        'site_name': 'Scancourse',
    }


# ── Send ────────────────────────────────────────────────────────────

def send_digest(user) -> bool:
    """Build the per-user digest and send it. Returns True on send."""
    ctx = build_digest(user)
    if ctx is None:
        return False
    if not user.email:
        return False

    subject = (
        f'Your week on Scancourse — {ctx["current_aps"]} APS' if ctx['current_aps']
        else 'Your week on Scancourse'
    )

    try:
        html_body = render_to_string('emails/weekly_digest.html', ctx)
        text_body = render_to_string('emails/weekly_digest.txt', ctx)
    except Exception as e:
        logger.warning('Digest render failed for %s: %s', user.email, e)
        return False

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(
                settings, 'DEFAULT_FROM_EMAIL', 'info@scancourse.co.za'),
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        logger.warning('Digest send failed for %s: %s', user.email, e)
        return False


def send_weekly_digests_for_all() -> int:
    """Top-level cron entry point. Returns the count sent."""
    User = get_user_model()
    sent = 0
    for u in User.objects.filter(is_active=True).iterator():
        if not u.email:
            continue
        ok = send_digest(u)
        if ok:
            sent += 1
    return sent
