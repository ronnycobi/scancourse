"""
UWC (University of the Western Cape) undergraduate programme scraper.

Strategy:
  1. Iterate known department /undergraduate-programmes pages (HTML tables with subjects).
  2. Seed with known programmes + APS values from published UWC requirements.
  3. Merge scraped subject requirements with seeded APS data.

Campus: Bellville (single campus).
"""
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE = 'https://www.uwc.ac.za'

# ── Department undergraduate-programme pages that carry HTML subject tables ──
DEPARTMENT_PAGES = [
    # EMS
    (f'{BASE}/study/all-areas-of-study/departments/department-of-accounting/undergraduate-programmes',             'Economic and Management Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-economics/undergraduate-programmes',             'Economic and Management Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-management-and-entrepreneurship/undergraduate-programmes', 'Economic and Management Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-information-systems/undergraduate-programmes',   'Economic and Management Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-statistics-and-population-studies/undergraduate-programmes', 'Economic and Management Sciences'),
    # Law
    (f'{BASE}/study/all-areas-of-study/departments/department-of-public-law/undergraduate-programmes',            'Law'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-private-law/undergraduate-programmes',           'Law'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-procedural-law/undergraduate-programmes',        'Law'),
    # Arts
    (f'{BASE}/study/all-areas-of-study/departments/department-of-afrikaans-and-dutch/undergraduate-programmes',   'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-english/undergraduate-programmes',               'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-history/undergraduate-programmes',               'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-philosophy/undergraduate-programmes',            'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-political-studies/undergraduate-programmes',     'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-psychology/undergraduate-programmes',            'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-sociology/undergraduate-programmes',             'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-religious-studies-and-arabic/undergraduate-programmes', 'Arts and Humanities'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-geography-and-environmental-studies/undergraduate-programmes', 'Arts and Humanities'),
    # Education
    (f'{BASE}/study/all-areas-of-study/departments/department-of-curriculum-studies/undergraduate-programmes',    'Education'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-educational-psychology/undergraduate-programmes','Education'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-adult-and-continuing-education/undergraduate-programmes', 'Education'),
    # Natural Sciences
    (f'{BASE}/study/all-areas-of-study/departments/department-of-biodiversity-and-conservation-biology/undergraduate-programmes', 'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-biotechnology/undergraduate-programmes',         'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-chemistry/undergraduate-programmes',             'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-computer-science/undergraduate-programmes',      'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-earth-sciences/undergraduate-programmes',        'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-mathematics-and-applied-mathematics/undergraduate-programmes', 'Natural Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-physics-and-astronomy/undergraduate-programmes', 'Natural Sciences'),
    # Community & Health Sciences
    (f'{BASE}/study/all-areas-of-study/departments/department-of-nursing/undergraduate-programmes',               'Community and Health Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-occupational-therapy/undergraduate-programmes',  'Community and Health Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-physiotherapy/undergraduate-programmes',         'Community and Health Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-dietetics-and-nutrition/undergraduate-programmes', 'Community and Health Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-social-work/undergraduate-programmes',           'Community and Health Sciences'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-sport-recreation-and-exercise-science/undergraduate-programmes', 'Community and Health Sciences'),
    # Pharmacy
    (f'{BASE}/study/all-areas-of-study/schools/school-of-pharmacy/undergraduate-programmes',                      'Pharmacy'),
    # Dentistry
    (f'{BASE}/study/all-areas-of-study/departments/department-of-oral-medicine-and-periodontology/undergraduate-programmes', 'Dentistry'),
    (f'{BASE}/study/all-areas-of-study/departments/department-of-prosthetics-and-dental-materials/undergraduate-programmes', 'Dentistry'),
]

# ── Static seed: known UWC programmes with APS values ───────────────────────
# Format: (full_name, faculty, duration_years, min_aps, subjects_list)
KNOWN_PROGRAMMES = [
    # EMS
    ('Bachelor of Commerce in Accounting',                      'Economic and Management Sciences', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Accounting (Extended)',           'Economic and Management Sciences', 4, 22, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':3}]),
    ('Bachelor of Commerce in Financial Accounting',           'Economic and Management Sciences', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Economics',                      'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Information Systems',            'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Management',                     'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Supply Chain Management',        'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Industrial Psychology',          'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Law',                            'Economic and Management Sciences', 3, 28, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Administration in Public Administration',    'Economic and Management Sciences', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Economics',                                  'Economic and Management Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Higher Certificate in Economic Development',             'Economic and Management Sciences', 1, 20, [{'subject':'English','min_level':3}]),
    # Law
    ('Bachelor of Laws',                                       'Law', 4, 30, [{'subject':'English','min_level':4}]),
    ('Bachelor of Laws (Extended)',                            'Law', 5, 24, [{'subject':'English','min_level':3}]),
    ('Bachelor of Arts in Law',                                'Law', 3, 26, [{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Law',                            'Law', 3, 26, [{'subject':'English','min_level':4}]),
    ('Higher Certificate in Forensic Examination',             'Law', 1, 22, [{'subject':'English','min_level':3}]),
    # Arts
    ('Bachelor of Arts',                                       'Arts and Humanities', 3, 26, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts (Extended)',                            'Arts and Humanities', 4, 20, [{'subject':'English','min_level':3}]),
    ('Bachelor of Arts in Social Work',                        'Arts and Humanities', 4, 26, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts in Geography and Environmental Studies','Arts and Humanities', 3, 24, [{'subject':'English','min_level':4}]),
    # Education
    ('Bachelor of Education in Foundation Phase Teaching',     'Education', 4, 26, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Education in Intermediate Phase Teaching',   'Education', 4, 26, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Education in Senior Phase and Further Education and Training Teaching', 'Education', 4, 26, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    # Natural Sciences
    ('Bachelor of Science',                                    'Natural Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Science in Biotechnology',                   'Natural Sciences', 3, 30, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Science in Computer Science',                'Natural Sciences', 3, 26, [{'subject':'Mathematics','min_level':5},{'subject':'English','min_level':4}]),
    ('Bachelor of Science in Applied Geology',                 'Natural Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Science in Biodiversity and Conservation Biology', 'Natural Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Science in Chemical Sciences',               'Natural Sciences', 3, 28, [{'subject':'Mathematics','min_level':5},{'subject':'Physical Sciences','min_level':5}]),
    ('Bachelor of Science in Environmental and Water Science', 'Natural Sciences', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Science in Mathematics and Statistical Sciences', 'Natural Sciences', 3, 28, [{'subject':'Mathematics','min_level':5}]),
    ('Bachelor of Science in Medical Bioscience',              'Natural Sciences', 3, 30, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Science in Physical Science',                'Natural Sciences', 3, 28, [{'subject':'Mathematics','min_level':5},{'subject':'Physical Sciences','min_level':5}]),
    # Community & Health Sciences
    ('Bachelor of Science in Sport and Exercise Science',      'Community and Health Sciences', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Occupational Therapy',                       'Community and Health Sciences', 4, 32, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Physiotherapy',                              'Community and Health Sciences', 4, 34, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':5}]),
    ('Bachelor of Dietetics',                                  'Community and Health Sciences', 4, 30, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Nursing',                                    'Community and Health Sciences', 4, 28, [{'subject':'Mathematics','min_level':3},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Social Work',                                'Community and Health Sciences', 4, 26, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts in Community Development',              'Community and Health Sciences', 3, 24, [{'subject':'English','min_level':4}]),
    # Pharmacy
    ('Bachelor of Pharmacy',                                   'Pharmacy', 4, 32, [{'subject':'Mathematics','min_level':5},{'subject':'Life Sciences','min_level':5},{'subject':'Physical Sciences','min_level':5}]),
    # Dentistry
    ('Bachelor of Dental Surgery',                             'Dentistry', 5, 36, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':5},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Oral Health',                                'Dentistry', 3, 30, [{'subject':'Mathematics','min_level':3},{'subject':'Life Sciences','min_level':4}]),
]


LEVEL_PATTERN = re.compile(r'Level\s+(\d)', re.IGNORECASE)
PERCENT_PATTERN = re.compile(r'(\d{2,3})\s*%')


def _percent_to_level(pct: int) -> int:
    if pct >= 80: return 7
    if pct >= 70: return 6
    if pct >= 60: return 5
    if pct >= 50: return 4
    if pct >= 40: return 3
    if pct >= 30: return 2
    return 1


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _parse_subject_table(table) -> dict[str, list[dict]]:
    """
    Parse a UWC requirements table.
    Columns: Subject | Programme1 | Programme2 | ...
    Returns {programme_name: [{subject, min_level}, ...]}
    """
    rows = table.find_all('tr')
    if not rows:
        return {}

    # Header row — programme names
    header_cells = rows[0].find_all(['th', 'td'])
    if len(header_cells) < 2:
        return {}

    programme_names = []
    for cell in header_cells[1:]:
        name = cell.get_text(' ', strip=True)
        # Strip programme code suffix like "(1021)" or "1021"
        name = re.sub(r'\s*\(?(\d{4,5})\)?$', '', name).strip()
        programme_names.append(name)

    # Filter out non-programme header cells (e.g. "Level 2", blank, pure numbers)
    PROG_NAME_RE = re.compile(
        r'^(Bachelor|BCom|BSc|BAdmin|BEcon|BEd|LLB|BPharm|BDS|BNurs|BOH|'
        r'Diploma|Higher Certificate|Advanced Diploma|Certificate)\b',
        re.IGNORECASE,
    )
    programme_names = [n for n in programme_names if PROG_NAME_RE.match(n) and len(n) > 4]

    result: dict[str, list[dict]] = {n: [] for n in programme_names}
    seen: dict[str, set] = {n: set() for n in programme_names}

    for row in rows[1:]:
        cells = row.find_all(['td', 'th'])
        if len(cells) < 2:
            continue
        subject_text = cells[0].get_text(' ', strip=True)
        # Normalise subject name
        subject_text = re.sub(r'\s+', ' ', subject_text).strip()
        if not subject_text or subject_text.lower() in ('subject', 'requirement', ''):
            continue
        # Map to canonical SA subject name
        subj_canon = _canonicalise_subject(subject_text)
        if not subj_canon:
            continue

        for i, prog_name in enumerate(programme_names):
            if i + 1 >= len(cells):
                continue
            cell_text = cells[i + 1].get_text(' ', strip=True)
            level = _extract_level(cell_text)
            if level and subj_canon.lower() not in seen[prog_name]:
                seen[prog_name].add(subj_canon.lower())
                result[prog_name].append({'subject': subj_canon, 'min_level': level})

    return result


def _canonicalise_subject(text: str) -> Optional[str]:
    """Map raw subject text to a canonical SA NSC subject name."""
    t = text.lower().strip()
    if not t or t in ('-', 'n/a', 'none', 'or', 'and'):
        return None
    if 'english' in t:
        return 'English'
    if 'afrikaans' in t:
        return 'Afrikaans'
    if 'math' in t and 'lit' in t:
        return 'Mathematical Literacy'
    if 'math' in t:
        return 'Mathematics'
    if 'physical sc' in t or 'physics' in t:
        return 'Physical Sciences'
    if 'life sc' in t or 'biology' in t:
        return 'Life Sciences'
    if 'accounting' in t:
        return 'Accounting'
    if 'economics' in t:
        return 'Economics'
    if 'business' in t:
        return 'Business Studies'
    if 'geography' in t:
        return 'Geography'
    if 'history' in t:
        return 'History'
    if 'language' in t or 'home lang' in t or '1st lang' in t or 'first lang' in t:
        return 'English'
    if '2nd lang' in t or 'second lang' in t or 'additional lang' in t:
        return 'Afrikaans'
    if 'information tech' in t or 'computer' in t:
        return 'Information Technology'
    # Generic "any subject" rows — skip
    if any(k in t for k in ['any', 'elective', 'other', 'subject of choice']):
        return None
    return None


def _extract_level(cell_text: str) -> Optional[int]:
    """Extract NSC level from a cell string like 'Level 4' or '50%'."""
    m = LEVEL_PATTERN.search(cell_text)
    if m:
        level = int(m.group(1))
        return level if 1 <= level <= 7 else None
    m = PERCENT_PATTERN.search(cell_text)
    if m:
        pct = int(m.group(1))
        return _percent_to_level(pct)
    return None


def _scrape_department_page(url: str, faculty: str, session: requests.Session) -> list[ParsedCourse]:
    """Fetch one department page and extract programme names + subject requirements."""
    logger.info(f'Fetching {url}')
    try:
        resp = session.get(url, timeout=20, allow_redirects=True)
        if resp.status_code == 404:
            logger.debug(f'  404: {url}')
            return []
        resp.raise_for_status()
    except Exception as e:
        logger.debug(f'  Failed {url}: {e}')
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    courses = []

    tables = soup.find_all('table')
    for table in tables:
        prog_subjects = _parse_subject_table(table)
        for prog_name, subjects in prog_subjects.items():
            if len(prog_name) < 5:
                continue
            level = classify_level(prog_name)
            field = classify_field(prog_name + ' ' + faculty)
            dur = _duration_for(prog_name)
            c = ParsedCourse(
                name=prog_name,
                field=field,
                level=level,
                duration_years=dur,
                min_aps=0,           # filled from seed merge or default
                campus='Bellville',
                subject_requirements=subjects,
                institution_short_name='UWC',
                source_excerpt=f'Faculty: {faculty}',
            )
            courses.append(c)

    if not tables:
        # Try to extract programme names from headings/strong tags
        content = (soup.find('main') or soup.find('div', class_=re.compile(r'content|main|body', re.I)) or soup)
        for tag in content.find_all(['h2', 'h3', 'h4', 'strong']):
            text = tag.get_text(' ', strip=True)
            if re.match(r'\b(Bachelor|BCom|BSc|BAdmin|LLB|BEd|BPharm|BDS|Diploma|Higher Cert)', text, re.I) and len(text) > 6:
                text = re.sub(r'\s+', ' ', text).strip()
                text = re.sub(r'\s*\(\d{4}\)\s*$', '', text).strip()
                level = classify_level(text)
                field = classify_field(text + ' ' + faculty)
                c = ParsedCourse(
                    name=text,
                    field=field,
                    level=level,
                    duration_years=_duration_for(text),
                    min_aps=0,
                    campus='Bellville',
                    institution_short_name='UWC',
                    source_excerpt=f'Faculty: {faculty}',
                )
                courses.append(c)

    return courses


def _duration_for(name: str) -> float:
    name_l = name.lower()
    m = re.search(r'\b(\d)\s*-?\s*(?:year|yr)', name_l)
    if m:
        return float(m.group(1))
    if any(k in name_l for k in ['dental surgery', 'bds']):
        return 5.0
    if any(k in name_l for k in ['pharmacy', 'bpharm', 'occupational therapy', 'physiotherapy',
                                   'dietetics', 'nursing', 'social work', 'education', 'bed',
                                   'laws', 'llb', 'fine art', 'music']):
        return 4.0
    if 'higher certificate' in name_l or 'higher cert' in name_l:
        return 1.0
    if 'diploma' in name_l:
        return 3.0
    return 3.0


def parse_uwc() -> list[ParsedCourse]:
    """
    Main entry point — scrape all UWC undergraduate programmes.
    Returns a deduplicated list of ParsedCourse objects.
    """
    session = _session()
    all_courses: list[ParsedCourse] = []
    seen_names: set = set()

    def _clean_name(n: str) -> str:
        """Return a clean programme name (used for both display and dedup)."""
        # Strip trailing programme codes: "1612/", "(1021)", "- ECP 1753", "(4 year)"
        n = re.sub(r'\s*[\(\-]\s*(ECP\s*)?\d{4,5}[/\)]?\s*$', '', n, flags=re.IGNORECASE)
        n = re.sub(r'\s+\d{4,5}[/]?\s*$', '', n)
        n = re.sub(r'\s*-\s*ECP\s*$', '', n, flags=re.IGNORECASE)
        n = re.sub(r'\s*\(\s*\d\s*year\s*\)\s*$', '', n, flags=re.IGNORECASE)
        n = re.sub(r'[/\s]+$', '', n)
        # Expand BCom/BSc abbreviations to full form
        n = re.sub(r'^BCom\s+', 'Bachelor of Commerce in ', n, flags=re.IGNORECASE)
        n = re.sub(r'^BSc\s+', 'Bachelor of Science in ', n, flags=re.IGNORECASE)
        n = re.sub(r'^BAdmin\s+', 'Bachelor of Administration in ', n, flags=re.IGNORECASE)
        n = re.sub(r'\s+in\s+in\s+', ' in ', n, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', n).strip()

    def _norm_name(n: str) -> str:
        """Lowercase normalised key for deduplication."""
        return _clean_name(n).lower()

    # Step 1: Scrape department pages for programme names + subjects
    dept_courses: dict[str, ParsedCourse] = {}  # keyed by normalised name
    for url, faculty in DEPARTMENT_PAGES:
        courses = _scrape_department_page(url, faculty, session)
        logger.info(f'  {faculty} (dept): {len(courses)} programmes')
        for c in courses:
            c.name = _clean_name(c.name)
            key = _norm_name(c.name)
            if key not in dept_courses:
                dept_courses[key] = c

    # Step 2: Merge with static seed (seed provides APS; dept page provides subjects)
    seed_keys_added = set()
    for name, faculty, duration, min_aps, subjects in KNOWN_PROGRAMMES:
        key = _norm_name(name)
        if key in dept_courses:
            # Prefer seed's full name; enrich with APS + subjects
            dept_courses[key].name = name
            dept_courses[key].min_aps = min_aps
            dept_courses[key].duration_years = duration
            if not dept_courses[key].subject_requirements:
                dept_courses[key].subject_requirements = list(subjects)
        else:
            # Add seed programme if not found from scraping
            level = classify_level(name)
            field = classify_field(name + ' ' + faculty)
            c = ParsedCourse(
                name=name,
                field=field,
                level=level,
                duration_years=duration,
                min_aps=min_aps,
                campus='Bellville',
                subject_requirements=list(subjects),
                institution_short_name='UWC',
                source_excerpt=f'Faculty: {faculty}',
                description=f'Offered by the Faculty of {faculty} at the University of the Western Cape.',
            )
            dept_courses[key] = c
        seed_keys_added.add(key)

    # Step 3: Collect all, apply defaults for missing APS
    from apps.courses.defaults import default_subjects_for
    for key, c in dept_courses.items():
        if c.min_aps == 0:
            # Set a reasonable floor based on faculty
            faculty_text = (c.source_excerpt or '').replace('Faculty: ', '')
            c.min_aps = _faculty_aps_floor(faculty_text, c.name)
        if not c.subject_requirements:
            c.subject_requirements = default_subjects_for(c.field, c.level)
        all_courses.append(c)

    logger.info(f'UWC total: {len(all_courses)} programmes')
    return all_courses


def _faculty_aps_floor(faculty: str, name: str) -> int:
    """Return a sensible APS floor when none is available."""
    name_l = name.lower()
    if 'dentistry' in faculty.lower() or 'dental surgery' in name_l:
        return 36
    if 'pharmacy' in faculty.lower() or 'pharmacy' in name_l:
        return 32
    if 'physiotherapy' in name_l:
        return 34
    if 'occupational therapy' in name_l:
        return 32
    if 'natural sciences' in faculty.lower():
        return 26
    if 'health sciences' in faculty.lower():
        return 28
    if 'economic' in faculty.lower() or 'management' in faculty.lower():
        return 26
    if 'law' in faculty.lower():
        return 28
    if 'education' in faculty.lower():
        return 26
    return 24


def parse_uwc_url(url: str, institution_short_name: str = 'UWC') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_uwc()
