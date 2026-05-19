"""
UJ-specific PDF parser.

UJ's undergraduate prospectus uses multi-column tables where SOME cells
(notably programme codes, subject requirements, "Not accepted") are stored
in REVERSE character order due to font rendering. The other columns
(programme name, APS, careers, campus) are normal.

This parser:
1. Uses pdfplumber.extract_tables() to get column-aware data
2. Detects + reverses cells whose text appears backwards
3. Tracks "section headers" like "Bachelor of Commerce Degree (3 years)"
   so programme rows inherit the right qualification prefix
4. Builds ParsedCourse instances ready for review/save
"""
import logging
import re

import pdfplumber

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
# Reversed-text detection + recovery
# ════════════════════════════════════════════════════════════════

# Tokens that only appear in REVERSED English text (so their presence
# means we should flip the string)
REVERSED_INDICATORS = (
    'toN', 'detpecca', 'EMMARGORP', 'noitacfiilauQ', 'edoC',
    'lacitamehtaM', 'scitamehtaM', 'hsilgnE', 'ycaretiL',
)


def looks_reversed(text: str) -> bool:
    """Heuristic: does this string look like it was rendered character-reversed?"""
    if not text:
        return False
    for marker in REVERSED_INDICATORS:
        if marker in text:
            return True
    # Common reversed pattern: ends with "(" instead of starting with it
    stripped = text.strip()
    if stripped.endswith('(') or stripped.endswith('+%'):
        return True
    # Code patterns that match when reversed (e.g. Q01L2B → B2L10Q)
    reversed_text = '\n'.join(l[::-1] for l in text.split('\n'))
    if CODE_PATTERN.search(reversed_text) and not CODE_PATTERN.search(text):
        return True
    return False


def maybe_reverse(text: str) -> str:
    """Reverse the string (line-wise) if it looks like it was character-flipped."""
    if not text:
        return ''
    if looks_reversed(text):
        return '\n'.join(line[::-1] for line in text.split('\n'))
    return text


# ════════════════════════════════════════════════════════════════
# Section-header detection
# ════════════════════════════════════════════════════════════════

# A row is a "section header" (qualification prefix) rather than a
# programme if it matches one of these patterns
SECTION_HEADER_PATTERNS = [
    re.compile(r'^Bachelor of [A-Z][\w\s]+', re.IGNORECASE),
    re.compile(r'^Diplomas?\s*\(', re.IGNORECASE),  # "Diplomas (3 years)"
    re.compile(r'^Diploma\b', re.IGNORECASE),
    re.compile(r'^Advanced Diploma\b', re.IGNORECASE),
    re.compile(r'^Extended Diplomas?\b', re.IGNORECASE),
    re.compile(r'^Higher Certificate\b', re.IGNORECASE),
    re.compile(r'^B(Com|Sc|A|Ed|Eng|Tech|cur|Mil|Soc)\b', re.IGNORECASE),
    re.compile(r'^LLB\b'),
    re.compile(r'^MBChB\b'),
]


# UJ campus codes — extracted from the prospectus
UJ_CAMPUS_CODES = {
    'APK': 'Auckland Park Kingsway',
    'APB': 'Auckland Park Bunting Road',
    'DFC': 'Doornfontein Campus',
    'SWC': 'Soweto Campus',
}


def normalise_campus(raw: str) -> str:
    """Convert messy 'KPA / CWS' (reversed campus codes) into 'Auckland Park Kingsway, Soweto Campus'."""
    if not raw:
        return ''
    text = raw.replace('\n', ' ').strip()

    # Find all 3-letter codes in original form
    codes = re.findall(r'\b[A-Z]{3}\b', text)
    if not codes:
        return text[:50]

    translated = []
    for code in codes:
        # Try forward first
        if code in UJ_CAMPUS_CODES:
            translated.append(UJ_CAMPUS_CODES[code])
            continue
        # Try reversed (e.g. KPA → APK)
        rev = code[::-1]
        if rev in UJ_CAMPUS_CODES:
            translated.append(UJ_CAMPUS_CODES[rev])
            continue
        # Unknown — keep as-is (could be a typo or new campus)
        translated.append(code)

    # Deduplicate while preserving order
    seen = set()
    result = []
    for t in translated:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return ', '.join(result)


def is_section_header(text: str) -> bool:
    if not text:
        return False
    text = text.strip().split('\n')[0]  # first line only
    return any(p.search(text) for p in SECTION_HEADER_PATTERNS)


def derive_full_name(section_header: str, programme_name: str) -> str:
    """Combine 'Bachelor of Commerce Degree (3 years)' + 'ACCOUNTING' = 'Bachelor of Commerce in Accounting'."""
    if not section_header:
        return programme_name.title()

    # Strip "(3 years)" / "(4 years)" suffix from section header
    header_clean = re.sub(r'\s*\(\d+\s*years?\)', '', section_header).strip()
    # Remove trailing "Degree", "Programme"
    header_clean = re.sub(r'\s+(Degree|Programme)s?\s*$', '', header_clean, flags=re.IGNORECASE).strip()

    # Title-case the all-caps programme name
    name_title = programme_name.title().strip()

    # If header ends with "of X" or "of X and Y", join with "in"
    if re.search(r'\bof\b', header_clean, re.IGNORECASE):
        return f'{header_clean} in {name_title}'
    return f'{header_clean} {name_title}'


# ════════════════════════════════════════════════════════════════
# Per-table-row → ParsedCourse
# ════════════════════════════════════════════════════════════════

# UJ programme codes have a strict format we should enforce to avoid false positives.
# Real examples: B34A5Q, B3NE4Q, D34LGQ, B2I01Q, B6SU0Q, B1CEMQ, DI1401
# • Letter (B/D/N) + digit + 3-4 alphanumerics + Q
# • OR DI + 4 digits (Diploma codes from older format)
CODE_PATTERN = re.compile(
    r'\b(?:[BDN]\d{1,2}[A-Z0-9]{2,4}Q|DI\d{4})\b'
)

# Convert NSC percentage threshold → level
PERCENT_TO_LEVEL = [
    (80, 7), (70, 6), (60, 5), (50, 4), (40, 3), (30, 2),
]


def percent_to_level(pct_str: str) -> int | None:
    """e.g. '60%' → 5"""
    m = re.search(r'(\d{1,3})\s*%', pct_str)
    if not m:
        return None
    pct = int(m.group(1))
    for threshold, level in PERCENT_TO_LEVEL:
        if pct >= threshold:
            return level
    return 1


def _clean_name(text: str) -> str:
    """Clean a multi-line name cell into a single normalised string."""
    if not text:
        return ''
    # Replace internal newlines with spaces, collapse whitespace
    cleaned = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
    # Strip trailing punctuation
    cleaned = re.sub(r'[,.;:]+\s*$', '', cleaned)
    return cleaned


def _find_code_index(cells: list[str]) -> tuple[int, str] | tuple[None, str]:
    """
    Return the column index that holds the programme code, plus the code itself.
    Tries both forward and reversed forms of each cell since some columns are reversed.
    """
    for i, c in enumerate(cells):
        if not c:
            continue
        # Try forward
        m = CODE_PATTERN.search(c)
        if m:
            return i, m.group(0)
        # Try reversed (line-by-line to preserve multi-line cells)
        reversed_c = '\n'.join(line[::-1] for line in c.split('\n'))
        m = CODE_PATTERN.search(reversed_c)
        if m:
            return i, m.group(0)
    return None, ''


def parse_row(row: list, current_section: str, institution: str = 'UJ') -> ParsedCourse | None:
    """Convert one extracted-table row into a ParsedCourse, or None if invalid."""
    cells = [c.strip() if c else '' for c in row]
    if not cells or not any(cells):
        return None

    # Apply reversal where needed (now smart enough to detect reversed codes too)
    cells_clean = [maybe_reverse(c) for c in cells]

    # ── Find the programme code (the anchor for this row) ───
    code_idx, code = _find_code_index(cells_clean)
    if code_idx is None:
        return None

    # ── Programme name = column 0 (cleaned) ──
    name_raw = _clean_name(cells_clean[0])
    if not name_raw or len(name_raw) < 3:
        return None

    # Skip rows whose col 0 is just the section header (we already track it)
    if is_section_header(name_raw):
        return None

    # Skip column legends/footers
    junk_markers = {
        'programme', 'nsc endorsement', 'page', 'subject', 'campus', 'qualification',
        'closing dates for applications', 'undergraduate prospectus',
        'degree programmes', 'extended degree programmes',
        'diploma programmes', 'extended diploma programmes',
        'fundamental component', 'vocational component',
    }
    if name_raw.lower() in junk_markers or any(
        name_raw.lower().startswith(j) for j in (
            'the university', '2027', '2026', 'closing dates',
        )
    ):
        return None

    # ── Detect table layout: is the column after the code an APS or a %? ──
    after_code = cells_clean[code_idx + 1] if code_idx + 1 < len(cells_clean) else ''
    has_aps_column = bool(re.search(r'^\s*\d{2}\s*$', after_code.replace('\n', ' ').strip()))

    aps = 0
    subjects = []
    subject_names_in_order = ['English', 'Mathematics', 'Mathematical Literacy', 'Technical Mathematics']

    if has_aps_column:
        # ── Layout A: degree tables ── code | APS | English-level | Maths-level | ...
        m = re.search(r'\b(\d{2})\b', after_code)
        if m and 15 <= int(m.group(1)) <= 50:
            aps = int(m.group(1))
        # Subject levels start after the APS column
        start = code_idx + 2
        for offset, subj_name in enumerate(subject_names_in_order):
            idx = start + offset
            if idx >= len(cells_clean):
                break
            cell = cells_clean[idx]
            if 'not accepted' in cell.lower() or not cell.strip():
                continue
            m = re.search(r'\b([1-7])\b', cell)
            if m:
                subjects.append({'subject': subj_name, 'min_level': int(m.group(1))})
    else:
        # ── Layout B: diploma tables ── code | English% | Maths% | MathLit% | ...
        # Convert percentages to NSC levels and let user adjust APS in review UI
        start = code_idx + 1
        for offset, subj_name in enumerate(subject_names_in_order):
            idx = start + offset
            if idx >= len(cells_clean):
                break
            cell = cells_clean[idx]
            if 'not accepted' in cell.lower() or not cell.strip():
                continue
            level = percent_to_level(cell)
            if level:
                subjects.append({'subject': subj_name, 'min_level': level})

    # Fallback: any 2-digit number in row could be APS
    if not aps:
        for c in cells_clean:
            for tok in re.findall(r'\b\d{2}\b', c.replace('\n', ' ')):
                if 18 <= int(tok) <= 50:
                    aps = int(tok)
                    break
            if aps:
                break

    # ── Campus — last cell containing 3-letter codes (CWS, KPA, etc.) ──
    campus = ''
    campus_idx = -1
    for idx in range(len(cells_clean) - 1, -1, -1):
        c = cells_clean[idx]
        if not c or not c.strip():
            continue
        clean = c.replace('\n', ' ').strip()
        if len(clean) > 60:
            continue
        if re.search(r'\b[A-Z]{3}\b', c) or re.search(r'\b[A-Z]{3}\b', maybe_reverse(c)):
            normalised = normalise_campus(c)
            if normalised:
                campus = normalised
                campus_idx = idx
                break

    # ── Careers — longest readable cell BEFORE the campus column ──
    careers = ''
    careers_start = code_idx + 2 + len(subject_names_in_order) if has_aps_column else code_idx + 1 + len(subject_names_in_order)
    candidate_end = campus_idx if campus_idx > 0 else len(cells_clean)
    longest = ''
    for c in cells_clean[max(0, careers_start - 1):candidate_end]:
        if not c:
            continue
        clean = re.sub(r'\s+', ' ', c.replace('\n', ' ')).strip()
        if len(clean) < 15:
            continue
        if looks_reversed(c) or CODE_PATTERN.search(c):
            continue
        if len(clean) > len(longest):
            longest = clean
    careers = longest

    # ── Build full name from section header + col 0 name ──
    full_name = derive_full_name(current_section, name_raw)

    # ── Description — auto-generate from what we have ──
    desc_parts = []
    duration_text = ''
    dur_match = re.search(r'\((\d+(?:\.\d+)?)\s*years?\)', current_section or '', re.IGNORECASE)
    if dur_match:
        duration_text = f"{dur_match.group(1)}-year"
    if duration_text:
        desc_parts.append(f"{duration_text} {full_name} programme at the University of Johannesburg.")
    else:
        desc_parts.append(f"{full_name} programme at the University of Johannesburg.")
    if campus:
        desc_parts.append(f"Offered at {campus}.")
    if careers:
        desc_parts.append(f"Career paths include: {careers[:300]}.")
    description = ' '.join(desc_parts)[:1500]

    course = ParsedCourse(
        name=full_name[:300],
        institution_short_name=institution,
        min_aps=aps,
        campus=campus,
        programme_code=code,
        description=description,
        subject_requirements=subjects,
        career_opportunities=careers[:1000],
        source_excerpt=f'UJ code: {code}',
    )
    course.field = classify_field(full_name + ' ' + (current_section or ''))
    course.level = classify_level(full_name + ' ' + (current_section or ''))

    # Duration — try section header first, then col 0, then default by level
    dur_match = re.search(r'\((\d+(?:\.\d+)?)\s*years?\)', current_section or '', re.IGNORECASE)
    if not dur_match:
        # Sometimes the duration is in col 0 itself: "Diplomas (3 years)"
        dur_match = re.search(r'\((\d+(?:\.\d+)?)\s*years?\)', name_raw, re.IGNORECASE)
    if dur_match:
        course.duration_years = float(dur_match.group(1))
    else:
        # Default by level
        DEFAULTS = {
            'certificate': 1.0, 'diploma': 3.0, 'advanced_diploma': 1.0,
            'degree': 3.0, 'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
        }
        course.duration_years = DEFAULTS.get(course.level, 3.0)

    return course


# ════════════════════════════════════════════════════════════════
# Main entry point
# ════════════════════════════════════════════════════════════════

def parse_uj_pdf(pdf_path_or_bytes, institution: str = 'UJ') -> list[ParsedCourse]:
    """Extract programmes from a UJ undergraduate prospectus."""
    courses = []
    seen_names = set()

    if isinstance(pdf_path_or_bytes, bytes):
        import io
        pdf_source = io.BytesIO(pdf_path_or_bytes)
    else:
        pdf_source = pdf_path_or_bytes

    with pdfplumber.open(pdf_source) as pdf:
        for page_num, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception as e:
                logger.warning(f'Page {page_num+1} table extraction failed: {e}')
                continue

            current_section = ''
            for table in tables:
                for row in table:
                    cells = [c.strip() if c else '' for c in row]
                    if not cells or not any(cells):
                        continue

                    first_cell = maybe_reverse(cells[0]).strip()

                    # Update section header if this row is one
                    if is_section_header(first_cell):
                        # Strip trailing "(3 years)" but keep main title
                        current_section = first_cell.split('\n')[0]
                        continue

                    # Otherwise try to parse as a programme
                    course = parse_row(row, current_section, institution)
                    if not course or not course.name:
                        continue

                    key = course.name.lower().strip()
                    if key in seen_names:
                        continue
                    seen_names.add(key)
                    courses.append(course)

    logger.info(f'UJ parser extracted {len(courses)} programmes')
    return courses
