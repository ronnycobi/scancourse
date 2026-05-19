"""
AI assistant service using Google Gemini with platform context injection.
"""
import logging
from django.conf import settings
import google.generativeai as genai

from apps.institutions.models import Institution
from apps.bursaries.models import Bursary
from apps.ocr.models import APSResult

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """You are Scan, the friendly AI assistant for Scancourse — South Africa's student guidance platform.
You help Grade 11, Grade 12, and gap year learners navigate university applications, bursaries, and career choices.

Your tone is:
- Friendly, encouraging, and supportive
- Use simple South African English
- Reference South African institutions and context
- Never give medical, legal, or financial advice beyond course guidance

You have access to the student's profile and platform data. Use it to give personalised answers.
Always be honest about what you know and don't know.
"""


def build_context(user) -> str:
    context_parts = []

    profile_ctx = f"""
STUDENT PROFILE:
- Grade: {user.grade or 'Not specified'}
- Province: {user.get_province_display() if user.province else 'Not specified'}
- Preferred field: {user.preferred_field or 'Not specified'}
- Dream career: {user.dream_career or 'Not specified'}
"""
    context_parts.append(profile_ctx)

    latest_aps = APSResult.objects.filter(user=user).order_by('-created_at').first()
    if latest_aps:
        subjects_summary = ', '.join(
            f"{s['name']} ({s['mark']}%)" for s in latest_aps.subjects_data[:6]
        )
        context_parts.append(f"APS SCORE: {latest_aps.total_aps}\nSUBJECTS: {subjects_summary}")

    institutions = Institution.objects.filter(is_active=True, application_open=True).values(
        'name', 'institution_type', 'province', 'min_aps', 'application_deadline'
    )[:15]
    if institutions:
        inst_lines = [
            f"- {i['name']} ({i['institution_type']}, {i['province']}) - Min APS: {i['min_aps']}, Deadline: {i['application_deadline']}"
            for i in institutions
        ]
        context_parts.append("INSTITUTIONS STILL OPEN:\n" + '\n'.join(inst_lines))

    from django.utils import timezone
    from datetime import timedelta
    soon = timezone.now().date() + timedelta(days=60)
    bursaries = Bursary.objects.filter(is_active=True, application_deadline__lte=soon).values(
        'name', 'provider', 'field', 'application_deadline', 'funding_type'
    )[:10]
    if bursaries:
        bur_lines = [
            f"- {b['name']} by {b['provider']} ({b['field']}) - Deadline: {b['application_deadline']}"
            for b in bursaries
        ]
        context_parts.append("BURSARIES CLOSING SOON:\n" + '\n'.join(bur_lines))

    return '\n'.join(context_parts)


def get_ai_response(user, message: str, history: list[dict]) -> str:
    context = build_context(user)
    system_with_context = SYSTEM_PROMPT + f"\n\nCURRENT PLATFORM DATA:\n{context}"

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_with_context,
    )

    # Convert history to Gemini format (role must be 'user' or 'model')
    gemini_history = []
    for msg in history[-10:]:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        gemini_history.append({'role': role, 'parts': [msg['content']]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(message)
    return response.text
