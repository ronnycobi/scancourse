"""
Wits (University of the Witwatersrand) scraper.

Wits has a clean structure:
  /undergraduate/academic-programmes/                          → faculty index
  /undergraduate/academic-programmes/faculty-of-X/             → faculty list of programmes
  /course-finder/undergraduate/{faculty-code}/{slug}/          → programme detail page

Each programme detail page has labelled <h2> sections:
  - Overview            (description)
  - Career Opportunities
  - Curriculum          (list of first/second/third-year modules)
  - Entry Requirements  (APS, English level, Maths level)
  - University Application Process
  - Closing Date

This scraper:
1. Walks /undergraduate/academic-programmes/ + each faculty page
2. Collects all /course-finder/undergraduate/ URLs
3. Visits each programme page and extracts structured fields
"""
import logging
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)

WITS_BASE = 'https://www.wits.ac.za'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
PROG_URL_RE = re.compile(r'/course-finder/undergraduate/[\w-]+/[\w-]+/?')
ACADEMIC_PROGRAMMES_PATHS = [
    '/undergraduate/academic-programmes/',
    '/undergraduate/academic-programmes/faculty-of-commerce-law-and-management/',
    '/undergraduate/academic-programmes/faculty-of-engineering-and-the-built-environment/',
    '/undergraduate/academic-programmes/faculty-of-health-sciences/',
    '/undergraduate/academic-programmes/faculty-of-humanities/',
    '/undergraduate/academic-programmes/faculty-of-science/',
]
REQUEST_DELAY_SECONDS = 0.6
MAX_PROGRAMMES = 300

FACULTY_CODE_TO_FIELD = {
    'clm': 'business',          # Commerce, Law and Management
    'ebe': 'engineering',       # Engineering and Built Environment
    'health': 'health',
    'humanities': 'humanities',
    'science': 'science',
}

FACULTY_CODE_TO_NAME = {
    'clm': 'Faculty of Commerce, Law and Management',
    'ebe': 'Faculty of Engineering and the Built Environment',
    'health': 'Faculty of Health Sciences',
    'humanities': 'Faculty of Humanities',
    'science': 'Faculty of Science',
}


# ════════════════════════════════════════════════════════════════
# HTTP helpers
# ════════════════════════════════════════════════════════════════

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


# ════════════════════════════════════════════════════════════════
# Discovery: find all programme detail URLs
# ════════════════════════════════════════════════════════════════

def discover_programme_urls(start_url: str = '', max_urls: int = MAX_PROGRAMMES) -> list[str]:
    """Walk Wits academic programme listings to collect every /course-finder/undergraduate/ URL."""
    session = _session()
    found = set()

    # Always crawl all faculty pages, regardless of starting URL
    paths = list(ACADEMIC_PROGRAMMES_PATHS)
    if start_url:
        # If user passed a specific listing URL, include it too
        path = urlparse(start_url).path
        if path and path not in paths:
            paths.insert(0, path)

    for path in paths:
        url = WITS_BASE + path
        logger.info(f'Discover: {url}')
        html = fetch_html(url, session)
        if not html:
            continue
        soup = BeautifulSoup(html, 'html.parser')
        new_count = 0
        for a in soup.find_all('a', href=True):
            href = a.get('href', '').split('?')[0].split('#')[0]
            if not href:
                continue
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = WITS_BASE + href
            elif not href.startswith('http'):
                continue
            if 'wits.ac.za' not in urlparse(href).netloc:
                continue
            if PROG_URL_RE.search(href):
                # Normalise trailing slash
                if not href.endswith('/'):
                    href = href + '/'
                if href not in found:
                    found.add(href)
                    new_count += 1
        logger.info(f'  → +{new_count} programme URLs (total {len(found)})')
        time.sleep(REQUEST_DELAY_SECONDS)
        if len(found) >= max_urls:
            break

    return sorted(found)[:max_urls]


# ════════════════════════════════════════════════════════════════
# Single programme page extraction
# ════════════════════════════════════════════════════════════════

# Section labels we look for on a programme page (in <h2>)
SECTION_LABELS = {
    'overview': ['overview', 'about'],
    'careers': ['career opportunities', 'career options'],
    'curriculum': ['curriculum', 'modules'],
    'entry': ['entry requirements', 'admission requirements', 'minimum requirements'],
    'closing': ['closing date'],
    'fees': ['fees', 'tuition'],
}


def _section_after(soup: BeautifulSoup, label_keywords: list[str], stop_tags=('h1', 'h2'), max_chars: int = 5000) -> str:
    """
    Find an <h2>/<h3> heading whose text matches one of label_keywords,
    then return the concatenated text of all following siblings until the next heading.
    """
    for el in soup.find_all(['h1', 'h2', 'h3']):
        txt = el.get_text(strip=True)
        if not txt:
            continue
        if not any(kw in txt.lower() for kw in label_keywords):
            continue
        # Walk siblings collecting text
        out = []
        node = el.find_next_sibling()
        steps = 0
        while node and steps < 60:
            if node.name in stop_tags:
                break
            t = node.get_text(' ', strip=True)
            if t:
                out.append(t)
            node = node.find_next_sibling()
            steps += 1
        if out:
            return ' '.join(out)[:max_chars]
    return ''


def _extract_modules(soup: BeautifulSoup) -> list:
    """Curriculum section often has 'First-year', 'Second-year', etc. as <strong>."""
    modules = []
    for h in soup.find_all(['h2', 'h3']):
        if 'curriculum' in h.get_text(strip=True).lower() or 'modules' in h.get_text(strip=True).lower():
            current_year = None
            node = h.find_next_sibling()
            steps = 0
            while node and steps < 80:
                if node.name in ('h1', 'h2'):
                    break
                # Year markers come as <strong>First-year</strong>
                strongs = node.find_all('strong') if hasattr(node, 'find_all') else []
                for s in strongs:
                    s_txt = s.get_text(strip=True).lower()
                    if any(y in s_txt for y in ('first-year', 'first year', 'second-year', 'second year',
                                                'third-year', 'third year', 'fourth-year', 'fourth year')):
                        current_year = s.get_text(strip=True)
                # Module list items
                for li in (node.find_all('li') if hasattr(node, 'find_all') else []):
                    text = li.get_text(' ', strip=True)
                    if 5 < len(text) < 200:
                        modules.append({'year': current_year or 'unknown', 'name': text})
                node = node.find_next_sibling()
                steps += 1
            break
    return modules[:60]


def parse_programme_page(html: str, url: str) -> ParsedCourse | None:
    """Extract a ParsedCourse from a single Wits programme detail page."""
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()

    # Title — Wits puts the programme name in <title>
    title_tag = soup.find('title')
    raw_title = title_tag.get_text(strip=True) if title_tag else ''
    # "Accounting - Wits University" → "Accounting"
    name = raw_title.split(' - ')[0].split(' | ')[0].strip()
    if not name or len(name) < 3:
        # Fallback to first h1 / h2
        h = soup.find(['h1', 'h2'])
        name = h.get_text(strip=True) if h else ''
    if not name:
        return None

    # Faculty code from URL
    fac_code = ''
    m = re.search(r'/course-finder/undergraduate/([\w-]+)/', url)
    if m:
        fac_code = m.group(1)
    faculty_name = FACULTY_CODE_TO_NAME.get(fac_code, '')

    # Improve name: prepend qualification prefix if it's a generic name like "Accounting"
    if not any(name.startswith(prefix) for prefix in ('Bachelor', 'BCom', 'BSc', 'BA', 'BEng', 'BEd', 'LLB', 'MBChB', 'Diploma', 'BAcc', 'BAS')):
        # Look for qualification clues elsewhere on page
        page_text = soup.get_text(' ', strip=True)
        if 'BCom' in page_text or 'Bachelor of Commerce' in page_text:
            name = f'BCom in {name}'
        elif 'BSc' in page_text or 'Bachelor of Science' in page_text:
            name = f'BSc in {name}'
        elif 'BEng' in page_text or 'Bachelor of Engineering' in page_text:
            name = f'BEng in {name}'
        elif 'BA' in page_text and 'Bachelor of Arts' in page_text:
            name = f'BA in {name}'

    page_text = soup.get_text(' ', strip=True)

    course = ParsedCourse(name=name[:300], institution_short_name='Wits')

    # Description — Overview section
    course.description = _section_after(soup, SECTION_LABELS['overview'])[:5000]

    # Career opportunities
    careers = _section_after(soup, SECTION_LABELS['careers'])
    if careers:
        course.career_opportunities = careers[:2000]

    # Curriculum / Modules → store as JSON list (Course model has 'modules' field)
    modules = _extract_modules(soup)

    # Entry Requirements section — extract APS, English/Maths levels
    entry_section = _section_after(soup, SECTION_LABELS['entry'])

    # APS — Wits writes "APS 38+" or "APS of 38" or just "APS 32"
    aps_candidates = []
    for m in re.finditer(r'\bAPS\b[^.\n]{0,30}?(\d{2})\b', entry_section, re.IGNORECASE):
        try:
            v = int(m.group(1))
            if 18 <= v <= 50:
                aps_candidates.append(v)
        except ValueError:
            continue
    if aps_candidates:
        course.min_aps = min(aps_candidates)  # base requirement

    # Subject requirements — "English Home Language Level 5", "Mathematics Level 6"
    subj_pattern = re.compile(
        r'(English\s+Home\s+Language(?:\s+OR\s+First\s+Additional\s+Language)?|'
        r'English\s+First\s+Additional\s+Language|English|'
        r'Mathematics(?:\s+Literacy)?|Afrikaans|Physical\s+Sciences?|Life\s+Sciences?)'
        r'\s*[:\-]?\s*Level\s+([1-7])',
        re.IGNORECASE,
    )
    seen = set()
    for m in subj_pattern.finditer(entry_section):
        subj = m.group(1).strip()[:50]
        try:
            level = int(m.group(2))
        except ValueError:
            continue
        if subj.lower() in seen or not (1 <= level <= 7):
            continue
        seen.add(subj.lower())
        course.subject_requirements.append({'subject': subj, 'min_level': level})

    # Application closing date
    closing = _section_after(soup, SECTION_LABELS['closing'])
    dl_match = re.search(r'(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})', closing)
    if dl_match:
        from datetime import datetime
        try:
            d = datetime.strptime(dl_match.group(1), '%d %B %Y').date()
            course.application_deadline = d.isoformat()
        except ValueError:
            pass

    # Field + level classification
    course.field = FACULTY_CODE_TO_FIELD.get(fac_code) or classify_field(name + ' ' + course.description)
    course.level = classify_level(name)

    # Default duration — Wits BCom/BSc/BA = 3yr, BEng = 4yr, MBChB = 6yr
    if 'BEng' in name or 'engineering' in name.lower():
        course.duration_years = 4.0
    elif 'MBChB' in name or 'medicine' in name.lower():
        course.duration_years = 6.0
    elif 'LLB' in name or 'BArch' in name:
        course.duration_years = 4.0
    else:
        DEFAULTS = {'certificate': 1.0, 'diploma': 3.0, 'degree': 3.0,
                    'honours': 1.0, 'masters': 2.0, 'phd': 3.0}
        course.duration_years = DEFAULTS.get(course.level, 3.0)

    course.programme_code = ''  # Wits doesn't publish programme codes the same way as UJ/UP
    course.campus = 'Braamfontein Campus'  # Main Wits campus
    course.source_excerpt = f'Wits | {faculty_name} | {url}'

    # Save modules to source_excerpt if no other place
    if modules:
        # Compress modules into a string for the description
        course.description = (course.description + '\n\nModules: ' +
                              ', '.join(m['name'] for m in modules[:20]))[:5000]

    return course


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_wits_url(start_url: str, institution_short_name: str = 'Wits') -> list[ParsedCourse]:
    """Crawl Wits academic programmes and return ParsedCourse list."""
    urls = discover_programme_urls(start_url)
    if not urls:
        return []

    session = _session()
    courses = []
    seen_names = set()

    for i, url in enumerate(urls, 1):
        logger.info(f'[{i}/{len(urls)}] {url}')
        html = fetch_html(url, session)
        course = parse_programme_page(html, url)
        if not course or not course.name:
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        key = course.name.lower().strip()
        if key in seen_names:
            time.sleep(REQUEST_DELAY_SECONDS)
            continue
        seen_names.add(key)

        course.institution_short_name = institution_short_name
        courses.append(course)
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f'Parsed {len(courses)} Wits programmes')
    return courses
