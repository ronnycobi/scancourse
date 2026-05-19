"""
NWU (North-West University) undergraduate programme scraper.

Source: https://studies.nwu.ac.za/undergraduate-studies/fields-study
Structure:
  - Index page lists 8 faculty cards → each card links to a faculty page
  - Each faculty page has <table> rows: Degree | Field | Subjects | APS | Campus
  - Programmes offered on 3 campuses: Potchefstroom (P), Mahikeng (M), Vanderbijlpark (V)
"""
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

INDEX_URL = 'https://studies.nwu.ac.za/undergraduate-studies/fields-study'

CAMPUS_ABBREVIATIONS = {
    'potchefstroom': 'Potchefstroom',
    'potch':         'Potchefstroom',
    'mahikeng':      'Mahikeng',
    'mafikeng':      'Mahikeng',
    'vanderbijlpark':'Vanderbijlpark',
    'vaal':          'Vanderbijlpark',
    'all campuses':  'Potchefstroom',   # default to main campus
    'distance':      'Distance',
}

SUBJECT_LEVEL_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English(?:\s+(?:HL|FAL|Home|First))?|'
    r'Afrikaans(?:\s+(?:HL|FAL|Home|First))?|'
    r'Accounting|Economics|Business\s+Studies|Geography|History|'
    r'Information\s+Technology|Computer\s+Applications\s+Technology|'
    r'Language\s+of\s+(?:tuition|instruction)|Home\s+Language|'
    r'NSC\s+subject|Any\s+subject|Language)'
    r'[\s:,;-]*(?:Level\s+)?(\d)\b',
    re.IGNORECASE,
)

# Also match percentage thresholds: "Mathematics 70%" or "Maths (70%)"
SUBJECT_PERCENT_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English|Afrikaans|Accounting|Economics|Business\s+Studies|'
    r'Geography|History|Information\s+Technology|Language\s+of\s+(?:tuition|instruction)|'
    r'Home\s+Language)\s*[\(:]?\s*(\d{2})\s*%',
    re.IGNORECASE,
)

PERCENT_TO_LEVEL = {
    range(80, 101): 7,
    range(70, 80):  6,
    range(60, 70):  5,
    range(50, 60):  4,
    range(40, 50):  3,
    range(30, 40):  2,
    range(0,  30):  1,
}


def _percent_to_nsc_level(pct: int) -> int:
    for r, lvl in PERCENT_TO_LEVEL.items():
        if pct in r:
            return lvl
    return 3


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _parse_campus_cell(text: str) -> list[str]:
    """Return list of campus names from the Campus column text."""
    if not text or not text.strip():
        return ['Potchefstroom']
    text_lower = text.lower()
    found = []
    if 'potchefstroom' in text_lower or 'potch' in text_lower:
        found.append('Potchefstroom')
    if 'mahikeng' in text_lower or 'mafikeng' in text_lower:
        found.append('Mahikeng')
    if 'vanderbijlpark' in text_lower or 'vaal' in text_lower:
        found.append('Vanderbijlpark')
    if 'distance' in text_lower:
        found.append('Distance')
    if not found:
        # Try comma-separated abbreviations: P, M, V
        parts = re.split(r'[,/\s]+', text.strip())
        for p in parts:
            p = p.strip().upper()
            if p == 'P':
                found.append('Potchefstroom')
            elif p == 'M':
                found.append('Mahikeng')
            elif p == 'V':
                found.append('Vanderbijlpark')
    return found or ['Potchefstroom']


def _parse_subjects(cell_text: str) -> list[dict]:
    """Extract subject requirements from the requirements column."""
    reqs = []
    seen = set()

    # Level format: "Mathematics Level 5"
    for m in SUBJECT_LEVEL_PATTERN.finditer(cell_text):
        subj = re.sub(r'\s+', ' ', m.group(1).strip()).title()
        try:
            level = int(m.group(2))
        except ValueError:
            continue
        if not (1 <= level <= 7):
            continue
        key = subj.lower()
        if key in seen:
            continue
        seen.add(key)
        reqs.append({'subject': subj, 'min_level': level})

    # Percentage format: "Mathematics 70%"
    if not reqs:
        for m in SUBJECT_PERCENT_PATTERN.finditer(cell_text):
            subj = re.sub(r'\s+', ' ', m.group(1).strip()).title()
            try:
                pct = int(m.group(2))
            except ValueError:
                continue
            level = _percent_to_nsc_level(pct)
            key = subj.lower()
            if key in seen:
                continue
            seen.add(key)
            reqs.append({'subject': subj, 'min_level': level})

    return reqs


def _clean_programme_name(degree: str, specialization: str) -> str:
    """Combine degree prefix with specialization into a full name."""
    degree = re.sub(r'\s+', ' ', (degree or '').strip())
    spec = re.sub(r'\s+', ' ', (specialization or '').strip())

    if not spec:
        return degree
    if not degree:
        return spec

    # If spec already starts with "in" or "of" it's a clean suffix
    if re.match(r'^(?:in|of|for)\b', spec, re.IGNORECASE):
        return f'{degree} {spec}'

    # If degree already contains a specialization, don't duplicate
    if degree.lower().endswith(spec.lower()):
        return degree

    return f'{degree}: {spec}'


def _parse_faculty_table(table, faculty_name: str) -> list[ParsedCourse]:
    """Parse a single <table> on an NWU faculty page."""
    courses = []
    rows = table.find_all('tr')
    if not rows:
        return courses

    # Detect header row to find column positions
    header_row = rows[0]
    headers = [th.get_text(' ', strip=True).lower() for th in header_row.find_all(['th', 'td'])]

    # Try to find column indices
    def _col(keywords):
        for i, h in enumerate(headers):
            if any(k in h for k in keywords):
                return i
        return None

    degree_col  = _col(['degree', 'qualification', 'programme'])
    field_col   = _col(['field', 'specialis', 'major', 'stream'])
    subj_col    = _col(['subject', 'requirement', 'nsc', 'entry'])
    aps_col     = _col(['aps', 'score', 'points'])
    campus_col  = _col(['campus', 'location', 'site'])

    # If we can't find a degree column try to detect from content
    if degree_col is None and headers:
        degree_col = 0  # assume first column

    data_rows = rows[1:]
    last_degree = ''  # carry forward if degree cell spans

    def _cell_tag(idx: Optional[int]) -> object:
        """Return the BeautifulSoup tag for a cell, or None."""
        return None  # placeholder — overridden per-row below

    def _cell_text_from_tag(tag) -> str:
        if tag is None:
            return ''
        return tag.get_text(' ', strip=True)

    def _cell_specializations(tag) -> list[str]:
        """
        If the cell contains a <ul><li> list, return each <li> as a separate
        specialization string. Otherwise return [cell_text].
        """
        if tag is None:
            return ['']
        ul = tag.find('ul')
        if ul:
            items = [li.get_text(' ', strip=True) for li in ul.find_all('li')]
            return [s for s in items if s.strip()] or ['']
        text = tag.get_text(' ', strip=True)
        return [text] if text.strip() else ['']

    for row in data_rows:
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue

        def get_tag(idx: Optional[int]):
            if idx is None or idx >= len(cells):
                return None
            return cells[idx]

        degree_tag  = get_tag(degree_col)
        field_tag   = get_tag(field_col)
        subj_tag    = get_tag(subj_col)
        aps_tag     = get_tag(aps_col)
        campus_tag  = get_tag(campus_col)

        degree_text = _cell_text_from_tag(degree_tag)
        if degree_text:
            last_degree = degree_text
        else:
            degree_text = last_degree

        subj_text  = _cell_text_from_tag(subj_tag)
        aps_text   = _cell_text_from_tag(aps_tag)
        campus_text= _cell_text_from_tag(campus_tag)

        # Field/specialization may contain a <ul> listing multiple specializations
        specializations = _cell_specializations(field_tag)

        # APS — extract once per row (shared across specializations)
        aps_val = 0
        aps_match = re.search(r'\b(\d{2})\b', aps_text)
        if aps_match:
            try:
                aps_val = int(aps_match.group(1))
                if not (15 <= aps_val <= 45):
                    aps_val = 0
            except ValueError:
                pass

        subjects = _parse_subjects(subj_text)
        campuses = _parse_campus_cell(campus_text)

        for spec_text in specializations:
            # Combine degree + specialization
            full_name = _clean_programme_name(degree_text, spec_text)
            if len(full_name) < 4:
                continue

            # Duration
            dur_match = re.search(r'\b(\d)\s*(?:-\s*)?(?:year|yr)s?\b', full_name + ' ' + subj_text, re.I)
            duration = float(dur_match.group(1)) if dur_match else None
            if duration is None:
                level_str_tmp = classify_level(full_name)
                if level_str_tmp == 'diploma':
                    duration = 3.0
                elif level_str_tmp == 'certificate':
                    duration = 1.0
                elif level_str_tmp == 'advanced_diploma':
                    duration = 1.0
                else:
                    duration = 4.0 if any(k in full_name.lower() for k in [
                        'engineering', 'mbchb', 'pharmacy', 'dentistry', 'llb'
                    ]) else 3.0

            level_str = classify_level(full_name)
            field_str = classify_field(full_name + ' ' + faculty_name)

            for campus in campuses:
                c = ParsedCourse(
                    name=full_name,
                    field=field_str,
                    level=level_str,
                    duration_years=duration,
                    min_aps=aps_val,
                    campus=campus,
                    subject_requirements=list(subjects),
                    institution_short_name='NWU',
                    source_excerpt=f'Faculty: {faculty_name} | Campus: {campus}',
                )
                courses.append(c)

    return courses


def _parse_faculty_page(url: str, faculty_name: str, session: requests.Session) -> list[ParsedCourse]:
    """Fetch and parse one NWU faculty page."""
    logger.info(f'Fetching NWU faculty page: {url}')
    try:
        resp = session.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f'Failed to fetch {url}: {e}')
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    courses = []

    tables = soup.find_all('table')
    if tables:
        for table in tables:
            courses.extend(_parse_faculty_table(table, faculty_name))
    else:
        # Some pages use definition lists or paragraph blocks
        logger.info(f'No tables found on {url}, falling back to text regex')
        from .parser import parse_text
        text = soup.get_text('\n', strip=True)
        generic = parse_text(text, 'NWU')
        for c in generic:
            c.campus = 'Potchefstroom'
        courses.extend(generic)

    logger.info(f'  {faculty_name}: {len(courses)} offerings')
    return courses


def _get_faculty_urls(session: requests.Session) -> list[tuple[str, str]]:
    """
    Fetch the NWU programme index and return list of (url, faculty_name) tuples.
    Falls back to hardcoded URLs if the index page fails.
    """
    HARDCODED = [
        ('https://studies.nwu.ac.za/undergraduate-studies/economic-and-management-sciences-2027',
         'Economic and Management Sciences'),
        ('https://studies.nwu.ac.za/undergraduate-studies/education-2027',
         'Education'),
        ('https://studies.nwu.ac.za/undergraduate-studies/engineering-2027',
         'Engineering'),
        ('https://studies.nwu.ac.za/undergraduate-studies/health-sciences-2027',
         'Health Sciences'),
        ('https://studies.nwu.ac.za/undergraduate-studies/humanities-2027',
         'Humanities'),
        ('https://studies.nwu.ac.za/undergraduate-studies/law-2027',
         'Law'),
        ('https://studies.nwu.ac.za/undergraduate-studies/natural-and-agricultural-sciences-2027',
         'Natural and Agricultural Sciences'),
        ('https://studies.nwu.ac.za/undergraduate-studies/theology-2027',
         'Theology'),
    ]

    try:
        logger.info(f'Fetching NWU index: {INDEX_URL}')
        resp = session.get(INDEX_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        results = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if 'undergraduate-studies/' in href and 'fields-study' not in href:
                # Make absolute
                if href.startswith('/'):
                    href = 'https://studies.nwu.ac.za' + href
                name = a.get_text(' ', strip=True) or ''
                if len(name) > 3 and (href, name) not in results:
                    results.append((href, name))

        if results:
            logger.info(f'Found {len(results)} faculty links from index page')
            return results
    except Exception as e:
        logger.warning(f'Index page failed ({e}), using hardcoded faculty URLs')

    return HARDCODED


def parse_nwu() -> list[ParsedCourse]:
    """
    Main entry point — scrape all NWU undergraduate programmes.
    Returns a deduplicated list of ParsedCourse objects.
    """
    session = _session()
    all_courses: list[ParsedCourse] = []
    seen = set()  # (name_lower, campus) dedup key

    faculty_urls = _get_faculty_urls(session)

    for url, faculty_name in faculty_urls:
        try:
            courses = _parse_faculty_page(url, faculty_name, session)
        except Exception as e:
            logger.error(f'Error parsing {faculty_name} ({url}): {e}')
            continue

        for c in courses:
            key = (c.name.lower().strip(), c.campus)
            if key in seen:
                continue
            seen.add(key)
            all_courses.append(c)

    logger.info(f'NWU total: {len(all_courses)} programmes (deduplicated)')
    return all_courses


def parse_nwu_url(url: str, institution_short_name: str = 'NWU') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_nwu()
