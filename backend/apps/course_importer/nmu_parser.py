"""
Nelson Mandela University (NMU) scraper.

NMU publishes its complete undergraduate catalogue in a single 2-page "Z-Card" PDF
at a stable URL. The Z-Card is a dense multi-column tri-fold:

  | Career field | Qualification | Faculty | Duration | AS-Maths | AS-MathsLit | AS-TechMaths | Subjects |

Each row contains up to 4 programme groups side-by-side. A single qualification
cell can hold multiple programme variants joined by '|', and each variant has
matching pipe-separated values in the AS columns.

This parser:
  1. Downloads the Z-Card PDF
  2. Uses pdfplumber.extract_tables() to get the column-aware data
  3. Walks each row column-by-column, finding qualification cells
  4. For each qualification, splits multi-programme cells and aligns AS values
"""
import io
import logging
import re

import requests
import pdfplumber

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)

NMU_ZCARD_URL = (
    'https://www.mandela.ac.za/www-new/media/Store/documents/StudyAtMandela/'
    'QuickGuides/Apply/NMU-Z-CARD-UNDERGRAD-PROGRAMME_DIGITAL-FA.pdf'
)
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)

# Programme name patterns NMU uses
QUAL_NAME_RE = re.compile(
    r'^(?:'
    r'Bachelor of [A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|BCom[\w\s,&\-\(\)\.:]{0,60}'
    r'|BSc[\w\s,&\-\(\)\.:]{0,60}'
    r'|BA\b[\w\s,&\-\(\)\.:]{0,60}'
    r'|BEd[\w\s,&\-\(\)\.:]{0,60}'
    r'|BVA\b[\w\s,&\-\(\)\.:]{0,40}'
    r'|BMus\b[\w\s,&\-\(\)\.:]{0,40}'
    r'|LLB\b'
    r'|MBChB\b'
    r'|Diploma\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|Higher\s+Certificate\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|Advanced\s+Diploma\s+(?:in|of)\s+[A-Z][\w\s,&\-\(\)\.:]{2,80}'
    r'|PGCE[\w\s,&\-\(\)\.:]{0,40}'
    r')'
)

# Header text that locates programme-group columns within a row
QUAL_HEADER_RE = re.compile(r'qualification', re.IGNORECASE)
CAREER_HEADER_RE = re.compile(r'career', re.IGNORECASE)


# ════════════════════════════════════════════════════════════════
# HTTP
# ════════════════════════════════════════════════════════════════

def fetch_pdf_bytes(url: str = NMU_ZCARD_URL, timeout: int = 60) -> bytes:
    logger.info(f'Downloading NMU Z-Card from {url}')
    r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=timeout)
    r.raise_for_status()
    if r.content[:4] != b'%PDF':
        raise RuntimeError('NMU Z-Card URL did not return a PDF')
    return r.content


# ════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════

def _clean(text: str) -> str:
    if not text:
        return ''
    return re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()


def _split_pipe(cell: str) -> list[str]:
    """Split a pipe/newline-separated cell into trimmed parts (preserve order)."""
    if not cell:
        return []
    parts = [p.strip() for p in re.split(r'[|\n]', cell)]
    return [p for p in parts if p]


def _find_qualification_columns(header_row: list[str]) -> list[int]:
    """Find every column index whose header is 'Qualification'."""
    cols = []
    for i, cell in enumerate(header_row or []):
        if cell and QUAL_HEADER_RE.search(_clean(cell)):
            cols.append(i)
    return cols


def _find_career_columns(header_row: list[str]) -> list[int]:
    """Find every column index whose header is 'Career/study field'."""
    cols = []
    for i, cell in enumerate(header_row or []):
        if cell and CAREER_HEADER_RE.search(_clean(cell)) and 'study' in _clean(cell).lower():
            cols.append(i)
    return cols


def _nmu_as_to_aps(as_value: int) -> int:
    """
    Convert NMU 'Applicant Score' (typically 200-450) to a standard SA APS (18-45).

    NMU AS is computed differently from APS — it's a weighted percentage system.
    Roughly:  APS ≈ (AS - 200) / 10 + 18, capped at 45.

    Empirical mapping from real NMU programmes:
        AS 410 → APS ≈ 39  (top engineering / accounting)
        AS 370 → APS ≈ 35  (engineering tech)
        AS 350 → APS ≈ 33  (BVA, BA)
        AS 330 → APS ≈ 31  (advertising, BCom)
        AS 290 → APS ≈ 27  (lower-bar)
    """
    if not as_value or as_value < 100:
        return 0
    aps = round((as_value - 200) / 10 + 18)
    return max(18, min(45, aps))


def _parse_aps_list(cell: str) -> list[int]:
    """Convert '410|390|370|-|-|350|290' to APS values [39,37,35,0,0,33,27]."""
    out = []
    for piece in _split_pipe(cell or ''):
        m = re.search(r'\d+', piece)
        if m:
            try:
                raw = int(m.group())
                if 100 <= raw <= 600:
                    out.append(_nmu_as_to_aps(raw))
                else:
                    out.append(0)
            except ValueError:
                out.append(0)
        else:
            out.append(0)
    return out


def _parse_subjects_text(text: str) -> list[dict]:
    """Extract subject + percentage requirements from NMU's subject text."""
    if not text:
        return []
    seen = set()
    out = []
    blob = text.replace('\n', ' ')
    # NMU writes like "Mathematics – 60%" / "Physical Sciences – 50%"
    for m in re.finditer(
        r'(Mathematics(?:\s+Literacy)?|Maths(?:\s+Lit)?|'
        r'Engl?(?:ish)?(?:\s+(?:HL|FAL))?|'
        r'Phys(?:ical)?\s+Sci(?:ence)?s?|'
        r'Life\s+Sci(?:ence)?s?|'
        r'Geography|History|Accounting|Economics|'
        r'Technical\s+Maths|Technical\s+Sciences?|'
        r'isiXhosa|Afrikaans|Agric(?:ultural)?\s+Sci(?:ence)?s?)'
        r'\s*[–\-:]?\s*(\d{2,3})\s*%',
        blob, re.IGNORECASE,
    ):
        subj_raw = m.group(1)
        try:
            pct = int(m.group(2))
        except ValueError:
            continue
        # % → NSC level
        if pct >= 80:   level = 7
        elif pct >= 70: level = 6
        elif pct >= 60: level = 5
        elif pct >= 50: level = 4
        elif pct >= 40: level = 3
        elif pct >= 30: level = 2
        else:           level = 1

        subj = re.sub(r'\s+', ' ', subj_raw.strip())
        # Normalise common variants
        subj_lower = subj.lower()
        if subj_lower in ('engl', 'english'):
            subj = 'English'
        elif subj_lower.startswith('phys'):
            subj = 'Physical Sciences'
        elif subj_lower.startswith('life sci'):
            subj = 'Life Sciences'
        elif subj_lower.startswith('maths lit') or subj_lower == 'mathematics literacy':
            subj = 'Mathematical Literacy'
        elif subj_lower in ('maths', 'math', 'mathematics'):
            subj = 'Mathematics'
        elif subj_lower.startswith('agric'):
            subj = 'Agricultural Sciences'
        else:
            subj = subj.title()

        if subj.lower() in seen:
            continue
        seen.add(subj.lower())
        out.append({'subject': subj, 'min_level': level})
    return out


# ════════════════════════════════════════════════════════════════
# Programme-group extraction
# ════════════════════════════════════════════════════════════════

def _extract_group(row: list[str], qual_col: int) -> list[ParsedCourse]:
    """
    Given a row and the column index of a 'Qualification' header,
    extract one or more ParsedCourses from this programme group.

    Surrounding columns (relative to qual_col):
      qual_col - 1   → Career/study field
      qual_col + 1   → Faculty (often reversed/garbage — skip)
      qual_col + 2   → Delivery mode & Duration
      qual_col + 3   → AS Maths
      qual_col + 4   → AS Maths Lit
      qual_col + 5   → AS Tech Maths
      qual_col + 6   → Subject(s) and % Required
    """
    if qual_col < 0 or qual_col >= len(row):
        return []

    qual_cell = row[qual_col] or ''
    qual_names = _split_pipe(qual_cell)
    if not qual_names:
        return []

    # Filter to only entries that actually look like programme names
    qual_names = [n for n in qual_names if QUAL_NAME_RE.match(n)]
    if not qual_names:
        return []

    def get(off: int) -> str:
        idx = qual_col + off
        return _clean(row[idx]) if 0 <= idx < len(row) else ''

    career = get(-1).split('|')[0].split('(')[0].strip()  # career field
    duration_text = get(2)
    aps_maths = _parse_aps_list(get(3))
    aps_maths_lit = _parse_aps_list(get(4))
    aps_tech = _parse_aps_list(get(5))
    subjects_text = get(6)

    # Best AS to use per programme: prefer Maths, fall back to MathsLit then TechMaths.
    # If still nothing for this index, fall back to the LOWEST non-zero APS in the
    # cell (representing a more lenient route into the same programme).
    def aps_for(idx: int) -> int:
        for arr in (aps_maths, aps_maths_lit, aps_tech):
            if idx < len(arr) and arr[idx] > 0:
                return arr[idx]
        # Fallback: lowest non-zero APS across all three columns
        all_vals = [v for arr in (aps_maths, aps_maths_lit, aps_tech) for v in arr if v > 0]
        return min(all_vals) if all_vals else 0

    subjects = _parse_subjects_text(subjects_text)

    # Try to split duration too — "Full-time 3 years|Part-time 5 years"
    durations = _split_pipe(duration_text)

    courses: list[ParsedCourse] = []
    for i, name in enumerate(qual_names):
        course = ParsedCourse(
            name=name[:300],
            institution_short_name='NMU',
            campus='Gqeberha (South / North)',
            source_excerpt=f'NMU | {career or "—"}',
        )
        course.field = classify_field(name + ' ' + career)
        course.level = classify_level(name)

        # AS / APS — NMU uses Applicant Score; we treat it as APS for now
        course.min_aps = aps_for(i)

        # Duration — pick i-th if multiple, else first
        d_text = durations[i] if i < len(durations) else (durations[0] if durations else '')
        m = re.search(r'(\d+(?:[.,]\d+)?)\s*year', d_text or '', re.IGNORECASE)
        if m:
            try:
                course.duration_years = float(m.group(1).replace(',', '.'))
            except ValueError:
                pass
        if not course.duration_years:
            DEFAULTS = {
                'certificate': 1.0, 'diploma': 3.0, 'advanced_diploma': 1.0,
                'degree': 3.0, 'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
            }
            course.duration_years = DEFAULTS.get(course.level, 3.0)

        course.subject_requirements = list(subjects)
        course.description = (
            f'Undergraduate qualification at Nelson Mandela University'
            f'{" — " + career if career else ""}.'
        )
        courses.append(course)

    return courses


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_nmu(institution_short_name: str = 'NMU') -> list[ParsedCourse]:
    """Download the NMU Z-Card and extract every programme."""
    pdf_bytes = fetch_pdf_bytes()
    logger.info(f'Downloaded {len(pdf_bytes):,} bytes')

    all_courses: list[ParsedCourse] = []
    seen_keys: set[tuple[str, str]] = set()  # (name, career) dedupe

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pn, page in enumerate(pdf.pages):
            try:
                tables = page.extract_tables()
            except Exception as e:
                logger.warning(f'  Page {pn+1} table extract failed: {e}')
                continue

            for ti, table in enumerate(tables):
                if not table or len(table) < 3:
                    continue

                # Find header row (the one with 'Qualification' columns)
                header_idx = -1
                for ri in range(min(5, len(table))):
                    qual_cols = _find_qualification_columns(table[ri])
                    if qual_cols:
                        header_idx = ri
                        break
                if header_idx < 0:
                    continue

                qual_cols = _find_qualification_columns(table[header_idx])
                logger.info(
                    f'  Page {pn+1} Table {ti+1}: header at row {header_idx}, '
                    f'{len(qual_cols)} qualification columns'
                )

                for row in table[header_idx + 1:]:
                    if not row:
                        continue
                    for qc in qual_cols:
                        for course in _extract_group(row, qc):
                            key = (course.name.lower().strip(), course.source_excerpt)
                            if key in seen_keys:
                                continue
                            seen_keys.add(key)
                            course.institution_short_name = institution_short_name
                            all_courses.append(course)

    logger.info(f'Parsed {len(all_courses)} NMU programmes')
    return all_courses


def parse_nmu_url(start_url: str = '', institution_short_name: str = 'NMU') -> list[ParsedCourse]:
    """Public entry-point matching the dispatcher signature."""
    return parse_nmu(institution_short_name)
