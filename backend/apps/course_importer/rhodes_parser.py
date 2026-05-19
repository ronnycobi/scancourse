"""
Rhodes University undergraduate programme scraper.

Sources:
  - Faculty APS table:  https://www.ru.ac.za/admissiongateway/departmentsandfaculties/requirements/
  - Entry requirements: https://www.ru.ac.za/admissiongateway/application/entryrequirements/
  - Curriculum pages:   https://www.ru.ac.za/admissiongateway/application/curriculumselection/{faculty}/

Rhodes has 6 faculties and a small, prestigious programme set.
Campus: Makhanda (formerly Grahamstown) — single campus.
"""
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE = 'https://www.ru.ac.za'
REQUIREMENTS_URL  = f'{BASE}/admissiongateway/departmentsandfaculties/requirements/'
ENTRY_REQ_URL     = f'{BASE}/admissiongateway/application/entryrequirements/'

FACULTY_CURRICULUM_URLS = {
    'Commerce':   f'{BASE}/admissiongateway/application/curriculumselection/commerce/',
    'Education':  f'{BASE}/admissiongateway/application/curriculumselection/education/',
    'Humanities': f'{BASE}/admissiongateway/application/curriculumselection/humanities/',
    'Law':        f'{BASE}/admissiongateway/application/curriculumselection/law/',
    'Pharmacy':   f'{BASE}/admissiongateway/application/curriculumselection/pharmacy/',
    'Science':    f'{BASE}/admissiongateway/application/curriculumselection/science/',
}

# Known Rhodes programmes (static seed — helps when HTML parsing misses names)
# Format: (full_name, faculty, duration_years)
KNOWN_PROGRAMMES = [
    # Commerce
    ('Bachelor of Business Science',              'Commerce',   4),
    ('Bachelor of Commerce',                      'Commerce',   3),
    ('Bachelor of Economics',                     'Commerce',   3),
    # Education
    ('Bachelor of Education in Foundation Phase Teaching', 'Education', 4),
    ('Bachelor of Education in Intermediate Phase Teaching', 'Education', 4),
    ('Bachelor of Education in Senior Phase and Further Education and Training Teaching', 'Education', 4),
    # Humanities
    ('Bachelor of Arts',                          'Humanities', 3),
    ('Bachelor of Fine Art',                      'Humanities', 4),
    ('Bachelor of Music',                         'Humanities', 4),
    ('Bachelor of Arts in Journalism and Media Studies', 'Humanities', 3),
    ('Bachelor of Social Science',                'Humanities', 3),
    # Law
    ('Bachelor of Laws',                          'Law',        4),
    # Pharmacy
    ('Bachelor of Pharmacy',                      'Pharmacy',   4),
    # Science
    ('Bachelor of Science',                       'Science',    3),
    ('Bachelor of Science in Information Systems','Science',    3),
    ('Bachelor of Science in Software Development','Science',   4),
    ('Bachelor of Science in Environmental Science','Science',  3),
]

# Faculty-level APS minimums (dean's discretion entry = practical minimum)
FACULTY_APS = {
    'Commerce':   34,
    'Education':  32,
    'Humanities': 30,
    'Pharmacy':   40,
    'Science':    38,
    'Law':        32,
}

# Faculty-level subject requirements
FACULTY_SUBJECTS = {
    'Commerce': [
        {'subject': 'Mathematics', 'min_level': 4},
        {'subject': 'English', 'min_level': 4},
    ],
    'Education': [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 3},
    ],
    'Humanities': [
        {'subject': 'English', 'min_level': 4},
    ],
    'Pharmacy': [
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Life Sciences', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 5},
    ],
    'Science': [
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 4},
    ],
    'Law': [
        {'subject': 'English', 'min_level': 4},
    ],
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _get_soup(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    """Fetch URL and return BeautifulSoup, or None on failure."""
    logger.info(f'Fetching {url}')
    try:
        resp = session.get(url, timeout=30, allow_redirects=True)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'html.parser')
    except Exception as e:
        logger.warning(f'Failed to fetch {url}: {e}')
        return None


def _extract_content(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """
    Extract the main content div — handles both page templates:
    - Template A (MDL): <main class="demo-main">
    - Template B (Kingster WP): <div class="gdlr-core-text-box-item-content">
    """
    if soup is None:
        return None
    # Template B (WordPress)
    content = soup.find('div', class_='gdlr-core-text-box-item-content')
    if content:
        return content
    # Template A (MDL)
    main = soup.find('main', class_='demo-main')
    if main:
        return main
    # Fallback: the whole body
    return soup.find('body') or soup


def _scrape_faculty_aps(session: requests.Session) -> dict:
    """
    Scrape the faculty requirements table.
    Returns dict: {faculty_name: min_aps}
    """
    aps_map = dict(FACULTY_APS)  # start with hardcoded defaults
    soup = _get_soup(REQUIREMENTS_URL, session)
    if not soup:
        return aps_map

    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = [td.get_text(' ', strip=True) for td in row.find_all(['td', 'th'])]
            if len(cells) < 3:
                continue
            faculty_cell = cells[0].strip()
            # Match known faculties
            for faculty in FACULTY_APS:
                if faculty.lower() in faculty_cell.lower():
                    # Extract first number from extended/dean's column
                    for cell in cells[1:]:
                        nums = re.findall(r'\b(\d{2})\b', cell)
                        if nums:
                            try:
                                val = int(nums[0])
                                if 20 <= val <= 50:
                                    aps_map[faculty] = val
                                    break
                            except ValueError:
                                pass
                    break

    logger.info(f'Faculty APS map: {aps_map}')
    return aps_map


def _parse_programme_names_from_page(content, faculty_name: str) -> list[str]:
    """
    Extract programme names from a curriculum selection page.
    Only accepts clean, complete degree names — rejects fragments.
    """
    if content is None:
        return []

    names = []
    seen = set()

    # Patterns that signal a real programme name (must end cleanly)
    DEGREE_PATTERN = re.compile(
        r'\b(Bachelor of (?:Business Science|Commerce|Economics|Arts|Laws?|'
        r'Science|Education|Fine Art|Music|Pharmacy|Social Science|'
        r'Environmental Science|Information Systems|Software Development'
        r'|[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,4})'
        r'(?:\s+in\s+[A-Z][A-Za-z\s,&\-]{2,50})?'
        r'|BPharm\b'
        r'|LLB\b)',
    )

    NOISE_PATTERNS = [
        r'might look like',
        r'over \w+ years?',
        r'are classified',
        r'etc[,\.]',
        r'\bDEGREE\b',
        r'\bSTUDIES\b',
        r'\w+\s*[,;]\s*\w+\s*[,;]',  # "BCom, BSc, etc"
        r'^\s*BSc\s*[,\(]',            # "BSc (InfSys))" style fragments
    ]

    # Only scan heading-level and list tags (not prose paragraphs)
    for tag in content.find_all(['h1', 'h2', 'h3', 'h4', 'strong', 'b', 'li']):
        text = tag.get_text(' ', strip=True)
        # Must be a plausible name length
        if len(text) < 8 or len(text) > 150:
            continue
        # Reject noise
        noise = False
        for np in NOISE_PATTERNS:
            if re.search(np, text, re.IGNORECASE):
                noise = True
                break
        if noise:
            continue

        for m in DEGREE_PATTERN.finditer(text):
            raw = m.group(0).strip()
            raw = re.sub(r'\s+', ' ', raw)
            raw = re.sub(r'[,;:\s\(\)]+$', '', raw)
            # Must be a full proper name (at least 3 words)
            if len(raw.split()) < 3:
                continue
            # Skip ALL-CAPS fragments (truncated names)
            if raw == raw.upper() and len(raw) < 20:
                continue
            norm = raw.lower()
            if norm not in seen:
                seen.add(norm)
                names.append(raw)

    return names


def _duration_for(name: str, faculty: str) -> float:
    """Assign duration based on programme name and faculty knowledge."""
    name_lower = name.lower()
    # Explicit year mentions
    m = re.search(r'\b(\d)\s*-?\s*year', name_lower)
    if m:
        return float(m.group(1))
    # Known long programmes
    if any(k in name_lower for k in ['pharmacy', 'bpharm', 'laws', 'llb', 'fine art', 'music',
                                       'business science', 'software']):
        return 4.0
    if 'education' in name_lower or 'bed' in name_lower:
        return 4.0
    if 'diploma' in name_lower:
        return 3.0
    if 'certificate' in name_lower:
        return 1.0
    return 3.0


def parse_rhodes() -> list[ParsedCourse]:
    """
    Main entry point — scrape all Rhodes University undergraduate programmes.
    Returns a list of ParsedCourse objects (one per programme, single campus).
    """
    session = _session()

    # Step 1: Get faculty APS minimums
    faculty_aps = _scrape_faculty_aps(session)

    # Step 2: Scrape programme names from each faculty curriculum page
    all_programmes: list[tuple[str, str]] = []  # (name, faculty)
    seen_names: set = set()

    for faculty, url in FACULTY_CURRICULUM_URLS.items():
        soup = _get_soup(url, session)
        content = _extract_content(soup)
        names = _parse_programme_names_from_page(content, faculty)
        logger.info(f'  {faculty}: {len(names)} programmes found from web')
        for n in names:
            key = n.lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                all_programmes.append((n, faculty))

    # Step 3: Seed with known programmes (fill gaps)
    for name, faculty, _ in KNOWN_PROGRAMMES:
        key = name.lower().strip()
        if key not in seen_names:
            seen_names.add(key)
            all_programmes.append((name, faculty))
            logger.info(f'  Seeded: {name} ({faculty})')

    # Step 4: Build ParsedCourse objects
    courses: list[ParsedCourse] = []
    for name, faculty in all_programmes:
        # Clean name
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'[,;:\s]+$', '', name)
        if len(name) < 5:
            continue

        min_aps = faculty_aps.get(faculty, 30)
        # Override for specific programmes
        name_lower = name.lower()
        if 'pharmacy' in name_lower or 'bpharm' in name_lower:
            min_aps = faculty_aps.get('Pharmacy', 40)
        elif 'business science' in name_lower:
            min_aps = faculty_aps.get('Commerce', 34) + 2  # BBS typically higher
        elif 'law' in name_lower or 'llb' in name_lower:
            min_aps = 32

        subjects = list(FACULTY_SUBJECTS.get(faculty, []))
        duration = _duration_for(name, faculty)
        level = classify_level(name)
        field = classify_field(name + ' ' + faculty)

        c = ParsedCourse(
            name=name,
            field=field,
            level=level,
            duration_years=duration,
            min_aps=min_aps,
            campus='Makhanda',
            subject_requirements=subjects,
            institution_short_name='Rhodes',
            source_excerpt=f'Faculty: {faculty}',
            description=f'Offered by the Faculty of {faculty} at Rhodes University, Makhanda.',
        )
        courses.append(c)

    logger.info(f'Rhodes total: {len(courses)} programmes')
    return courses


def parse_rhodes_url(url: str, institution_short_name: str = 'Rhodes') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_rhodes()
