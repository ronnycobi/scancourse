"""
UKZN (University of KwaZulu-Natal) scraper.

UKZN publishes its complete undergraduate prospectus as a single PDF at:
  https://applications.ukzn.ac.za/prospectus/undergraduate/latest

The PDF contains structured tables (~5 columns) per college:
  | Programme Name | CAO Code | Entry Requirements | APS Range | Duration |

Each row is one programme. CAO codes follow the format `KN-X-YYY` where:
  - X = campus letter (W=Westville, H=Howard College, P=Pietermaritzburg, E=Edgewood)
  - YYY = qualification code

A single cell may contain multiple CAO codes (one per campus) joined by '|'
or newlines — we expand these to one offering per campus.
"""
import io
import logging
import re
from urllib.parse import urlparse

import requests
import pdfplumber

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)

UKZN_PROSPECTUS_URL = 'https://applications.ukzn.ac.za/prospectus/undergraduate/latest'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)

# CAO code: KN-X-YYY (e.g. KN-W-BPA, KN-H-BEV, KN-P-BS3)
CAO_CODE_RE = re.compile(r'\bKN-[A-Z]-[A-Z0-9]{2,5}\b')

# Campus letter → name (used for the campus column on each offering)
CAMPUS_LETTER = {
    'W': 'Westville',
    'H': 'Howard College',
    'P': 'Pietermaritzburg',
    'E': 'Edgewood',
    'M': 'Medical School',
    'D': 'Durban',
}

# Map college name (top of each table) to default field code
COLLEGE_TO_FIELD = {
    'agriculture, engineering': 'engineering',
    'engineering': 'engineering',
    'agriculture': 'agriculture',
    'science': 'science',
    'health sciences': 'health',
    'humanities': 'humanities',
    'law and management': 'business',
    'law': 'law',
    'commerce': 'business',
    'management': 'business',
    'education': 'education',
}


# ════════════════════════════════════════════════════════════════
# HTTP
# ════════════════════════════════════════════════════════════════

def fetch_pdf_bytes(url: str = UKZN_PROSPECTUS_URL, timeout: int = 180) -> bytes:
    logger.info(f'Downloading UKZN prospectus from {url}')
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    if r.content[:4] != b'%PDF':
        raise RuntimeError('UKZN prospectus URL did not return a PDF')
    return r.content


# ════════════════════════════════════════════════════════════════
# Subject + APS extraction from the "Entry Requirements" cell
# ════════════════════════════════════════════════════════════════

# Subject patterns UKZN uses, e.g.:
#   "NSC-Deg with Maths and Phys Sci 5"
#   "Maths 5 & Eng & LO 4"
#   "Engl & LO L4, isiZulu L4"
#   "Mathematical Literacy" / "Maths" / "Math"
SUBJECT_LEVEL_RE = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Maths(?:\s+Lit)?|Math\s+Lit|Math|'
    r'Engl?(?:ish)?(?:\s+(?:HL|FAL))?|LO|Life Orientation|'
    r'Phys(?:ical)?\s+Sci(?:ence)?s?|Phy\s+Sci|'
    r'Life\s+Sci(?:ence)?s?|'
    r'Geography|History|Accounting|Economics|Business Studies|'
    r'isiZulu|Afrikaans|Agric(?:ultural)?\s+Sci(?:ence)?s?)'
    r'\s*(?:L|Level\s+)?(\d)',
    re.IGNORECASE,
)

# APS range like "48-33" or "48-30" or single "30"
APS_RANGE_RE = re.compile(r'\b(\d{2})\s*-\s*(\d{2})\b')
APS_SINGLE_RE = re.compile(r'\b(\d{2})\b')

# Duration like "4 yrs" or "3 years"
DURATION_RE = re.compile(r'(\d(?:[.,]\d)?)\s*(?:yrs?|years?)', re.IGNORECASE)


def normalise_subject(name: str) -> str:
    n = name.strip().lower()
    if n in ('engl', 'english'):           return 'English'
    if n.startswith('engl'):                return 'English'
    if n in ('lo', 'life orientation'):     return 'Life Orientation'
    if n.startswith('maths lit') or n in ('math lit',): return 'Mathematical Literacy'
    if n.startswith('mathematics literacy'):return 'Mathematical Literacy'
    if n in ('maths', 'math', 'mathematics'): return 'Mathematics'
    if n.startswith('phys'):                return 'Physical Sciences'
    if n.startswith('life sci'):            return 'Life Sciences'
    if n.startswith('agric'):               return 'Agricultural Sciences'
    return name.strip().title()


def parse_subjects(req_text: str) -> list[dict]:
    """Extract NSC subject requirements from a UKZN entry-requirements cell."""
    if not req_text:
        return []
    seen = set()
    out = []
    # Replace newlines and pipes with spaces so multi-line cells join cleanly
    blob = re.sub(r'[\n|]', ' ', req_text)
    for m in SUBJECT_LEVEL_RE.finditer(blob):
        subj = normalise_subject(m.group(1))
        try:
            level = int(m.group(2))
        except ValueError:
            continue
        if not (1 <= level <= 7):
            continue
        if subj.lower() in seen:
            continue
        seen.add(subj.lower())
        out.append({'subject': subj, 'min_level': level})
    return out


def parse_aps(aps_cell: str, req_cell: str = '') -> int:
    """Extract APS — prefer range minimum from APS column, fall back to req text."""
    for cell in (aps_cell, req_cell):
        if not cell:
            continue
        m = APS_RANGE_RE.search(cell)
        if m:
            high, low = int(m.group(1)), int(m.group(2))
            return min(high, low)  # the lower bound is the minimum entry APS
    # Fallback: any 2-digit number in the APS cell
    for cell in (aps_cell,):
        if not cell:
            continue
        for n in APS_SINGLE_RE.findall(cell):
            v = int(n)
            if 18 <= v <= 50:
                return v
    return 0


def parse_duration(dur_cell: str, req_cell: str = '') -> float | None:
    for cell in (dur_cell, req_cell):
        if not cell:
            continue
        m = DURATION_RE.search(cell)
        if m:
            try:
                return float(m.group(1).replace(',', '.'))
            except ValueError:
                continue
    return None


# ════════════════════════════════════════════════════════════════
# Table parsing
# ════════════════════════════════════════════════════════════════

def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', (text or '').replace('\n', ' ')).strip()


def detect_college(table) -> str:
    """The first non-empty cell in the first 2 rows usually names the college."""
    for row in table[:2]:
        for c in row:
            if c and 'college' in c.lower():
                return _clean(c)
    return ''


def detect_field_from_college(college_name: str) -> str:
    blob = (college_name or '').lower()
    for keyword, field_code in COLLEGE_TO_FIELD.items():
        if keyword in blob:
            return field_code
    return 'other'


def find_header_row(table) -> int:
    """Find the row index that has 'Programme Name' or 'CAO Code' in it."""
    for i, row in enumerate(table[:5]):
        joined = ' '.join((c or '').lower() for c in row)
        if 'programme name' in joined or 'cao code' in joined:
            return i
    return -1


def parse_table(table) -> list[ParsedCourse]:
    """Parse one extract_tables() table into ParsedCourse list."""
    if not table or len(table) < 3:
        return []

    college = detect_college(table)
    default_field = detect_field_from_college(college)

    header_idx = find_header_row(table)
    if header_idx < 0:
        return []

    header = [(_clean(c)).lower() for c in table[header_idx]]
    # Find which column has each field
    def col_idx(*keywords):
        for i, h in enumerate(header):
            if any(k in h for k in keywords):
                return i
        return -1

    name_col = col_idx('programme name', 'qualification', 'programme')
    code_col = col_idx('cao code', 'cao')
    req_col  = col_idx('entry requirements', 'requirements', 'entry')
    aps_col  = col_idx('aps')
    dur_col  = col_idx('duration')

    if name_col < 0 or code_col < 0:
        return []

    # Track the previous programme name in case of cells split across rows
    courses: list[ParsedCourse] = []
    last_name = ''

    for row in table[header_idx + 1:]:
        if not row or len(row) <= max(name_col, code_col):
            continue

        name = _clean(row[name_col])
        code_cell = _clean(row[code_col]) if code_col < len(row) else ''
        req_text = _clean(row[req_col]) if 0 <= req_col < len(row) else ''
        aps_text = _clean(row[aps_col]) if 0 <= aps_col < len(row) else ''
        dur_text = _clean(row[dur_col]) if 0 <= dur_col < len(row) else ''

        # If this row's name is empty, attach to the previous name (table cell wraps)
        if not name and last_name:
            name = last_name

        if name:
            last_name = name

        # Find every CAO code in the code cell — each is a separate campus offering
        codes = CAO_CODE_RE.findall((row[code_col] or '').replace('\n', ' '))
        if not codes:
            continue
        if not name or len(name) < 4:
            continue

        for code in codes:
            campus_letter = code.split('-')[1] if '-' in code else ''
            campus_name = CAMPUS_LETTER.get(campus_letter, campus_letter)

            course = ParsedCourse(
                name=name[:300],
                institution_short_name='UKZN',
                programme_code=code,
                campus=campus_name,
                source_excerpt=f'UKZN | {college} | code {code}',
            )

            course.field = (
                classify_field(name) if classify_field(name) != 'other' else default_field
            )
            course.level = classify_level(name)
            course.subject_requirements = parse_subjects(req_text)
            course.min_aps = parse_aps(aps_text, req_text)

            dur = parse_duration(dur_text, req_text)
            if dur:
                course.duration_years = dur
            else:
                # Default by level
                DEFAULTS = {
                    'certificate': 1.0, 'diploma': 3.0, 'advanced_diploma': 1.0,
                    'degree': 3.0, 'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
                }
                course.duration_years = DEFAULTS.get(course.level, 3.0)

            course.description = (
                f'Undergraduate qualification at the University of KwaZulu-Natal, '
                f'offered through the {college or "relevant college"}.'
            )

            courses.append(course)

    return courses


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════
# Fallback: text-based extraction for pages where tables fail
# ════════════════════════════════════════════════════════════════

# Programme-name detector for paragraph layout — UKZN uses headings like
# "Bachelor of X", "B Com X", "B Sc X", "B Soc Sc X", etc.
NAME_PREFIXES = (
    'Bachelor of', 'Bachelor in',
    'B Com', 'BCom', 'B Sc', 'BSc', 'B Soc Sc', 'BSocSc', 'B Soc',
    'B A', 'BA in', 'B Ed', 'BEd', 'B Bus Sc', 'B Theol',
    'B Cur', 'B Mus', 'B BSC', 'B Bus',
    'Diploma in', 'Higher Certificate', 'Advanced Diploma',
    'LLB', 'MBChB',
)

NAME_LINE_RE = re.compile(
    r'^(?:'
    r'(?:Bachelor of|Bachelor in)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|B\s*Com\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Sc\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Soc\s*Sc\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*A\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Ed\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Mus\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Theol\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Cur\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*Bus\s*Sc\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|B\s*BSC\b[\w\s,&\-\(\)\.:]{0,80}'
    r'|Higher\s+Certificate\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|Advanced\s+Diploma\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|Diploma\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|LLB\b'
    r'|MBChB\b'
    r')',
    re.MULTILINE,
)


def _looks_like_name_line(line: str) -> bool:
    """Return True if `line` reads like a programme heading."""
    s = line.strip()
    if not (5 <= len(s) <= 150):
        return False
    if any(s.startswith(p) for p in NAME_PREFIXES):
        return True
    return False


def parse_text_for_codes(text: str, default_field: str = 'other') -> list[ParsedCourse]:
    """
    Fallback parser for pages where pdfplumber can't extract tables.
    Uses CAO codes as anchors and looks for the programme name above them.
    """
    if not text:
        return []

    courses: list[ParsedCourse] = []

    # Find every CAO code occurrence with its position
    matches = list(CAO_CODE_RE.finditer(text))
    if not matches:
        return []

    lines = text.split('\n')
    # Build line-index → char-offset map
    char_offsets = [0]
    for line in lines:
        char_offsets.append(char_offsets[-1] + len(line) + 1)

    def char_to_line(pos: int) -> int:
        for i, off in enumerate(char_offsets):
            if off > pos:
                return max(0, i - 1)
        return len(lines) - 1

    # Group consecutive codes that belong to the same programme.
    # If two codes appear within ~6 lines of each other and there's no name
    # between them, they're sibling campuses of one programme.
    code_positions = [(m.start(), m.group(0)) for m in matches]
    seen_codes_emitted = set()

    for pos, code in code_positions:
        if code in seen_codes_emitted:
            continue

        # Walk upwards from this code to find the nearest programme-name line
        line_idx = char_to_line(pos)
        name = ''
        for back in range(line_idx, max(0, line_idx - 20), -1):
            candidate = lines[back].strip()
            # Skip lines that ARE the code itself or mostly-codes
            if CAO_CODE_RE.search(candidate):
                continue
            if _looks_like_name_line(candidate):
                name = re.sub(r'\s+', ' ', candidate).strip().rstrip(',.;:')
                break

        if not name or len(name) < 5:
            continue

        # Walk a window forward (next 25 lines) for entry requirements + APS
        window_text = '\n'.join(lines[line_idx:min(len(lines), line_idx + 25)])

        aps = parse_aps('', window_text)
        subjects = parse_subjects(window_text)

        # Find any sibling codes in the same window — they're separate campus offerings
        sibling_codes = list(dict.fromkeys(CAO_CODE_RE.findall(window_text)))

        for sib_code in sibling_codes:
            if sib_code in seen_codes_emitted:
                continue
            seen_codes_emitted.add(sib_code)

            campus_letter = sib_code.split('-')[1] if '-' in sib_code else ''
            campus_name = CAMPUS_LETTER.get(campus_letter, campus_letter)

            course = ParsedCourse(
                name=name[:300],
                institution_short_name='UKZN',
                programme_code=sib_code,
                campus=campus_name,
                source_excerpt=f'UKZN | text-extracted | {sib_code}',
            )
            course.field = (
                classify_field(name) if classify_field(name) != 'other' else default_field
            )
            course.level = classify_level(name)
            course.subject_requirements = subjects
            course.min_aps = aps

            DEFAULTS = {
                'certificate': 1.0, 'diploma': 3.0, 'advanced_diploma': 1.0,
                'degree': 3.0, 'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
            }
            course.duration_years = DEFAULTS.get(course.level, 3.0)
            course.description = (
                'Undergraduate qualification at the University of KwaZulu-Natal.'
            )

            courses.append(course)

    return courses


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_ukzn(institution_short_name: str = 'UKZN') -> list[ParsedCourse]:
    """Download UKZN prospectus PDF and extract every programme."""
    pdf_bytes = fetch_pdf_bytes()
    logger.info(f'Downloaded {len(pdf_bytes):,} bytes')

    all_courses: list[ParsedCourse] = []
    seen_keys: set[tuple[str, str]] = set()  # (name, code) dedupe key

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pn, page in enumerate(pdf.pages):
            page_courses_before = len(all_courses)

            # ── PASS 1: tables ──────────────────────────
            try:
                tables = page.extract_tables()
            except Exception as e:
                logger.warning(f'  Page {pn+1} table extract failed: {e}')
                tables = []

            for table in tables:
                courses = parse_table(table)
                for c in courses:
                    key = (c.name.lower().strip(), c.programme_code)
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    c.institution_short_name = institution_short_name
                    all_courses.append(c)

            # ── PASS 2: text fallback for codes the tables missed ──
            try:
                text = page.extract_text() or ''
            except Exception:
                text = ''

            if text:
                # Detect which codes are still unaccounted for on this page
                page_codes = set(CAO_CODE_RE.findall(text))
                covered = {c.programme_code for c in all_courses}
                missing = page_codes - covered

                if missing:
                    text_courses = parse_text_for_codes(text)
                    for c in text_courses:
                        key = (c.name.lower().strip(), c.programme_code)
                        if key in seen_keys:
                            continue
                        if c.programme_code not in missing:
                            continue  # already covered by tables
                        seen_keys.add(key)
                        c.institution_short_name = institution_short_name
                        all_courses.append(c)

            page_added = len(all_courses) - page_courses_before
            if page_added:
                logger.info(f'  Page {pn+1}: +{page_added} programmes (total {len(all_courses)})')

    logger.info(f'Parsed {len(all_courses)} UKZN programmes')
    return all_courses


def parse_ukzn_url(start_url: str = '', institution_short_name: str = 'UKZN') -> list[ParsedCourse]:
    """Public entry point matching the parse_xx_url(...) signature used by other parsers."""
    return parse_ukzn(institution_short_name)
