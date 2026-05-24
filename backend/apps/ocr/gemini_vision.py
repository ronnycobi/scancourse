"""
Gemini multimodal OCR for report cards.

Sends the report-card image directly to Gemini 1.5 Flash and asks for
structured subject+mark extraction in a single call. Returns either
plain text (for compatibility with the existing pipeline) or structured
JSON (preferred — bypasses the brittle regex parser).

Activated when GEMINI_API_KEY is set in settings. No extra billing needed
beyond the Gemini free tier (which is much more generous than Vision).
"""
from __future__ import annotations

import json
import logging
import mimetypes
import re
from pathlib import Path

import google.generativeai as genai
from django.conf import settings

logger = logging.getLogger(__name__)


def is_available() -> bool:
    return bool(getattr(settings, 'GEMINI_API_KEY', ''))


def _configure():
    """Idempotent SDK configuration."""
    genai.configure(api_key=settings.GEMINI_API_KEY)


def _mime_for(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    ext = path.suffix.lower()
    return {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
        '.png': 'image/png', '.webp': 'image/webp',
        '.heic': 'image/heic', '.pdf': 'application/pdf',
    }.get(ext, 'application/octet-stream')


PROMPT_TEXT = (
    'You are reading a South African school report card. Extract ALL visible '
    'text accurately, preserving line breaks. Include subject names, marks, '
    "and percentages. Don't summarise — output the raw text exactly as it appears."
)

PROMPT_STRUCTURED = '''You are reading a South African Grade 11 or 12 school report card.

Extract every subject and its final mark. Return ONLY valid JSON in this exact shape:

{
  "subjects": [
    {"name": "<subject name as written on the report>", "mark": <integer 0-100>}
  ],
  "school": "<school name if visible, else null>",
  "grade": "<grade_10 | grade_11 | grade_12 | other, based on the report>"
}

Rules:
- "mark" must be an integer between 0 and 100. Convert any "63%" → 63.
- If a subject appears multiple times (term 1, term 2, etc.), use the FINAL / FINAL AVERAGE / YEAR MARK.
- Include Life Orientation if present.
- Ignore class teachers' comments and signatures.
- Do not include subjects that are not academic (e.g. attendance, conduct).
- Output ONLY the JSON — no markdown fences, no prose before or after.
'''


PROMPT_PRECHECK = '''You are doing a quick quality check on an image a learner is about to upload as their school report card.

Look at the image and return ONLY valid JSON in this exact shape:

{
  "is_report": <true if this looks like a school report / academic transcript, false otherwise>,
  "quality": "<one of: good, blurry, dark, cropped, glare>",
  "marks_readable": <true if subject marks are clearly visible and readable, false if not>,
  "issues": [<short strings, e.g. "blurry text", "marks cut off at bottom", "wrong document">],
  "suggestion": "<one short sentence telling the learner what to do, e.g. 'Retake the photo with better lighting'. Empty string if no issues.>"
}

Be strict: if marks aren't crisp and readable, mark quality lower. Output ONLY the JSON.
'''


def precheck_image(image_path: str) -> dict:
    """
    Fast pre-flight check before a real OCR upload. Returns:
      {is_report: bool, quality: str, marks_readable: bool,
       issues: [str], suggestion: str}
    On any failure, returns a permissive "ok" verdict so the user
    isn't blocked by an AI hiccup.
    """
    fallback = {
        'is_report': True,
        'quality': 'good',
        'marks_readable': True,
        'issues': [],
        'suggestion': '',
    }
    if not is_available():
        return fallback
    try:
        _configure()
        path = Path(image_path)
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config={'response_mime_type': 'application/json'},
        )
        response = model.generate_content([
            {'mime_type': _mime_for(path), 'data': path.read_bytes()},
            PROMPT_PRECHECK,
        ])
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '',
                     (response.text or '').strip(),
                     flags=re.IGNORECASE)
        data = json.loads(raw)
        # Defensive defaults
        return {
            'is_report': bool(data.get('is_report', True)),
            'quality': str(data.get('quality') or 'good'),
            'marks_readable': bool(data.get('marks_readable', True)),
            'issues': [str(x) for x in (data.get('issues') or [])][:5],
            'suggestion': str(data.get('suggestion') or '')[:240],
        }
    except Exception as e:
        logger.warning('Precheck failed, allowing upload: %s', e)
        return fallback


def extract_text(image_path: str) -> str:
    """Plain-text OCR via Gemini. Drop-in for the existing pipeline."""
    if not is_available():
        raise RuntimeError('GEMINI_API_KEY is not set.')
    _configure()
    path = Path(image_path)
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    image_bytes = path.read_bytes()
    response = model.generate_content([
        {'mime_type': _mime_for(path), 'data': image_bytes},
        PROMPT_TEXT,
    ])
    return response.text or ''


def extract_subjects(image_path: str) -> dict | None:
    """
    Preferred path — returns:
        {'subjects': [{'name': 'Mathematics', 'mark': 65}, ...],
         'school': '<name or null>',
         'grade': 'grade_12'}
    Returns None if Gemini didn't produce parseable JSON.
    """
    if not is_available():
        raise RuntimeError('GEMINI_API_KEY is not set.')
    _configure()
    path = Path(image_path)
    model = genai.GenerativeModel(
        settings.GEMINI_MODEL,
        generation_config={'response_mime_type': 'application/json'},
    )
    image_bytes = path.read_bytes()
    response = model.generate_content([
        {'mime_type': _mime_for(path), 'data': image_bytes},
        PROMPT_STRUCTURED,
    ])
    raw = (response.text or '').strip()
    # Strip code-fence wrappers if Gemini ignored the no-fences instruction.
    raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.IGNORECASE)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning('Gemini JSON parse failed: %s — raw: %s', e, raw[:300])
        return None

    subjects = data.get('subjects') or []
    # Defensive normalisation
    cleaned = []
    for s in subjects:
        name = (s.get('name') or '').strip()
        try:
            mark = int(s.get('mark'))
        except (TypeError, ValueError):
            continue
        if name and 0 <= mark <= 100:
            cleaned.append({'name': name, 'mark': mark})
    data['subjects'] = cleaned
    return data
