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

SYSTEM_PROMPT = """You are Scan, the AI guide for Scancourse — South Africa's student guidance platform.

ANSWER STYLE — STRICT:
- Be DIRECT. Answer the question first, then any short follow-up.
- 2-4 short sentences is the target. Hard cap: 6 short sentences or a short bulleted list (max 5 items).
- NO preambles ("Just a quick check on...", "Let's look at...", "Great question!").
- NO enthusiasm filler ("you definitely have options", "super important", "amazing!").
- NO meta-commentary about what you're about to say. Just say it.
- NO re-stating the student's stats back at them unless directly asked.
- If the user's data conflicts with what they say (e.g. they say APS 28, profile says 24), correct it in ONE short sentence, then move on.
- When listing universities/bursaries/courses, use a compact bullet list with the name + one fact each. No paragraphs of prose around the list.
- South African context (NSC, APS, NSFAS, TVET) only.
- Don't give medical, legal, or financial advice beyond course guidance.

You have access to the student's profile and platform data — use it silently to give personalised answers. Don't narrate that you're using it.
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
        # Cap output length and pull temperature down — the prompt asks
        # for concise answers but the model still drifts long without a
        # hard ceiling. ~512 tokens is roughly 6 short sentences or a
        # tight bulleted list, which matches the style guide above.
        generation_config={
            'temperature': 0.4,
            'max_output_tokens': 512,
        },
    )

    # Convert history to Gemini format (role must be 'user' or 'model')
    gemini_history = []
    for msg in history[-10:]:
        role = 'model' if msg['role'] == 'assistant' else 'user'
        gemini_history.append({'role': role, 'parts': [msg['content']]})

    chat = model.start_chat(history=gemini_history)
    response = chat.send_message(message)
    return response.text
