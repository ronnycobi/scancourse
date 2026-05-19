"""
Conversation flow handlers for the WhatsApp bot.

Each handler returns a string reply (or None if reply was sent async).
The handlers mutate session state to track where the conversation is.
"""
import logging
import os
import tempfile
import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.bursaries.models import Bursary
from apps.institutions.models import Institution
from apps.ocr.aps_calculator import calculate_aps
from apps.ocr.models import APSResult, Report, Subject
from apps.ocr.ocr_service import extract_text, parse_subjects_from_text
from .models import WhatsAppSession
from .parsers import parse_marks
from .twilio_client import download_media

logger = logging.getLogger(__name__)
User = get_user_model()


# ════════════════════════════════════════════════════════════════
# Menu / state helpers
# ════════════════════════════════════════════════════════════════

WELCOME = (
    "Hi 👋 I'm Scan, your study guide.\n\n"
    "I can help you find courses, calculate your APS, and discover bursaries — all here on WhatsApp.\n\n"
    "What would you like to do?\n\n"
    "1️⃣  Calculate my APS\n"
    "2️⃣  Universities still open\n"
    "3️⃣  Bursaries closing soon\n"
    "4️⃣  Ask me anything 🤖\n\n"
    "Reply with a number or send a photo of your report card 📄"
)

MENU_HINT = "\n\nType *menu* anytime to start over."


def show_menu(session: WhatsAppSession) -> str:
    session.reset()
    return WELCOME


def get_or_create_user(phone: str) -> User:
    """Lookup user by phone or auto-create a passwordless WhatsApp-only account."""
    try:
        user = User.objects.get(phone_number=phone)
        return user
    except User.DoesNotExist:
        pass

    # Auto-create using phone as username
    username = f'wa_{phone.lstrip("+").replace("-", "")[:30]}'
    email = f'{username}@whatsapp.scancourse.local'
    user = User.objects.create_user(
        username=username,
        email=email,
        phone_number=phone,
    )
    user.set_unusable_password()
    user.save()
    logger.info(f'Auto-created WhatsApp user {phone}')
    return user


# ════════════════════════════════════════════════════════════════
# Top-level dispatch
# ════════════════════════════════════════════════════════════════

def handle_message(
    session: WhatsAppSession,
    text: str,
    media_url: str | None = None,
    media_type: str | None = None,
) -> str:
    """Main entrypoint — returns the reply string."""
    text_clean = (text or '').strip()
    text_lower = text_clean.lower()

    # Universal commands always work, regardless of state
    if text_lower in ('menu', 'reset', 'cancel', 'start', 'hi', 'hello', 'hey', 'help'):
        return show_menu(session)

    # Media (photo / PDF) is handled the same way regardless of state
    if media_url:
        return handle_media(session, media_url, media_type)

    # Route based on session state
    state = session.state
    if state == 'idle':
        return handle_idle(session, text_clean)
    if state == 'awaiting_marks':
        return handle_marks_input(session, text_clean)
    if state == 'awaiting_bursary_pick':
        return handle_bursary_pick(session, text_clean)
    if state == 'awaiting_uni_pick':
        return handle_uni_pick(session, text_clean)
    if state == 'chatting_ai':
        return handle_ai_chat(session, text_clean)

    # Fallback
    return show_menu(session)


# ════════════════════════════════════════════════════════════════
# State: idle (main menu)
# ════════════════════════════════════════════════════════════════

def handle_idle(session: WhatsAppSession, text: str) -> str:
    choice = text.strip()

    if choice == '1' or 'aps' in text.lower() or 'mark' in text.lower():
        session.state = 'awaiting_marks'
        session.save(update_fields=['state'])
        return (
            "Great! Let's calculate your APS 🎯\n\n"
            "Send me your subjects and marks like this:\n\n"
            "_English 75_\n"
            "_Maths 68_\n"
            "_Physical Sciences 72_\n"
            "_Life Sciences 80_\n"
            "_Geography 65_\n"
            "_Afrikaans 60_\n"
            "_Life Orientation 85_\n\n"
            "Or send a photo of your report card 📄"
        )

    if choice == '2' or 'open' in text.lower() or 'universit' in text.lower():
        return list_open_universities(session)

    if choice == '3' or 'bursar' in text.lower():
        return list_bursaries(session)

    if choice == '4' or 'ai' in text.lower() or 'ask' in text.lower():
        session.state = 'chatting_ai'
        session.context = {'history': []}
        session.save(update_fields=['state', 'context'])
        return (
            "✨ Chat mode on. Ask me anything about studying in SA — courses, bursaries, careers.\n\n"
            "Try things like:\n"
            "• What can I study with APS 28?\n"
            "• Which bursaries close soon?\n"
            "• Tell me about UCT\n\n"
            "Type *menu* to exit chat."
        )

    return (
        "I didn't catch that 😅\n\n" + WELCOME
    )


# ════════════════════════════════════════════════════════════════
# State: awaiting_marks
# ════════════════════════════════════════════════════════════════

def handle_marks_input(session: WhatsAppSession, text: str) -> str:
    subjects = parse_marks(text)

    if len(subjects) < 4:
        return (
            "I could only read a few subjects from that 😕\n\n"
            "Please send at least 6 subjects, one per line, like:\n\n"
            "_English 75_\n_Maths 68_\n_Physical Sciences 72_\n\n"
            "Or send a photo of your report card 📄"
        )

    aps_data = calculate_aps(subjects)
    save_aps_result(session, aps_data)

    return format_aps_reply(aps_data)


def save_aps_result(session: WhatsAppSession, aps_data: dict):
    if not session.user:
        session.user = get_or_create_user(session.phone_number)
        session.save(update_fields=['user'])

    APSResult.objects.create(
        user=session.user,
        total_aps=aps_data['total_aps'],
        subjects_data=aps_data['subjects'],
    )
    session.reset()


def format_aps_reply(aps_data: dict) -> str:
    aps = aps_data['total_aps']
    subjects = aps_data['subjects']

    label = 'Excellent 🌟' if aps >= 35 else 'Good 👍' if aps >= 28 else 'Fair' if aps >= 20 else 'Below average'

    lines = [f"Your APS is *{aps}* ({label})\n"]
    for s in subjects[:8]:
        if s['is_life_orientation']:
            lines.append(f"  • {s['name']}: {s['mark']}% _(LO not counted)_")
        else:
            lines.append(f"  • {s['name']}: {s['mark']}% — {s['aps_points']} pts")

    eligible_courses = match_courses_for_aps(aps)
    if eligible_courses:
        lines.append("\n🎓 *Courses you qualify for:*")
        for c in eligible_courses[:6]:
            lines.append(f"  • {c}")

    lines.append("\n_Type *3* for bursaries, *4* to chat with AI, or *menu_*")
    return '\n'.join(lines)


def match_courses_for_aps(aps: int) -> list[str]:
    from apps.courses.models import Course
    qs = Course.objects.filter(
        is_active=True,
        offerings__is_active=True,
        offerings__min_aps__lte=aps,
    ).distinct().order_by('-offerings__min_aps')[:8]
    return [c.name for c in qs]


# ════════════════════════════════════════════════════════════════
# Universities still open
# ════════════════════════════════════════════════════════════════

def list_open_universities(session: WhatsAppSession) -> str:
    today = timezone.now().date()
    qs = Institution.objects.filter(
        is_active=True,
    ).filter(
        # Either application_open=True, or has a future deadline
        application_deadline__gte=today,
    ).order_by('application_deadline')[:10]

    if not qs:
        qs = Institution.objects.filter(is_active=True, application_open=True)[:10]

    if not qs:
        session.reset()
        return "I couldn't find any universities currently open. Check our app for the latest list. 📱"

    lines = ["📍 *Universities accepting applications:*\n"]
    options = []
    for i, inst in enumerate(qs, 1):
        deadline = inst.application_deadline.strftime('%d %b %Y') if inst.application_deadline else 'rolling'
        lines.append(
            f"{i}. *{inst.short_name or inst.name}* ({inst.province}) — APS {inst.min_aps}+ · closes {deadline}"
        )
        options.append({'id': inst.id, 'name': inst.name, 'short_name': inst.short_name})

    lines.append("\nReply with a number for full details, or *menu* to go back.")

    session.state = 'awaiting_uni_pick'
    session.context = {'options': options}
    session.save(update_fields=['state', 'context'])
    return '\n'.join(lines)


def handle_uni_pick(session: WhatsAppSession, text: str) -> str:
    options = session.context.get('options', [])
    try:
        idx = int(text.strip()) - 1
        if 0 <= idx < len(options):
            inst = Institution.objects.get(id=options[idx]['id'])
            return format_university_detail(session, inst)
    except (ValueError, Institution.DoesNotExist):
        pass

    return "Reply with the number of a university from the list, or *menu* to go back."


def format_university_detail(session: WhatsAppSession, inst: Institution) -> str:
    deadline = inst.application_deadline.strftime('%d %B %Y') if inst.application_deadline else 'rolling intake'
    lines = [
        f"🏫 *{inst.name}*",
        f"📍 {inst.city}, {inst.province}",
        f"⭐ Min APS: {inst.min_aps}",
        f"📅 Closes: {deadline}",
    ]
    if inst.nsfas_accredited:
        lines.append("✅ NSFAS accredited")
    if inst.application_url:
        lines.append(f"\n🌐 Apply: {inst.application_url}")
    if inst.contact_email:
        lines.append(f"📧 {inst.contact_email}")

    lines.append(MENU_HINT)
    session.reset()
    return '\n'.join(lines)


# ════════════════════════════════════════════════════════════════
# Bursaries
# ════════════════════════════════════════════════════════════════

def list_bursaries(session: WhatsAppSession) -> str:
    today = timezone.now().date()
    soon = today + timedelta(days=120)
    qs = Bursary.objects.filter(
        is_active=True,
        application_deadline__gte=today,
        application_deadline__lte=soon,
    ).order_by('application_deadline')[:10]

    if not qs:
        qs = Bursary.objects.filter(is_active=True)[:10]

    if not qs:
        session.reset()
        return "No bursaries available right now. Check our app for updates! 🎁"

    lines = ["🎁 *Bursaries available:*\n"]
    options = []
    for i, b in enumerate(qs, 1):
        deadline = b.application_deadline.strftime('%d %b') if b.application_deadline else 'rolling'
        lines.append(f"{i}. *{b.name}* — {b.field} · closes {deadline}")
        options.append({'id': b.id})

    lines.append("\nReply with a number for details, or *menu* to go back.")

    session.state = 'awaiting_bursary_pick'
    session.context = {'options': options}
    session.save(update_fields=['state', 'context'])
    return '\n'.join(lines)


def handle_bursary_pick(session: WhatsAppSession, text: str) -> str:
    options = session.context.get('options', [])
    try:
        idx = int(text.strip()) - 1
        if 0 <= idx < len(options):
            bursary = Bursary.objects.get(id=options[idx]['id'])
            return format_bursary_detail(session, bursary)
    except (ValueError, Bursary.DoesNotExist):
        pass

    return "Reply with the number of a bursary from the list, or *menu* to go back."


def format_bursary_detail(session: WhatsAppSession, bursary: Bursary) -> str:
    deadline = bursary.application_deadline.strftime('%d %B %Y') if bursary.application_deadline else 'rolling'
    lines = [
        f"🎁 *{bursary.name}*",
        f"by {bursary.provider}",
        f"\n📚 Field: {bursary.field}",
        f"💰 Type: {bursary.get_funding_type_display()}",
        f"📅 Deadline: {deadline}",
    ]
    if bursary.eligibility:
        lines.append(f"\n*Eligibility:*\n{bursary.eligibility}")
    if bursary.coverage:
        lines.append(f"\n*Covers:* {', '.join(bursary.coverage)}")
    if bursary.application_url:
        lines.append(f"\n🌐 Apply: {bursary.application_url}")

    lines.append(MENU_HINT)
    session.reset()
    return '\n'.join(lines)


# ════════════════════════════════════════════════════════════════
# AI chat
# ════════════════════════════════════════════════════════════════

def handle_ai_chat(session: WhatsAppSession, text: str) -> str:
    from apps.ai_assistant.ai_service import get_ai_response

    if not session.user:
        session.user = get_or_create_user(session.phone_number)
        session.save(update_fields=['user'])

    history = session.context.get('history', [])

    try:
        reply = get_ai_response(session.user, text, history)
    except Exception as e:
        logger.exception(f'Gemini error: {e}')
        return "I'm having trouble right now 😕 Please try again in a moment, or type *menu*."

    history.append({'role': 'user', 'content': text})
    history.append({'role': 'assistant', 'content': reply})
    session.context = {'history': history[-20:]}  # keep last 20
    session.save(update_fields=['context'])

    # WhatsApp limit ~1600 chars per message
    if len(reply) > 1500:
        reply = reply[:1500] + '...\n\n_(reply truncated — type menu to exit chat)_'
    return reply + "\n\n_Type *menu* to exit chat._"


# ════════════════════════════════════════════════════════════════
# Media handler (photo / PDF report card)
# ════════════════════════════════════════════════════════════════

def handle_media(session: WhatsAppSession, media_url: str, media_type: str | None) -> str:
    is_pdf = media_type and 'pdf' in media_type.lower()
    is_image = media_type and media_type.lower().startswith('image/')

    if not (is_pdf or is_image):
        return "Please send a photo or PDF of your report card 📄"

    if not session.user:
        session.user = get_or_create_user(session.phone_number)
        session.save(update_fields=['user'])

    content = download_media(media_url)
    if not content:
        return "I couldn't download that file 😕 Please try again."

    ext = 'pdf' if is_pdf else 'jpg'
    tmp_path = os.path.join(tempfile.gettempdir(), f'wa_{uuid.uuid4().hex}.{ext}')
    with open(tmp_path, 'wb') as f:
        f.write(content)

    try:
        text = extract_text(tmp_path, 'pdf' if is_pdf else 'image')
        subjects = parse_subjects_from_text(text)

        if len(subjects) < 4:
            return (
                "Hmm, I struggled to read that report card 😕\n\n"
                "Please try:\n"
                "• A clearer, well-lit photo\n"
                "• Or type your marks: _English 75_, _Maths 68_, etc."
            )

        aps_data = calculate_aps(subjects)
        save_aps_result(session, aps_data)
        return "✅ Got your report card!\n\n" + format_aps_reply(aps_data)

    except Exception as e:
        logger.exception(f'OCR failed for {tmp_path}: {e}')
        return "Something went wrong reading your report 😕 Try again or type your marks manually."

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
