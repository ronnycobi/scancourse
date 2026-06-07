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

PROMPT_STRUCTURED = '''You are reading a South African school report card (DBE NSC or IEB). Extract every academic subject and its final mark.

Return ONLY valid JSON in this exact shape:

{
  "subjects": [
    {"name": "<full subject name>", "mark": <integer 0-100>, "confidence": "<high|medium|low>"}
  ],
  "school": "<school name if visible, else null>",
  "grade": "<grade_10 | grade_11 | grade_12 | other>",
  "board": "<DBE | IEB | unknown>"
}

CRITICAL RULES — read carefully:

1. WHICH MARK TO USE
   - Reports often show multiple columns: Term 1, Term 2, Term 3, Term 4, Final/Year/Promotion/Average.
   - You MUST pick the FINAL one. Priority order: "Promotion Mark" > "Final Mark" > "Year Mark" > "Year Average" > "Final Average" > the LAST term column.
   - NEVER return a single term's mark when a final/year mark is present.
   - If only one mark column exists, use it.

2. MARK FORMAT
   - Always an INTEGER 0-100. Convert "75%" → 75, "75/100" → 75.
   - If the report uses NSC achievement levels instead of percentages, convert by lower bound: L7 → 80, L6 → 70, L5 → 60, L4 → 50, L3 → 40, L2 → 30, L1 → 20.
   - If you genuinely cannot read the mark, OMIT THE ROW. Do not guess.

3. SUBJECT NAMES — use the FULL canonical name, not the abbreviation
   - "Mathematics" (not "Maths", "Math")
   - "Mathematical Literacy" (not "Math Lit", "Maths Lit")
   - Languages: always keep the LEVEL — "English Home Language", "English First Additional Language", "Afrikaans Home Language", "isiZulu First Additional Language", etc. Never just "English".
   - "Physical Sciences" (not "Physics", "Phys Sci")
   - "Life Sciences" (not "Biology", "Bio")
   - "Computer Applications Technology" (not "CAT")
   - "Information Technology" (not "IT")
   - "Business Studies", "Accounting", "Economics", "Geography", "History" — full names.
   - IEB Advanced Programme subjects: keep the "Advanced Programme " prefix (e.g. "Advanced Programme Mathematics").

4. INCLUDE
   - All academic subjects, INCLUDING Life Orientation.
   - Advanced Programme subjects (IEB only).

5. EXCLUDE
   - Attendance, conduct, effort, application, participation, extra-murals.
   - Comments, signatures, principal/teacher remarks.
   - Aggregate rows: "Total", "Average", "Overall", "Achievement Level".
   - Foundation-phase summary blocks ("Languages", "Mathematics", "Life Skills" as broad categories on a primary report).

6. CONFIDENCE
   - "high" — row is crisp, name and mark unambiguous.
   - "medium" — name or mark partially obscured but you're 90%+ certain.
   - "low" — you're guessing because of blur/glare/handwriting. Prefer to omit instead of returning "low".

Output ONLY the JSON. No markdown fences. No prose before or after.
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
            generation_config={
                'response_mime_type': 'application/json',
                'temperature': 0,
            },
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


# Aggregate / non-subject rows the LLM sometimes returns despite the
# prompt — drop them post-hoc so we never store "Total: 78" as a subject.
_NOT_A_SUBJECT = {
    'total', 'totals', 'average', 'overall', 'overall average',
    'aggregate', 'achievement level', 'composite', 'grand total',
    'attendance', 'conduct', 'effort', 'application', 'participation',
    'extra mural', 'extra-mural', 'extramural', 'comment', 'comments',
    'signature', 'principal', 'class teacher',
}


def extract_subjects(image_path: str) -> dict | None:
    """
    Preferred path — returns:
        {'subjects': [{'name': 'Mathematics', 'mark': 65,
                       'confidence': 'high'}, ...],
         'school': '<name or null>',
         'grade': 'grade_12',
         'board': 'DBE'}
    Returns None if Gemini didn't produce parseable JSON.
    """
    if not is_available():
        raise RuntimeError('GEMINI_API_KEY is not set.')
    _configure()
    path = Path(image_path)
    model = genai.GenerativeModel(
        settings.GEMINI_MODEL,
        generation_config={
            'response_mime_type': 'application/json',
            # Temperature 0 for OCR — we want deterministic, not creative.
            # Any randomness here turns into wrong marks.
            'temperature': 0,
        },
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
    cleaned = []
    seen_names = set()
    for s in subjects:
        name = (s.get('name') or '').strip()
        confidence = (s.get('confidence') or 'high').strip().lower()
        try:
            mark = int(s.get('mark'))
        except (TypeError, ValueError):
            continue
        if not name or not (0 <= mark <= 100):
            continue
        # Drop low-confidence guesses — better to ask the user to verify
        # a missing row than to silently feed a wrong mark into APS.
        if confidence == 'low':
            logger.info('Dropping low-confidence row: %s (%d)', name, mark)
            continue
        # Drop aggregate / non-academic rows that slipped through.
        lname = name.lower().strip()
        if lname in _NOT_A_SUBJECT:
            continue
        # Dedupe — if the LLM returned the same subject twice (mid-term +
        # final), keep the higher mark (matches the merge logic users see
        # downstream in best-marks-across-reports).
        key = lname
        if key in seen_names:
            for existing in cleaned:
                if existing['name'].lower() == key:
                    if mark > existing['mark']:
                        existing['mark'] = mark
                        existing['confidence'] = confidence
                    break
            continue
        seen_names.add(key)
        cleaned.append({
            'name': name,
            'mark': mark,
            'confidence': confidence,
        })
    data['subjects'] = cleaned
    return data
