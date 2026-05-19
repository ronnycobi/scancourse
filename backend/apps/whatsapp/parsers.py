"""
Parse free-text WhatsApp messages into structured subject/mark lists.

Accepts formats like:
  English 75
  Maths: 68
  Physical Sciences - 72
  Life Sciences 80%
  Geography 65, Afrikaans 60
"""
import re

# Match: word(s) + optional separator + number 0-100
SUBJECT_LINE_RE = re.compile(
    r'([A-Za-z][A-Za-z\s/\-&]+?)[\s:.\-=]+(\d{1,3})\s*%?',
    re.IGNORECASE,
)


def parse_marks(text: str) -> list[dict]:
    """Extract subjects + marks from free text."""
    subjects = []
    seen = set()

    # Split on commas, semicolons, and newlines
    chunks = re.split(r'[,;\n]+', text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        match = SUBJECT_LINE_RE.search(chunk)
        if not match:
            continue

        name_raw, mark_str = match.groups()
        name = name_raw.strip().rstrip(':-= ').strip()

        if len(name) < 3:
            continue

        try:
            mark = int(mark_str)
        except ValueError:
            continue

        if not (0 <= mark <= 100):
            continue

        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        subjects.append({'name': name, 'mark': mark})

    return subjects


def normalise_phone(twilio_from: str) -> str:
    """Strip 'whatsapp:' prefix from Twilio phone number."""
    return twilio_from.replace('whatsapp:', '').strip()
