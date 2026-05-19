"""
CPUT (Cape Peninsula University of Technology) undergraduate programme scraper.

Source: https://prospectus.cput.ac.za

Strategy:
  Pass 1 — Fetch each faculty listing page, extract programme codes + names.
  Pass 2 — Fetch each programme detail page, extract APS, subject requirements, campus.

Campuses: Bellville, District Six, Mowbray, Granger Bay, Wellington, Tygerberg, Symphony Way.
"""
import re
import logging
from typing import Optional

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

PROSPECTUS_BASE = 'https://prospectus.cput.ac.za'
LISTING_URL  = f'{PROSPECTUS_BASE}/index.php/link-to-courses?f={{fid}}'
DETAIL_URL   = f'{PROSPECTUS_BASE}/index.php/course-details?q={{code}}&f={{fid}}'

FACULTIES = {
    'Applied Sciences':               20,
    'Business and Management Sciences': 60,
    'Education':                      100,
    'Engineering and Built Environment': 140,
    'Health and Wellness Sciences':   180,
    'Informatics and Design':         220,
}

# Code prefix → (qualification level string, duration in years)
CODE_PREFIX_MAP = {
    'D3': ('diploma', 3.0),
    'DP': ('diploma', 3.0),
    'D2': ('diploma', 2.0),
    'AD': ('advanced_diploma', 1.0),
    'HC': ('certificate', 1.0),
    'PG': ('certificate', 1.0),
    'BP': ('degree', 4.0),
    'BG': ('degree', 3.0),
    'BH': ('degree', 4.0),
    'BE': ('degree', 4.0),
    'PD': ('honours', 1.0),
    'MG': ('masters', 2.0),
    'MD': ('masters', 2.0),
    'DG': ('phd', 3.0),
}

CAMPUS_ALIASES = {
    'bellville':      'Bellville',
    'district six':   'District Six',
    'district':       'District Six',
    'mowbray':        'Mowbray',
    'granger bay':    'Granger Bay',
    'granger':        'Granger Bay',
    'wellington':     'Wellington',
    'tygerberg':      'Tygerberg',
    'symphony':       'Bellville',
    'cape town':      'District Six',
}

APS_PATTERN = re.compile(
    r'(?:APS\s*(?:score|Score)?\s*(?:of\s*|=\s*)?(\d{2}))'
    r'|(?:minimum\s+(?:of\s+)?(\d{2})\s+(?:with|on\s+the\s+APS|APS))'
    r'|(?:score\s+a\s+minimum\s+of\s+(\d{2}))',
    re.IGNORECASE,
)

SUBJECT_LEVEL_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English(?:\s+(?:Home\s+Language|First\s+Additional\s+Language|HL|FAL))?|'
    r'Afrikaans|Accounting|Economics|Business\s+Studies|Geography|History|'
    r'Technical\s+Mathematics|Technical\s+Science[s]?|'
    r'Information\s+Technology|Computer\s+Applications\s+Technology)'
    r'[^.\n]{0,40}?\(?(\d)\)?(?:\s*\(\d+%\))?',
    re.IGNORECASE,
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    # prospectus.cput.ac.za has an untrusted intermediate cert — disable SSL verify
    s.verify = False
    return s


def _fetch(url: str, session: requests.Session, timeout: int = 20) -> Optional[BeautifulSoup]:
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        logger.debug(f'Fetch error {url}: {e}')
    return None


def _scrape_listing(faculty_name: str, fid: int,
                    session: requests.Session) -> list[tuple[str, str, bool]]:
    """
    Fetch faculty listing page.
    Returns list of (code, display_name, is_ecp) tuples.
    """
    url = LISTING_URL.format(fid=fid)
    soup = _fetch(url, session)
    if not soup:
        return []

    programmes = []
    seen_codes = set()

    # Programme links: <a href="/index.php/course-details?q=CODE&f=N">
    for a in soup.find_all('a', href=re.compile(r'course-details\?q=')):
        href = a.get('href', '')
        code_m = re.search(r'q=([A-Z0-9]+)', href)
        if not code_m:
            continue
        code = code_m.group(1)
        if code in seen_codes:
            continue
        seen_codes.add(code)

        raw_text = a.get_text(' ', strip=True)
        # Remove the [CODE] suffix from display name
        name = re.sub(r'\s*\[' + re.escape(code) + r'\]\s*', '', raw_text).strip()
        name = re.sub(r'\s+', ' ', name).title()
        name = re.sub(r'\s*\(Extended Curriculum Pr.*?\)', '', name, flags=re.IGNORECASE).strip()
        is_ecp = 'extended' in raw_text.lower() or code.endswith('X')

        if len(name) > 4:
            programmes.append((code, name, is_ecp))

    logger.info(f'  {faculty_name}: {len(programmes)} programmes listed')
    return programmes


def _scrape_detail(code: str, fid: int, name: str, faculty_name: str,
                   session: requests.Session) -> ParsedCourse:
    """Fetch programme detail page and extract APS, subjects, campus."""
    url = DETAIL_URL.format(code=code, fid=fid)
    soup = _fetch(url, session, timeout=15)

    # Defaults from code prefix
    prefix = code[:2]
    level_str, duration = CODE_PREFIX_MAP.get(prefix, ('degree', 3.0))
    # Override by name
    level_from_name = classify_level(name)
    if level_from_name != 'degree':
        level_str = level_from_name

    campus = 'Bellville'
    aps = 0
    subjects = []

    if soup:
        content = soup.find('div', class_='col-md-8')
        if not content:
            content = soup

        text = content.get_text('\n', strip=True)

        # APS
        for m in APS_PATTERN.finditer(text):
            val = m.group(1) or m.group(2) or m.group(3)
            if val:
                try:
                    v = int(val)
                    if 15 <= v <= 45:
                        aps = v
                        break
                except ValueError:
                    pass

        # Subject requirements — only from admission section
        adm_idx = text.lower().find('admission requirements')
        syl_idx = text.lower().find('syllabus')
        if adm_idx >= 0:
            adm_end = syl_idx if syl_idx > adm_idx else adm_idx + 1500
            adm_block = text[adm_idx:adm_end]
        else:
            adm_block = text[:2000]

        seen_s = set()
        for sm in SUBJECT_LEVEL_PATTERN.finditer(adm_block):
            subj = re.sub(r'\s+', ' ', sm.group(1)).strip().title()
            try:
                lvl = int(sm.group(2))
            except ValueError:
                continue
            if not (1 <= lvl <= 7) or subj.lower() in seen_s:
                continue
            seen_s.add(subj.lower())
            subjects.append({'subject': subj, 'min_level': lvl})

        # Campus — "Offering type: FULL-TIME WELLINGTON"
        camp_m = re.search(r'Offering\s+type[:\s]+(?:FULL.?TIME|PART.?TIME)\s+([A-Z\s]+)',
                           text, re.IGNORECASE)
        if camp_m:
            raw_campus = camp_m.group(1).strip().lower()
            for alias, canonical in CAMPUS_ALIASES.items():
                if alias in raw_campus:
                    campus = canonical
                    break
            else:
                campus = camp_m.group(1).strip().title()

        # Duration override from name or code
        dur_m = re.search(r'\b(\d)\s*-?\s*(?:year|yr)', name, re.I)
        if dur_m:
            duration = float(dur_m.group(1))

    field = classify_field(name + ' ' + faculty_name)

    return ParsedCourse(
        name=name,
        field=field,
        level=level_str,
        duration_years=duration,
        min_aps=aps,
        campus=campus,
        subject_requirements=subjects,
        programme_code=code,
        institution_short_name='CPUT',
        source_excerpt=f'Faculty: {faculty_name} | Code: {code}',
    )


def _is_undergrad(code: str) -> bool:
    """Filter to undergraduate qualifications only."""
    prefix = code[:2].upper()
    # Exclude postgrad: MG/MD/DG/PD (masters/doctorate/postgrad diploma)
    return prefix not in ('MG', 'MD', 'DG')


def parse_cput() -> list[ParsedCourse]:
    """Main entry point — scrape all CPUT undergraduate programmes."""
    session = _session()
    all_courses: list[ParsedCourse] = []
    seen_keys: set = set()

    for faculty_name, fid in FACULTIES.items():
        programmes = _scrape_listing(faculty_name, fid, session)

        for code, name, is_ecp in programmes:
            # Skip postgrad and ECP variants (they share admission with main)
            if not _is_undergrad(code):
                continue
            if is_ecp and not name.lower().startswith('higher'):
                # Include ECP only if it's a distinct Higher Certificate
                continue

            key = (name.lower().strip(), code[:2])  # dedup by name + qualification tier
            if key in seen_keys:
                continue
            seen_keys.add(key)

            course = _scrape_detail(code, fid, name, faculty_name, session)

            # Apply APS floor if nothing extracted
            if not course.min_aps:
                course.min_aps = _aps_floor(name, faculty_name, code)

            # Apply default subjects if none found
            if not course.subject_requirements:
                from apps.courses.defaults import default_subjects_for
                course.subject_requirements = default_subjects_for(course.field, course.level)

            all_courses.append(course)

    logger.info(f'CPUT total: {len(all_courses)} programmes')
    return all_courses


def _aps_floor(name: str, faculty: str, code: str) -> int:
    """Reasonable APS floor when detail page yields nothing."""
    name_l = name.lower()
    prefix = code[:2].upper()
    if prefix in ('BP', 'BH', 'BE'):
        # Professional bachelor degrees
        if any(k in name_l for k in ['engineering', 'marine', 'nautical']):
            return 28
        if any(k in name_l for k in ['nursing', 'emergency', 'radiograph', 'nuclear',
                                       'ultrasound', 'radiation', 'medical lab']):
            return 28
        return 26
    if prefix == 'BG':
        return 24
    if prefix in ('D3', 'DP', 'D2'):
        if 'engineering' in faculty.lower():
            return 18
        return 18
    if prefix == 'HC':
        return 16
    return 20


def parse_cput_url(url: str, institution_short_name: str = 'CPUT') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_cput()
