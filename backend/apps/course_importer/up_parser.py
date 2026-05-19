"""
UP (University of Pretoria) scraper.

UP's website has clean programme detail pages at /node/XXXXX with consistent labels:
- Title (h1) → programme name
- "Faculty of X" → faculty
- "Programme code: 01130119" → UP code
- "Programme information" → description
- "Career opportunities" → readable text
- "Minimum duration: 4 years, full-time"
- "Admission requirements" / "Minimum requirements" → APS, subjects

This scraper:
1. Takes any UP URL (faculty page, /undergraduate, etc.)
2. Walks all `/node/XXXXX` links it finds
3. For each programme page, extracts a ParsedCourse
"""
import logging
import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level

logger = logging.getLogger(__name__)

UP_BASE = 'https://www.up.ac.za'
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)
NODE_RE = re.compile(r'/node/\d+\b')

# Politeness: max programmes to crawl per scrape, delay between requests
MAX_PROGRAMMES_PER_SCRAPE = 200
REQUEST_DELAY_SECONDS = 0.6


# ════════════════════════════════════════════════════════════════
# HTTP helpers
# ════════════════════════════════════════════════════════════════

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-ZA,en;q=0.9',
    })
    return s


def fetch_html(url: str, session: requests.Session = None, timeout: int = 30) -> str:
    """Fetch a URL and return raw HTML (or empty string on failure)."""
    s = session or _session()
    try:
        r = s.get(url, timeout=timeout, allow_redirects=True)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.warning(f'  fetch failed {url}: {e}')
        return ''


# ════════════════════════════════════════════════════════════════
# Discovery: find all /node/XXXXX links from a starting page
# ════════════════════════════════════════════════════════════════

def _node_links_in(html: str) -> set[str]:
    """Extract all unique /node/XXXXX programme URLs from an HTML page."""
    if not html:
        return set()
    soup = BeautifulSoup(html, 'html.parser')
    found = set()
    for a in soup.find_all('a', href=True):
        href = a.get('href', '').split('?')[0].split('#')[0]
        if not href:
            continue
        if href.startswith('/'):
            href = UP_BASE + href
        elif not href.startswith('http'):
            continue
        if 'up.ac.za' in urlparse(href).netloc and NODE_RE.search(href):
            found.add(href)
    return found


def _faculty_ids_from_undergraduate(html: str) -> list[tuple[int, str]]:
    """Parse the faculty filter dropdown on /undergraduate to get all faculty IDs."""
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    select = soup.find('select', {'name': 'faculty'})
    if not select:
        return []
    out = []
    for opt in select.find_all('option'):
        val = (opt.get('value') or '').strip()
        if val.isdigit():
            out.append((int(val), opt.get_text(strip=True)))
    return out


def discover_programme_urls(start_url: str, max_urls: int = MAX_PROGRAMMES_PER_SCRAPE) -> list[str]:
    """
    Discover ALL UP programme URLs.

    Strategy:
      1. Fetch the start_url and grab any /node/XXXXX links visible.
      2. If we see UP's faculty filter dropdown, iterate through every faculty
         (and qualification level) to harvest the complete catalog.
      3. Otherwise just return what we found on the start page.
    """
    session = _session()
    found = set()

    # Step 1: scrape the entry page directly
    logger.info(f'Discover: {start_url}')
    html = fetch_html(start_url, session)
    found |= _node_links_in(html)
    logger.info(f'  → {len(found)} programmes from start page')

    # Step 2: detect which catalog page we're on (undergraduate vs postgraduate)
    # and iterate every faculty
    catalog_path = None
    if '/undergraduate' in start_url.lower():
        catalog_path = '/undergraduate'
    elif '/programmes/postgraduate' in start_url.lower() or '/postgraduate' in start_url.lower():
        catalog_path = '/programmes/postgraduate'

    if catalog_path:
        faculties = _faculty_ids_from_undergraduate(html)
        if faculties:
            logger.info(f'  Found filter form with {len(faculties)} faculties on {catalog_path} — crawling each')
            for fid, fname in faculties:
                if len(found) >= max_urls:
                    break
                # Try with both qualification levels to get degrees + diplomas (or PG variants)
                for ql in ('', '74', '75'):
                    params = f'faculty={fid}'
                    if ql:
                        params += f'&qualification_level={ql}'
                    page_url = f'{UP_BASE}{catalog_path}?{params}'
                    page_html = fetch_html(page_url, session)
                    new = _node_links_in(page_html) - found
                    found |= new
                    if new:
                        logger.info(f'    {fname[:40]:40s} (ql={ql or "all"}): +{len(new)}')
                    time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f'Discovered {len(found)} programme URLs total')
    return sorted(found)[:max_urls]


# ════════════════════════════════════════════════════════════════
# Field extraction from a single programme page
# ════════════════════════════════════════════════════════════════

# Labels we look for on the page
LABEL_HOOKS = {
    'description': ['programme information', 'overview', 'about the programme'],
    'careers': ['career opportunities', 'career options', 'employment opportunities'],
    'duration': ['minimum duration', 'duration', 'normal duration'],
    'aps': ['admission requirements', 'minimum requirements', 'aps'],
    'fees': ['fees', 'tuition'],
    'code': ['programme code', 'qualification code'],
    'faculty': ['faculty'],
}


# All known labels UP uses on programme pages, ordered by typical occurrence.
# Used to split concatenated page text into named sections.
UP_SECTION_LABELS = [
    'Programme code',
    'Programme information',
    'Career opportunities',
    'Faculty notes',
    'Closing Dates',
    'Closing dates',
    'Admission requirements',
    'Minimum requirements',
    'Achievement level',
    'Additional art requirements',
    'Important information for all prospective students',
    'Minimum duration',
    'Enquiries about the programme',
    'Disclaimer',
    'For more information, please consult the Faculty webpage',
]


def _split_into_sections(page_text: str) -> dict[str, str]:
    """
    UP concatenates labels with their content (e.g. 'Career opportunitiesGallery managers...').
    Split the text on known labels into a dict of {label: content}.
    """
    sections = {}
    # Build positions of every label in page_text
    positions = []
    for label in UP_SECTION_LABELS:
        idx = page_text.find(label)
        if idx >= 0:
            positions.append((idx, label))
    positions.sort()

    for i, (start, label) in enumerate(positions):
        content_start = start + len(label)
        content_end = positions[i + 1][0] if i + 1 < len(positions) else len(page_text)
        content = page_text[content_start:content_end].strip()
        if content:
            sections[label] = content
    return sections


def _section_text_after(soup: BeautifulSoup, label_keywords: list[str], max_chars: int = 2000) -> str:
    """
    Find content for a section by splitting the entire page text on UP's known labels.
    Returns the content matching any of the label_keywords.
    """
    text = soup.get_text(' ', strip=True)
    sections = _split_into_sections(text)
    for label, content in sections.items():
        if any(kw.lower() in label.lower() for kw in label_keywords):
            return content[:max_chars]
    return ''


def parse_programme_page(html: str, url: str) -> ParsedCourse | None:
    """Extract structured fields from a UP programme detail page."""
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')

    # Strip nav/footer noise
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe']):
        tag.decompose()

    # Title
    h1 = soup.find('h1')
    name = h1.get_text(strip=True) if h1 else ''
    if not name or len(name) < 4:
        return None

    page_text = soup.get_text(' ', strip=True)

    course = ParsedCourse(name=name[:300], institution_short_name='UP')

    # Programme code — appears as "Programme code\n01130119" or inline
    code_match = re.search(
        r'Programme\s+code[\s:]*([A-Z0-9]{6,15})',
        page_text, re.IGNORECASE,
    )
    if code_match:
        course.programme_code = code_match.group(1)

    # Faculty — "Faculty of Humanities"
    fac_match = re.search(r'Faculty\s+of\s+([A-Z][\w\s,&]+?)(?:\s{2}|\.|$|Programme)', page_text)
    if fac_match:
        # Save into source_excerpt (no faculty field on Course model)
        course.source_excerpt = f"Faculty of {fac_match.group(1).strip()[:100]}"

    # Duration — "4 years, full-time" or "Minimum duration: 3 years"
    dur_match = re.search(
        r'(?:Minimum\s+duration|Duration|Normal\s+duration)[\s:]+(\d(?:[.,]\d)?)\s*year',
        page_text, re.IGNORECASE,
    )
    if not dur_match:
        # Sometimes "X-year programme" in the title
        dur_match = re.search(r'(\d)\s*-?year\s+programme', name, re.IGNORECASE)
    if dur_match:
        try:
            course.duration_years = float(dur_match.group(1).replace(',', '.'))
        except (ValueError, IndexError):
            pass

    # APS — UP uses phrases like "APS of at least 28", "minimum APS of 30", "APS = 32"
    aps_candidates = []
    for m in re.finditer(
        r'\b(?:minimum\s+)?APS\b[^.\n]{0,40}?(\d{2})\b',
        page_text, re.IGNORECASE,
    ):
        try:
            val = int(m.group(1))
            if 18 <= val <= 50:
                aps_candidates.append(val)
        except (ValueError, IndexError):
            continue
    if aps_candidates:
        # Pick the lowest sensible APS (most lenient — usually NSC minimum)
        course.min_aps = min(aps_candidates)

    # Description — text under "Programme information"
    description = _section_text_after(soup, LABEL_HOOKS['description'])
    if description:
        course.description = description[:5000]
    else:
        # Fallback: first long paragraph after the title
        for p in soup.find_all('p'):
            txt = p.get_text(strip=True)
            if 80 < len(txt) < 1500:
                course.description = txt[:5000]
                break

    # Career opportunities
    careers = _section_text_after(soup, LABEL_HOOKS['careers'], max_chars=1500)
    if careers:
        course.career_opportunities = careers[:2000]

    # Subject requirements — search for "Mathematics: Level 5" patterns
    subject_pattern = re.compile(
        r'(Mathematics(?:\s+Literacy)?|English(?:\s*HL|\s*FAL)?|Afrikaans(?:\s*HL|\s*FAL)?|'
        r'Physical Sciences?|Life Sciences?|Geography|History|Accounting)'
        r'[\s:\-]+(?:Level\s+|Achievement\s+Level\s+|NSC\s+Level\s+)?([1-7])',
        re.IGNORECASE,
    )
    seen_subjects = set()
    for m in subject_pattern.finditer(page_text):
        subj = m.group(1).strip().title()
        try:
            level = int(m.group(2))
        except ValueError:
            continue
        if subj.lower() in seen_subjects or not (1 <= level <= 7):
            continue
        seen_subjects.add(subj.lower())
        course.subject_requirements.append({'subject': subj, 'min_level': level})

    # Fees
    fees_match = re.search(r'R\s*([\d\s,\.]{4,12})\s*(?:per\s+(?:annum|year)|p\.?a\.?)', page_text, re.IGNORECASE)
    if fees_match:
        try:
            raw = fees_match.group(1).replace(' ', '').replace(',', '').replace('.', '')
            course.fees_per_year = float(raw[:8])
        except (ValueError, IndexError):
            pass

    # Field + level classification
    course.field = classify_field(name + ' ' + (course.description or ''))
    course.level = classify_level(name)

    # Default duration if unset
    if not course.duration_years:
        DEFAULTS = {
            'certificate': 1.0, 'diploma': 3.0, 'degree': 3.0,
            'honours': 1.0, 'masters': 2.0, 'phd': 3.0,
        }
        course.duration_years = DEFAULTS.get(course.level, 3.0)

    # Default campus — UP is mostly Hatfield
    course.campus = 'Hatfield Campus'

    return course


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_up_url(start_url: str, institution_short_name: str = 'UP') -> list[ParsedCourse]:
    """Crawl a UP page, follow programme links, return ParsedCourse list."""
    programme_urls = discover_programme_urls(start_url)
    if not programme_urls:
        return []

    session = _session()
    courses = []
    seen_codes = set()
    seen_names = set()

    for i, url in enumerate(programme_urls, 1):
        logger.info(f'[{i}/{len(programme_urls)}] {url}')
        html = fetch_html(url, session)
        course = parse_programme_page(html, url)
        if not course or not course.name:
            time.sleep(REQUEST_DELAY_SECONDS)
            continue

        # Dedupe on code (preferred) or name
        if course.programme_code:
            if course.programme_code in seen_codes:
                time.sleep(REQUEST_DELAY_SECONDS)
                continue
            seen_codes.add(course.programme_code)
        else:
            key = course.name.lower().strip()
            if key in seen_names:
                time.sleep(REQUEST_DELAY_SECONDS)
                continue
            seen_names.add(key)

        course.institution_short_name = institution_short_name
        courses.append(course)
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f'Parsed {len(courses)} UP programmes')
    return courses
