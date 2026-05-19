"""
Tshwane University of Technology (TUT) undergraduate programme scraper.

Source: https://www.tut.ac.za — faculty prospectus PDFs (Part 2–8)

Strategy:
  Download each faculty prospectus PDF, extract text with pdfplumber, split
  into qualification sections, parse APS / subjects / campus / level from the
  NSC-2008 admission block within each section.

Campuses: Arcadia, Arts Campus, Emalahleni, Ga-Rankuwa, Mbombela,
          Polokwane, Pretoria West, Soshanguve.
"""
import io
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup  # noqa: F401 (imported for consistency with other parsers)

try:
    import pdfplumber
except ImportError:
    pdfplumber = None  # type: ignore

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.tut.ac.za'
PDF_BASE  = f'{BASE_URL}/media/tshwane-interim/site-content/images/prospectus/'

# Faculty name → (PDF filename, default campus if none extracted)
FACULTY_PDFS = {
    'Arts and Design':                   ('Part2_Arts-and-Design_Prospectus.pdf',          'Arts Campus'),
    'Economics and Finance':             ('Part3_Economics-and-Finance_Prospectus.pdf',    'Ga-Rankuwa'),
    'Engineering and Built Environment': ('Part4_FEBE_Prospectus.pdf',                    'Arcadia'),
    'Humanities':                        ('PART_5_Humanities_Prospectus_-2026.pdf',        'Soshanguve'),
    'ICT':                               ('Part6_ICT_Prospectus.pdf',                      'Arcadia'),
    'Management Sciences':               ('Part7_Management-Sciences_Prospectus.pdf',      'Soshanguve'),
    'Science':                           ('Part8_Science.pdf',                             'Arcadia'),
}

# Qualification keywords → (level slug, default duration yrs)
LEVEL_MAP = [
    (re.compile(r'\bHIGHER\s+CERTIFICATE\b'),  'certificate',        1.0),
    (re.compile(r'\bADVANCED\s+DIPLOMA\b'),    'advanced_diploma',   1.0),
    (re.compile(r'\bDIPLOMA\b'),               'diploma',            3.0),
    (re.compile(r'\bBACHELOR\b'),              'degree',             4.0),
    (re.compile(r'\bBENGTECH\b|\bBENG\b|\bBTECH\b|\bBSC\b|\bBCOM\b|\bBACHELOR\b'), 'degree', 4.0),
]

# Qualifications to EXCLUDE (postgraduate / research-only)
EXCLUDE_RE = re.compile(
    r'\b(POSTGRADUATE|POST-GRADUATE|MASTER|MAGISTER|DOCTOR|HONOURS|PHD|HONS)\b',
    re.IGNORECASE,
)

CAMPUS_ALIASES: dict[str, str] = {
    'arcadia':       'Arcadia',
    'arts':          'Arts Campus',
    'emalahleni':    'Emalahleni',
    'witbank':       'Emalahleni',
    'ga-rankuwa':    'Ga-Rankuwa',
    'ga rankuwa':    'Ga-Rankuwa',
    'garankuwa':     'Ga-Rankuwa',
    'mbombela':      'Mbombela',
    'nelspruit':     'Mbombela',
    'polokwane':     'Polokwane',
    'pretoria west': 'Pretoria West',
    'pretoria':      'Arcadia',
    'soshanguve':    'Soshanguve',
}

# APS inside the NSC-2008 block
APS_RE = re.compile(
    r'(?:Admission\s+Point\s+Score|APS)\b[^.]{0,80}?(?:of\s+at\s+least\s*|=\s*)(\d{2})',
    re.IGNORECASE | re.DOTALL,
)

# "achievement level of at least N for SUBJECT ..."
# Then continuation "N for SUBJECT" pairs
SUBJ_SEED_RE = re.compile(
    r'achievement\s+level\s+of\s+at\s+least\s+(\d)\s+for\s+'
    r'((?:Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|'
    r'Physical\s+Science[s]?|Technical\s+Science[s]?|'
    r'Life\s+Science[s]?|English|Afrikaans|'
    r'Accounting|Economics|Business\s+Studies|Geography|History|'
    r'Technical\s+Mathematics|'
    r'Information\s+Technology|Computer\s+Applications\s+Technology)'
    r'[a-zA-Z\s()]*?)'
    r'(?=\s*(?:and\s+\d|\,\s*\d|\.|$|\n))',
    re.IGNORECASE,
)
SUBJ_CONT_RE = re.compile(
    r'(?:,|and)\s+(\d)\s+for\s+'
    r'((?:Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|'
    r'Physical\s+Science[s]?|Technical\s+Science[s]?|'
    r'Life\s+Science[s]?|English|Afrikaans|'
    r'Accounting|Economics|Business\s+Studies|Geography|History|'
    r'Technical\s+Mathematics|'
    r'Information\s+Technology|Computer\s+Applications\s+Technology)'
    r'[a-zA-Z\s()]*?)'
    r'(?=\s*(?:and\s+\d|\,\s*\d|\.|$|\n|or\s+\d))',
    re.IGNORECASE,
)

DURATION_WORD = {'one': 1.0, 'two': 2.0, 'three': 3.0, 'four': 4.0, 'five': 5.0}


# ── helpers ───────────────────────────────────────────────────────────────────

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _fetch_pdf_bytes(url: str, session: requests.Session) -> Optional[bytes]:
    try:
        r = session.get(url, timeout=60)
        if r.status_code == 200 and b'%PDF' in r.content[:8]:
            return r.content
    except Exception as e:
        logger.debug(f'PDF fetch error {url}: {e}')
    return None


def _pdf_text(data: bytes) -> str:
    """Extract full text from PDF bytes using pdfplumber."""
    if pdfplumber is None:
        logger.error('pdfplumber not installed — cannot parse TUT PDFs')
        return ''
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return '\n'.join(pages)


def _parse_campuses(raw: str) -> list[str]:
    """'Ga-Rankuwa, Mbombela and Polokwane campuses' → ['Ga-Rankuwa','Mbombela','Polokwane']"""
    raw_l = raw.lower()
    found = []
    # longest-match first
    for alias in sorted(CAMPUS_ALIASES, key=len, reverse=True):
        if alias in raw_l:
            canonical = CAMPUS_ALIASES[alias]
            if canonical not in found:
                found.append(canonical)
    return found or ['Arcadia']


def _nsc_block(section_text: str) -> str:
    """Extract the NSC 2008+ admission block from a section."""
    marker = re.search(
        r'NATIONAL SENIOR CERTIFICATE(?:\s+OBTAINED)?\s+IN\s+OR\s+AFTER\s+2008',
        section_text, re.IGNORECASE,
    )
    if not marker:
        return section_text
    start = marker.start()
    # End at next major bullet or sub-section label (b., c., •)
    end_m = re.search(
        r'\n\s*(?:b\.|c\.|•\s+FOR\s+APPLICANTS\s+WITH)',
        section_text[start:], re.IGNORECASE,
    )
    end = start + end_m.start() if end_m else start + 2000
    return section_text[start:end]


def _extract_aps(text: str) -> int:
    """Return first plausible APS found in text (15–45)."""
    for m in APS_RE.finditer(text):
        try:
            v = int(m.group(1))
            if 15 <= v <= 45:
                return v
        except ValueError:
            pass
    return 0


def _extract_subjects(text: str) -> list[dict]:
    """Parse 'achievement level of at least N for SUBJECT ...' chains."""
    # Normalise line-breaks to spaces for regex matching
    flat = re.sub(r'\s+', ' ', text)
    subjects: list[dict] = []
    seen: set[str] = set()

    def _add(lvl_str: str, raw_subj: str) -> None:
        try:
            lvl = int(lvl_str)
        except ValueError:
            return
        if not (1 <= lvl <= 7):
            return
        subj = re.sub(r'\s+', ' ', raw_subj).strip().title()
        # Drop parenthetical qualifier e.g. "(home language or first additional language)"
        subj = re.sub(r'\s*\([^)]+\)', '', subj).strip()
        # Normalise common variants
        subj = re.sub(r'Physical Sciences?', 'Physical Sciences', subj, flags=re.I)
        subj = re.sub(r'Life Sciences?', 'Life Sciences', subj, flags=re.I)
        key = subj.lower()
        if key not in seen and len(subj) > 2:
            seen.add(key)
            subjects.append({'subject': subj, 'min_level': lvl})

    for m in SUBJ_SEED_RE.finditer(flat):
        _add(m.group(1), m.group(2))
        # Also scan forward from match end for continuation pairs
        tail = flat[m.end():m.end() + 300]
        for cm in SUBJ_CONT_RE.finditer(tail):
            _add(cm.group(1), cm.group(2))
        break  # only use first "achievement level" sentence

    return subjects


def _qualify_level_duration(name_upper: str, nqf: int) -> tuple[str, float]:
    """Derive (level_slug, duration_years) from qualification name and NQF level."""
    if 'HIGHER CERTIFICATE' in name_upper:
        return 'certificate', 1.0
    if 'ADVANCED DIPLOMA' in name_upper:
        return 'advanced_diploma', 1.0
    if 'DIPLOMA' in name_upper:
        return 'diploma', 3.0
    if any(k in name_upper for k in ('BACHELOR', 'BENGTECH', 'BTECH', 'BENGTECH')):
        # Architecture is 5yr; most others 4yr
        if 'ARCHITECTURE' in name_upper:
            return 'degree', 5.0
        return 'degree', 4.0
    # Fallback by NQF
    if nqf <= 5:
        return 'certificate', 1.0
    if nqf == 6:
        return 'diploma', 3.0
    return 'degree', 4.0


# ── section parser ─────────────────────────────────────────────────────────────

def _parse_faculty_text(text: str, faculty_name: str,
                        default_campus: str) -> list[ParsedCourse]:
    """Split full faculty PDF text into qualification sections and parse each."""
    courses: list[ParsedCourse] = []

    # Split on section boundaries: newline followed by "N.N UPPERCASE..."
    # Use lookahead so the delimiter stays part of each section
    raw_sections = re.split(r'\n(?=\d+\.\d+\s+[A-Z])', text)

    for raw in raw_sections:
        raw = raw.strip()
        if not raw:
            continue

        # ── 1. Extract qualification name from header lines ──────────────────
        lines = raw.split('\n')
        header_match = re.match(r'^(\d+\.\d+)\s+(.+)$', lines[0])
        if not header_match:
            continue

        sec_num  = header_match.group(1)
        name_part = header_match.group(2).strip()

        # Skip TOC entries (they have dot-leaders like "..............61")
        if re.search(r'\.{4,}', name_part) or re.search(r'\s{2,}\d+$', name_part):
            continue

        # Collect continuation ALL-CAPS lines (multi-line header names)
        for extra_line in lines[1:4]:
            extra = extra_line.strip()
            if extra and extra == extra.upper() and len(extra) > 1 and not re.match(r'^[A-Z][a-z]', extra):
                name_part = name_part + ' ' + extra
            else:
                break

        name_upper = re.sub(r'\s+', ' ', name_part).strip().upper()

        # ── 2. Filter: skip postgrad / research programmes ───────────────────
        if EXCLUDE_RE.search(name_upper):
            continue

        # Must start with a recognised entry-level qualification keyword
        if not re.match(
            r'^(HIGHER\s+CERTIFICATE|ADVANCED\s+DIPLOMA|DIPLOMA|BACHELOR|'
            r'BACCALAUREUS|BENGTECH|BTECH|BSC|BCOM|BA\b)',
            name_upper,
        ):
            continue

        # ── 3. NQF level and programme code ─────────────────────────────────
        nqf = 6  # default
        nqf_m = re.search(r'NQF\s+Level\s+(\d)', raw, re.IGNORECASE)
        if nqf_m:
            nqf = int(nqf_m.group(1))

        prog_code = ''
        code_m = re.search(r'Qualification\s+code:\s*([A-Z0-9]+)', raw, re.IGNORECASE)
        if code_m:
            prog_code = code_m.group(1)

        # ── 4. Level and duration ────────────────────────────────────────────
        level_str, duration = _qualify_level_duration(name_upper, nqf)
        # Override from "Minimum duration: N year(s)"
        dur_m = re.search(r'Minimum\s+duration[:\s]+(\w+)\s+year', raw, re.IGNORECASE)
        if dur_m:
            duration = DURATION_WORD.get(dur_m.group(1).lower(), duration)

        # ── 5. Campus(es) ────────────────────────────────────────────────────
        camp_m = re.search(r'Campus(?:es)?\s+where\s+offered:\s*([^\n]+)', raw, re.IGNORECASE)
        if camp_m:
            campuses = _parse_campuses(camp_m.group(1))
        else:
            campuses = [default_campus]

        # ── 6. APS — prefer NSC-2008 block ──────────────────────────────────
        nsc_text = _nsc_block(raw)
        aps = _extract_aps(nsc_text) or _extract_aps(raw)

        # ── 7. Subjects ──────────────────────────────────────────────────────
        subjects = _extract_subjects(nsc_text)

        # ── 8. Display name (Title Case) ─────────────────────────────────────
        name = name_upper.title()
        # Fix common shorthands that title() mangles
        name = re.sub(r'\bIn\b', 'in', name)
        name = re.sub(r'\bOf\b', 'of', name)
        name = re.sub(r'\bAnd\b', 'and', name)
        name = re.sub(r'\bThe\b', 'the', name)
        name = re.sub(r'\bFor\b', 'for', name)
        # Fix "Bengtech" → "BEngTech", "Btech" → "BTech"
        name = re.sub(r'\bBengtech\b', 'BEngTech', name, flags=re.IGNORECASE)
        name = re.sub(r'\bBtech\b', 'BTech', name, flags=re.IGNORECASE)
        # Remove stray asterisks and trailing punctuation
        name = re.sub(r'\*', '', name).strip(' *:,')
        # Capitalise first word always
        if name:
            name = name[0].upper() + name[1:]
        if len(name) < 6:
            continue

        field = classify_field(name + ' ' + faculty_name)

        # ── 9. Emit one ParsedCourse per campus ──────────────────────────────
        for campus in campuses:
            courses.append(ParsedCourse(
                name=name,
                field=field,
                level=level_str,
                duration_years=duration,
                min_aps=aps,
                campus=campus,
                subject_requirements=subjects,
                programme_code=prog_code,
                institution_short_name='TUT',
                source_excerpt=f'Faculty: {faculty_name} | Code: {prog_code}',
            ))

    return courses


# ── APS floor fallback ─────────────────────────────────────────────────────────

def _aps_floor(name: str, level: str) -> int:
    n = name.lower()
    if level == 'certificate':
        return 18
    if level == 'advanced_diploma':
        return 0   # requires prior diploma — no NSC APS
    if level == 'diploma':
        if any(k in n for k in ['engineering', 'nursing', 'radiograph']):
            return 20
        return 18
    if level == 'degree':
        if any(k in n for k in ['engineering technology', 'architecture', 'nursing']):
            return 28
        return 24
    return 20


# ── main entry point ───────────────────────────────────────────────────────────

def parse_tut() -> list[ParsedCourse]:
    """Scrape all TUT undergraduate programmes from faculty prospectus PDFs."""
    session = _session()
    all_courses: list[ParsedCourse] = []
    seen_keys: set = set()

    for faculty_name, (pdf_name, default_campus) in FACULTY_PDFS.items():
        url = PDF_BASE + pdf_name
        logger.info(f'Fetching {faculty_name} PDF: {url}')
        data = _fetch_pdf_bytes(url, session)
        if not data:
            logger.warning(f'  Failed to fetch {pdf_name}')
            continue

        text = _pdf_text(data)
        if not text:
            logger.warning(f'  No text extracted from {pdf_name}')
            continue

        faculty_courses = _parse_faculty_text(text, faculty_name, default_campus)
        logger.info(f'  {faculty_name}: {len(faculty_courses)} entries parsed')

        for c in faculty_courses:
            # Dedup: same name + level + campus
            key = (c.name.lower().strip(), c.level, c.campus)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            # APS floor if none extracted (Advanced Diplomas skip)
            if not c.min_aps and c.level != 'advanced_diploma':
                c.min_aps = _aps_floor(c.name, c.level)

            # Subjects fallback
            if not c.subject_requirements:
                from apps.courses.defaults import default_subjects_for
                c.subject_requirements = default_subjects_for(c.field, c.level)

            all_courses.append(c)

    logger.info(f'TUT total: {len(all_courses)} programmes')
    return all_courses


def parse_tut_url(url: str, institution_short_name: str = 'TUT') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_tut()
