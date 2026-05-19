"""
AI motivation letter generator — uses Gemini to draft, refine, and personalise
SA university application motivation letters.
"""
import logging
from django.conf import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


SYSTEM_PROMPT = """You are an expert at writing motivation letters for South African university applications.

Your output must:
- Open with a clear statement of which course/programme the student is applying for
- Show genuine enthusiasm and specific reasons for choosing this institution
- Connect the student's background, marks, and achievements to the course
- Include 1–2 concrete experiences or interests that demonstrate fit
- Acknowledge any weaknesses constructively (e.g. lower marks in one subject)
- Close with a forward-looking statement about contribution and growth
- Be 350–500 words
- Use formal but personal South African English
- Avoid clichés like "passionate" or "dynamic"
- Sound authentic, not AI-generated — use specific details

Format the output as plain text with paragraph breaks. No markdown."""


REFINE_PROMPT = """You are refining a motivation letter. Apply the user's feedback while keeping the core message and structure.
Return the full revised letter — no commentary."""


def generate_motivation_letter(
    *, student_name: str, course_name: str, institution_name: str,
    student_background: str, key_achievements: str = '',
    why_this_course: str = '', why_this_institution: str = '',
    additional_info: str = '',
    tone: str = 'professional',
    language: str = 'en',
) -> str:
    """Generate a draft motivation letter using Gemini."""

    prompt_parts = [
        f"STUDENT NAME: {student_name}",
        f"APPLYING FOR: {course_name} at {institution_name}",
        f"STUDENT BACKGROUND: {student_background}",
    ]
    if key_achievements:
        prompt_parts.append(f"KEY ACHIEVEMENTS / EXPERIENCES: {key_achievements}")
    if why_this_course:
        prompt_parts.append(f"WHY THIS COURSE: {why_this_course}")
    if why_this_institution:
        prompt_parts.append(f"WHY THIS INSTITUTION: {why_this_institution}")
    if additional_info:
        prompt_parts.append(f"OTHER NOTES: {additional_info}")

    prompt_parts.append(f"\nTONE: {tone}")

    lang_map = {
        'en': 'English',
        'zu': 'isiZulu',
        'xh': 'isiXhosa',
        'af': 'Afrikaans',
        'st': 'Sesotho',
    }
    if language != 'en':
        prompt_parts.append(f"\nWRITE THE ENTIRE LETTER IN {lang_map.get(language, 'English')}.")

    prompt_parts.append("\nWrite the motivation letter now.")

    user_prompt = '\n'.join(prompt_parts)

    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
    )
    response = model.generate_content(
        user_prompt,
        generation_config={'temperature': 0.8, 'max_output_tokens': 1500},
    )
    return response.text.strip()


def refine_motivation_letter(current_letter: str, feedback: str) -> str:
    """Apply user feedback to refine an existing letter."""
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=REFINE_PROMPT,
    )
    prompt = f"CURRENT LETTER:\n\n{current_letter}\n\n\nUSER FEEDBACK:\n{feedback}\n\nReturn the revised letter."
    response = model.generate_content(
        prompt,
        generation_config={'temperature': 0.6, 'max_output_tokens': 1500},
    )
    return response.text.strip()
