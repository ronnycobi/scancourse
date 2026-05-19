"""
Twilio WhatsApp webhook endpoint.

Twilio POSTs to /whatsapp/webhook/ for every inbound message.
We respond with TwiML containing the reply, OR send via Twilio REST API.
This implementation uses TwiML (synchronous reply) for low latency.
"""
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from twilio.twiml.messaging_response import MessagingResponse

from .handlers import handle_message
from .models import WhatsAppMessage, WhatsAppSession
from .parsers import normalise_phone
from .twilio_client import validate_request

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request):
    """
    Handle inbound WhatsApp message from Twilio.
    Twilio sends application/x-www-form-urlencoded POST with fields like:
      From=whatsapp:+27xxx, Body=..., NumMedia=1, MediaUrl0=..., MediaContentType0=...
    """
    # 1. Validate signature
    signature = request.headers.get('X-Twilio-Signature', '')
    url = request.build_absolute_uri()
    post_data = request.POST.dict()

    if not validate_request(url, post_data, signature):
        logger.warning(f'Invalid Twilio signature from {request.META.get("REMOTE_ADDR")}')
        return HttpResponseForbidden('Invalid signature')

    # 2. Parse inbound
    from_raw = post_data.get('From', '')
    body = post_data.get('Body', '').strip()
    num_media = int(post_data.get('NumMedia', '0') or 0)

    media_url = post_data.get('MediaUrl0') if num_media > 0 else None
    media_type = post_data.get('MediaContentType0') if num_media > 0 else None
    phone = normalise_phone(from_raw)

    if not phone:
        return HttpResponse(str(MessagingResponse()), content_type='application/xml')

    # 3. Get/create session
    session, _ = WhatsAppSession.objects.get_or_create(phone_number=phone)

    # 4. Log inbound
    WhatsAppMessage.objects.create(
        session=session,
        direction='in',
        body=body,
        media_url=media_url or '',
    )

    # 5. Process and get reply
    try:
        reply_text = handle_message(session, body, media_url, media_type)
    except Exception as e:
        logger.exception(f'Handler error for {phone}: {e}')
        reply_text = "Sorry, something went wrong 😕 Type *menu* to start over."

    # 6. Log outbound
    WhatsAppMessage.objects.create(
        session=session,
        direction='out',
        body=reply_text or '',
    )

    # 7. Respond via TwiML
    twiml = MessagingResponse()
    if reply_text:
        twiml.message(reply_text)
    return HttpResponse(str(twiml), content_type='application/xml')


@csrf_exempt
def health(request):
    """Simple health check Twilio can hit."""
    return HttpResponse('ok', content_type='text/plain')
