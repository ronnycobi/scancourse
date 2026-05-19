"""
UCT (University of Cape Town) scraper.

UCT structures their undergraduate prospectus as faculty-specific listing pages
where programmes appear as paragraph blocks like:

    <p><strong>Bachelor of Business Science specialising in</strong><br>
    Analytics<br>
    Computer Science<br>
    ...</p>

Each `<strong>` declares a degree prefix; the lines that follow (separated by <br>)
are specialisations. This parser combines them into full programme names like
"Bachelor of Business Science specialising in Analytics".

Faculty pages used:
  /students/study-uct-degrees-diplomas-commerce/commerce-undergraduate
  /students/study-uct-degrees-diplomas-engineering-built-environment/...
  /students/study-uct-degrees-diplomas-health-sciences/health-sciences-undergraduate
  /students/study-uct-degrees-diplomas-humanities/humanities-undergraduate
  /students/study-uct-degrees-diplomas-law/law-undergraduate
  /students/study-uct-degrees-diplomas-science/science-undergraduate

Note: UCT doesn't publish per-programme APS/fees/duration on these pages.
The detailed admission scores live in the faculty handbooks (PDFs).
For now, this scraper extracts NAMES + faculty + base degree prefix; user can
then upload the UCT prospectus PDF separately for richer data.
"""
import logging
import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)

UCT_BASE = 'https://uct.ac.za'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
REQUEST_DELAY_SECONDS = 0.5

# Faculty pages (path → faculty info)
FACULTY_PAGES = {
    'commerce':   ('/students/study-uct-degrees-diplomas-commerce/commerce-undergraduate', 'Faculty of Commerce', 'business'),
    'ebe':        ('/students/study-uct-degrees-diplomas-engineering-built-environment/engineering-built-environment-undergraduate', 'Faculty of Engineering and the Built Environment', 'engineering'),
    'health':     ('/students/study-uct-degrees-diplomas-health-sciences/health-sciences-undergraduate', 'Faculty of Health Sciences', 'health'),
    'humanities': ('/students/study-uct-degrees-diplomas-humanities/humanities-undergraduate', 'Faculty of Humanities', 'humanities'),
    'law':        ('/students/study-uct-degrees-diplomas-law/law-undergraduate', 'Faculty of Law', 'law'),
    'science':    ('/students/study-uct-degrees-diplomas-science/science-undergraduate', 'Faculty of Science', 'science'),
}

# Heuristic: a <strong> qualifies as a "degree header" if its text matches one of these
DEGREE_PREFIX_RE = re.compile(
    r'^(?:'
    r'Bachelor of [A-Z][\w\s,&\-]*?'
    r'|(?:Higher\s+|Advanced\s+)?Diploma (?:in|of) [A-Z][\w\s,&\-]*?'
    r'|LLB(?:\s+\([\w\s\.]+\))?'
    r'|MBChB'
    r'|Bcom\b|BCom\b|BSc\b|BBusSc\b|BSocSc\b|BA\b|BFA\b|BArch\b|BAS\b|BMus\b|BCom\b'
    r')'
    r'(?:\s+(?:specialising in|in)\s*)?\s*$',
    re.IGNORECASE,
)

# Lines that should be ignored
JUNK_LINES = {
    'please note:', 'please note', 'apply', 'apply now', 'note:',
    'click here', 'see below', 'consult the', 'enquiries',
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT, 'Accept': 'text/html'})
    return s


def fetch_html(url: str, session: requests.Session = None, timeout: int = 30) -> str:
    s = session or _session()
    try:
        r = s.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning(f'  fetch failed {url}: {e}')
        return ''


def _is_strong_degree_header(strong_el) -> bool:
    """Check if a <strong> element looks like a degree-prefix header (e.g. 'Bachelor of X specialising in')."""
    if not strong_el:
        return False
    txt = strong_el.get_text(strip=True)
    if len(txt) < 5 or len(txt) > 100:
        return False
    if not any(kw in txt for kw in ('Bachelor', 'Diploma', 'Certificate', 'BCom', 'BSc', 'BA', 'BBusSc',
                                     'BSocSc', 'BFA', 'BArch', 'BMus', 'LLB', 'MBChB')):
        return False
    return True


def _split_specialisations(p_element, strong_el) -> list[str]:
    """Given a <p> with <strong>Degree</strong><br>spec1<br>spec2, return spec list."""
    # Replace <br> with newlines for clean splitting
    for br in p_element.find_all('br'):
        br.replace_with('\n')
    full_text = p_element.get_text('\n')
    # Strip the strong text from the start
    strong_text = strong_el.get_text(strip=True)
    if full_text.startswith(strong_text):
        rest = full_text[len(strong_text):]
    else:
        rest = full_text.replace(strong_text, '', 1)

    lines = [l.strip().rstrip('.') for l in rest.split('\n')]
    lines = [l for l in lines if l and len(l) > 1 and l.lower() not in JUNK_LINES]
    return lines[:30]


def _clean_name(name: str) -> str:
    """Remove duplications introduced by combining UCT's <strong>+<br> structure.

    Common artefacts:
      • "Bachelor of Business Science specialising in In Actuarial Science"
        → "Bachelor of Business Science specialising in Actuarial Science"
      • "Bachelor of Commerce in In Actuarial Science"
        → "Bachelor of Commerce in Actuarial Science"
      • "Diplomas in Advanced Diploma in X" (where 'Diplomas' is a section header)
        → "Advanced Diploma in X"
      • "Diplomas in Diploma in X" → "Diploma in X"
    """
    n = re.sub(r'\s+', ' ', name).strip()

    # Fix: "specialising in In X" → "specialising in X"
    n = re.sub(r'\b(specialising in)\s+In\s+', r'\1 ', n, flags=re.IGNORECASE)
    # Fix: "Bachelor of X in In Y" → "Bachelor of X in Y"
    n = re.sub(r'\bin\s+In\s+', 'in ', n, flags=re.IGNORECASE)

    # Fix: "Diplomas in <Real qualification>" — strip the section-header prefix
    n = re.sub(
        r'^Diplomas?\s+in\s+(?=(Higher|Advanced|Postgraduate)?\s*(Diploma|Certificate)\b)',
        '', n, flags=re.IGNORECASE,
    )
    # Fix: "Degrees in Bachelor of X" → "Bachelor of X"
    n = re.sub(r'^Degrees?\s+in\s+(?=Bachelor|LLB|MBChB)', '', n, flags=re.IGNORECASE)

    # Strip trailing punctuation, collapse whitespace again
    n = re.sub(r'\s+', ' ', n).strip().rstrip(',.;:')
    return n


def parse_faculty_page(html: str, url: str, faculty_code: str) -> list[ParsedCourse]:
    """Extract all programmes from a UCT faculty undergraduate page."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()

    fac_path, fac_name, default_field = FACULTY_PAGES.get(faculty_code, ('', '', 'other'))
    courses = []
    seen_names = set()

    # Iterate through every <p> that has a <strong> looking like a degree header
    for p in soup.find_all('p'):
        strong = p.find('strong')
        if not strong:
            continue
        if not _is_strong_degree_header(strong):
            continue

        prefix = strong.get_text(strip=True).rstrip(':')
        specs = _split_specialisations(p, strong)

        # Skip plural section headers — "Diplomas", "Degrees", "Qualifications"
        if re.fullmatch(r'(Diplomas?|Degrees?|Qualifications?|Programmes?)', prefix, re.IGNORECASE):
            # Each spec line is a real qualification on its own — use it directly
            for spec in specs:
                full_name = _clean_name(spec)
                if 5 < len(full_name) < 200 and full_name.lower() not in seen_names:
                    seen_names.add(full_name.lower())
                    courses.append(_make_course(full_name, fac_name, default_field))
            continue

        if not specs:
            # Standalone qualification with no specialisations
            name = _clean_name(prefix)
            if name and name.lower() not in seen_names:
                seen_names.add(name.lower())
                courses.append(_make_course(name, fac_name, default_field))
            continue

        # If prefix ends with "specialising in" or "in", combine with each spec
        connector = ''
        if re.search(r'\b(specialising in|in)\s*$', prefix, re.IGNORECASE):
            connector = ''  # already in the prefix
        else:
            connector = ' specialising in' if 'Bachelor' in prefix else ' in'

        for spec in specs:
            full_name = f'{prefix} {spec}' if connector == '' else f'{prefix}{connector} {spec}'
            full_name = _clean_name(full_name)
            if 5 < len(full_name) < 200 and full_name.lower() not in seen_names:
                seen_names.add(full_name.lower())
                courses.append(_make_course(full_name, fac_name, default_field))

    # Also catch standalone <strong> degrees in flat text (e.g. "Bachelor of Laws (LLB)")
    for strong in soup.find_all('strong'):
        if not _is_strong_degree_header(strong):
            continue
        txt = strong.get_text(strip=True).rstrip(':')
        # Skip if the strong text is a "specialising in" prefix (handled above)
        if re.search(r'\b(specialising in|in)\s*$', txt, re.IGNORECASE):
            continue
        if 'Bachelor' in txt or 'Diploma' in txt or 'LLB' in txt or 'MBChB' in txt:
            cleaned = _clean_name(txt)
            if cleaned.lower() not in seen_names and 5 < len(cleaned) < 150:
                seen_names.add(cleaned.lower())
                courses.append(_make_course(cleaned, fac_name, default_field))

    return courses


def _make_course(name: str, faculty_name: str, field_code: str) -> ParsedCourse:
    """Build a ParsedCourse from name + faculty info. APS/fees fields are left blank."""
    course = ParsedCourse(
        name=name[:300],
        institution_short_name='UCT',
        field=classify_field(name) if classify_field(name) != 'other' else field_code,
        level=classify_level(name),
        campus='Upper Campus',
        source_excerpt=f'UCT | {faculty_name}',
    )

    # Sensible default duration based on level/keywords
    name_lower = name.lower()
    if 'mbchb' in name_lower or 'medicine' in name_lower:
        course.duration_years = 6.0
    elif 'bachelor of architecture' in name_lower or 'barch' in name_lower:
        course.duration_years = 5.0
    elif 'llb' in name_lower or 'engineering' in name_lower:
        course.duration_years = 4.0
    elif 'bbussc' in name_lower or 'business science' in name_lower:
        course.duration_years = 4.0
    else:
        DEFAULTS = {
            'certificate': 1.0, 'diploma': 3.0, 'advanced_diploma': 1.0,
            'degree': 3.0, 'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
        }
        course.duration_years = DEFAULTS.get(course.level, 3.0)

    course.description = (
        f'Undergraduate qualification at the University of Cape Town, offered through the '
        f'{faculty_name}. For detailed admission requirements, fees and curriculum, see the '
        f'UCT Faculty Handbook.'
    )
    return course


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_uct_url(start_url: str = '', institution_short_name: str = 'UCT') -> list[ParsedCourse]:
    """Crawl every UCT faculty undergraduate page and return ParsedCourse list."""
    session = _session()
    all_courses = []
    seen_names = set()

    for fac_code, (path, fac_name, _field) in FACULTY_PAGES.items():
        url = UCT_BASE + path
        logger.info(f'UCT [{fac_code}]: {url}')
        html = fetch_html(url, session)
        if not html:
            continue
        courses = parse_faculty_page(html, url, fac_code)
        new_count = 0
        for c in courses:
            key = c.name.lower().strip()
            if key not in seen_names:
                seen_names.add(key)
                all_courses.append(c)
                new_count += 1
        logger.info(f'  → +{new_count} programmes (total {len(all_courses)})')
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f'Parsed {len(all_courses)} UCT programmes')
    return all_courses
