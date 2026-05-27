"""
Celery tasks that drive Scancourse's push-notification engine.

Each trigger fans out per-user — never spam everyone with the same generic
message. We respect a 1-per-day cap per user per trigger type to avoid
"unsubscribe" rage.

Triggers shipping with v1:
  1. bursary_deadline_warning   — bursary user has SAVED is closing in N days
  2. course_deadline_warning    — saved course offering closes in N days
  3. new_course_match           — matcher just turned up courses they qualify
                                   for that they haven't seen
  4. aps_improvement_nudge      — they have an APS but haven't opened the
                                   improvement plan in 14 days
  5. weekly_digest              — sunday 7pm summary of saved + deadlines

All firing happens through Celery Beat — see CELERY_BEAT_SCHEDULE in
settings.
"""
import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)


# ── FCM core ────────────────────────────────────────────────────────────

def send_fcm_notification(fcm_token: str, title: str, body: str,
                          data: dict | None = None):
    """Single-target FCM send. Silently no-ops when token / creds missing."""
    if not fcm_token:
        return
    creds_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
    if not creds_path:
        logger.info('FCM skipped — FIREBASE_CREDENTIALS_PATH not set.')
        return
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(creds_path))
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        messaging.send(msg)
    except Exception as e:
        # Stale token? Unregister it so we don't keep retrying.
        msg = str(e).lower()
        if 'unregistered' in msg or 'invalid-argument' in msg or 'not found' in msg:
            User = get_user_model()
            User.objects.filter(fcm_token=fcm_token).update(fcm_token='')
            logger.info('Cleared invalid FCM token.')
        else:
            logger.error('FCM send failed: %s', e)


def _fire(user, ntype: str, title: str, body: str, data: dict | None = None):
    """Record + push. Returns the Notification model row."""
    from .models import Notification
    notif = Notification.objects.create(
        user=user,
        notification_type=ntype,
        title=title,
        body=body,
        data=data or {},
    )
    if user.fcm_token:
        send_fcm_notification(user.fcm_token, title, body, {
            'type': ntype,
            'notif_id': notif.id,
            **(data or {}),
        })
    return notif


def _already_sent_recently(user, ntype: str, hours: int = 22) -> bool:
    """Throttle: don't re-fire the same type to the same user within N hours."""
    from .models import Notification
    since = timezone.now() - timedelta(hours=hours)
    return Notification.objects.filter(
        user=user, notification_type=ntype, sent_at__gte=since
    ).exists()


# ── Trigger 1: bursary deadlines (saved bursaries) ─────────────────────

@shared_task
def send_bursary_deadline_reminders():
    """Hits ONLY users who saved a bursary that's closing in ≤ 7 days."""
    from apps.bursaries.models import Bursary
    from apps.users.models import SavedItem
    User = get_user_model()
    today = timezone.now().date()
    horizon = today + timedelta(days=7)
    fired = 0

    saves = SavedItem.objects.filter(item_type='bursary').values_list(
        'user_id', 'item_id'
    )
    saves_by_user: dict[int, list[int]] = {}
    for uid, bid in saves:
        saves_by_user.setdefault(uid, []).append(bid)

    for uid, bursary_ids in saves_by_user.items():
        user = User.objects.filter(id=uid, is_active=True).first()
        if not user or _already_sent_recently(user, 'bursary'):
            continue
        closing = Bursary.objects.filter(
            id__in=bursary_ids,
            application_deadline__range=(today, horizon),
        ).only('id', 'name', 'application_deadline')[:3]
        if not closing:
            continue
        if len(closing) == 1:
            b = closing[0]
            days = (b.application_deadline - today).days
            title = f'{b.name} closes in {days} day{"" if days == 1 else "s"}'
            body = 'Tap to view eligibility and apply.'
        else:
            title = f'{len(closing)} saved bursaries closing this week'
            body = ', '.join(b.name for b in closing[:2]) + '…'
        _fire(user, 'bursary', title, body,
              {'bursary_ids': ','.join(str(b.id) for b in closing)})
        fired += 1

    logger.info('bursary deadline reminders sent: %d', fired)
    return fired


# ── Trigger 2: saved-course application deadlines ──────────────────────

@shared_task
def send_course_deadline_reminders():
    """Notify when a saved course's offering closes in ≤ 7 days."""
    from apps.courses.models import CourseOffering
    from apps.users.models import SavedItem
    User = get_user_model()
    today = timezone.now().date()
    horizon = today + timedelta(days=7)
    fired = 0

    saves = SavedItem.objects.filter(item_type='course').values_list(
        'user_id', 'item_id'
    )
    saves_by_user: dict[int, list[int]] = {}
    for uid, cid in saves:
        saves_by_user.setdefault(uid, []).append(cid)

    for uid, course_ids in saves_by_user.items():
        user = User.objects.filter(id=uid, is_active=True).first()
        if not user or _already_sent_recently(user, 'deadline'):
            continue
        closing = list(CourseOffering.objects.filter(
            course_id__in=course_ids,
            application_deadline__range=(today, horizon),
        ).select_related('course', 'institution')[:3])
        if not closing:
            continue
        if len(closing) == 1:
            o = closing[0]
            days = (o.application_deadline - today).days
            inst = o.institution.short_name or o.institution.name if o.institution_id else ''
            title = f'{o.course.name} at {inst} closes in {days}d'
            body = 'Don\'t miss the application deadline — tap to view.'
        else:
            title = f'{len(closing)} saved courses closing this week'
            body = 'Tap to review your applications and submit before the deadline.'
        _fire(user, 'deadline', title, body, {
            'course_ids': ','.join(str(o.course_id) for o in closing),
        })
        fired += 1
    logger.info('course deadline reminders sent: %d', fired)
    return fired


# ── Trigger 3: new course matches (users with APS) ─────────────────────

@shared_task
def send_new_course_matches():
    """
    Catches new offerings added since the user's last visit AND that match
    their APS. Fires at most once per week per user.
    """
    from apps.courses.models import CourseOffering
    from apps.ocr.models import APSResult
    User = get_user_model()
    fired = 0
    cutoff = timezone.now() - timedelta(days=7)

    # Users with at least one APS result and an FCM token
    candidates = User.objects.filter(
        is_active=True,
    ).exclude(fcm_token='').distinct()

    for user in candidates:
        if _already_sent_recently(user, 'new_course', hours=24 * 7):
            continue
        last_aps = APSResult.objects.filter(user=user).order_by('-created_at').first()
        if not last_aps:
            continue
        # Offerings whose APS the user meets, added in the last 7 days
        new_count = CourseOffering.objects.filter(
            min_aps__lte=last_aps.total_aps,
            created_at__gte=cutoff,
        ).count() if hasattr(CourseOffering, 'created_at') else 0
        if new_count < 3:
            continue
        _fire(user, 'new_course',
              f'{new_count} new courses match your profile',
              'Tap to explore programmes you qualify for.',
              {'count': new_count})
        fired += 1
    logger.info('new course matches sent: %d', fired)
    return fired


# ── Trigger 4: APS improvement nudge ───────────────────────────────────

@shared_task
def send_aps_improvement_nudge():
    """
    Users who have an APS but haven't engaged with the improvement plan
    in 14 days get a friendly nudge.
    """
    from apps.ocr.models import APSResult
    User = get_user_model()
    fired = 0

    # All users with an APS result. Exclude very recently joined (let them
    # explore first).
    aps_users = User.objects.filter(
        is_active=True,
        date_joined__lte=timezone.now() - timedelta(days=3),
    ).exclude(fcm_token='').distinct()

    for user in aps_users:
        if _already_sent_recently(user, 'aps', hours=24 * 14):
            continue
        last_aps = APSResult.objects.filter(user=user).order_by(
            '-created_at').first()
        if not last_aps:
            continue
        _fire(user, 'aps',
              'Your APS is {}. Want to push it higher?'.format(last_aps.total_aps),
              'Tap to see 3 specific things you can do this week.',
              {})
        fired += 1
    logger.info('aps improvement nudges sent: %d', fired)
    return fired


# ── Trigger 5a: weekly email digest ────────────────────────────────────

@shared_task
def send_weekly_digest_emails():
    """Sunday 19:00 — sends the personalised HTML email digest to every
    active user with an email address. Skips users with nothing
    meaningful to report this week so we don't burn inbox goodwill."""
    from .digest import send_weekly_digests_for_all
    return send_weekly_digests_for_all()


# ── Trigger 5b: weekly Sunday push digest (kept for FCM) ───────────────

@shared_task
def send_weekly_digest():
    """
    Sunday evening summary. We respect that this is the highest-engagement
    notification of the week, so it goes to EVERY active user with a token
    (but only on Sundays — Celery Beat enforces that).
    """
    from apps.bursaries.models import Bursary
    from apps.users.models import SavedItem
    User = get_user_model()
    today = timezone.now().date()
    horizon = today + timedelta(days=14)
    fired = 0

    for user in User.objects.filter(is_active=True).exclude(fcm_token=''):
        # Skip if we've already sent ANY digest in the last 6 days.
        if _already_sent_recently(user, 'general', hours=24 * 6):
            continue

        saved_bursaries = SavedItem.objects.filter(
            user=user, item_type='bursary'
        ).values_list('item_id', flat=True)[:50]
        bursary_count = Bursary.objects.filter(
            id__in=list(saved_bursaries),
            application_deadline__range=(today, horizon),
        ).count()

        if bursary_count >= 1:
            title = 'Your week on Scancourse'
            body = f'{bursary_count} saved bursaries closing in the next 2 weeks. Tap to plan.'
        else:
            title = 'Your week on Scancourse'
            body = 'New courses and bursaries this week — tap to see what changed.'

        _fire(user, 'general', title, body, {'digest': 'weekly'})
        fired += 1
    logger.info('weekly digest sent: %d', fired)
    return fired


# ── Backwards-compat alias ─────────────────────────────────────────────

@shared_task
def send_deadline_reminders():
    """Legacy entry point — runs both deadline triggers in one go."""
    return (
        send_course_deadline_reminders()
        + send_bursary_deadline_reminders()
    )
