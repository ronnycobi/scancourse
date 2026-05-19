"""
Celery tasks for sending push notifications.
"""
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def send_fcm_notification(fcm_token: str, title: str, body: str, data: dict = None):
    if not fcm_token:
        return
    try:
        import firebase_admin
        from firebase_admin import messaging

        if not firebase_admin._apps:
            cred = firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        messaging.send(message)
    except Exception as e:
        logger.error(f'FCM send failed: {e}')


@shared_task
def send_deadline_reminders():
    from django.contrib.auth import get_user_model
    from apps.deadlines.models import Deadline
    from .models import Notification

    User = get_user_model()
    upcoming = Deadline.objects.filter(
        is_active=True,
        deadline_date__range=(
            timezone.now().date(),
            timezone.now().date() + timedelta(days=7),
        )
    )

    for deadline in upcoming:
        for user in User.objects.filter(is_active=True).exclude(fcm_token=''):
            notif = Notification.objects.create(
                user=user,
                notification_type='deadline',
                title=f'Deadline: {deadline.title}',
                body=f'Application closes on {deadline.deadline_date.strftime("%d %B %Y")}',
                data={'deadline_id': deadline.id},
            )
            send_fcm_notification(
                user.fcm_token,
                notif.title,
                notif.body,
                notif.data,
            )
