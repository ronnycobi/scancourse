"""
Twilio WhatsApp wrapper — sends messages and downloads inbound media.
"""
import logging
import requests
from django.conf import settings
from twilio.rest import Client
from twilio.request_validator import RequestValidator

logger = logging.getLogger(__name__)


def get_client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def get_validator() -> RequestValidator:
    return RequestValidator(settings.TWILIO_AUTH_TOKEN)


def send_message(to: str, body: str, media_urls: list[str] | None = None) -> dict:
    """
    Send a WhatsApp message. `to` should be in 'whatsapp:+27xxx' format.
    Returns {'sid': ..., 'error': ...}
    """
    if not to.startswith('whatsapp:'):
        to = f'whatsapp:{to}'

    try:
        client = get_client()
        params = {
            'from_': settings.TWILIO_WHATSAPP_FROM,
            'to': to,
            'body': body,
        }
        if media_urls:
            params['media_url'] = media_urls

        msg = client.messages.create(**params)
        return {'sid': msg.sid, 'error': None}
    except Exception as e:
        logger.exception(f'Failed to send WhatsApp message to {to}: {e}')
        return {'sid': None, 'error': str(e)}


def download_media(media_url: str) -> bytes | None:
    """
    Download a media file Twilio sent us. Twilio media URLs require basic auth
    with the account SID + auth token.
    """
    try:
        resp = requests.get(
            media_url,
            auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
            timeout=30,
            allow_redirects=True,
        )
        resp.raise_for_status()
        return resp.content
    except Exception as e:
        logger.exception(f'Failed to download Twilio media {media_url}: {e}')
        return None


def validate_request(url: str, post_data: dict, signature: str) -> bool:
    """Verify the request actually came from Twilio (HMAC-SHA1)."""
    if not settings.TWILIO_VALIDATE_SIGNATURE:
        return True
    if not settings.TWILIO_AUTH_TOKEN:
        logger.warning('TWILIO_AUTH_TOKEN not set — signature validation skipped')
        return True
    return get_validator().validate(url, post_data, signature)
