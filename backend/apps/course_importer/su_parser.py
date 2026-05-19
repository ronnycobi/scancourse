"""
Stellenbosch (SU) scraper.

SU publishes its programme catalogue as PDF documents per faculty:
  - Faculty brochures (e.g. fass-pamphlet-2026-eng.pdf)
  - Yearbooks (e.g. 2026-yearbook-engineering.pdf)
  - Admission requirement docs

The SU website is behind Cloudflare; we use cloudscraper to bypass the
JS challenge for HTML pages, then download each faculty brochure PDF and
parse it using the generic regex-based programme detector.

Faculty pages we discover from:
  /en/faculties/<slug>           – overview page
  /en/faculties/<slug>/prospective-students/undergraduate
"""
import logging
import re
import time
from urllib.parse import urljoin, urlparse

import cloudscraper
from bs4 import BeautifulSoup

from .parser import ParsedCourse, parse_text, classify_field, classify_level

logger = logging.getLogger(__name__)

SU_BASE = 'https://www.su.ac.za'
REQUEST_DELAY_SECONDS = 0.6
MAX_PROGRAMMES = 400

# Faculty slugs SU uses on their /en/faculties/<slug> pages
FACULTIES = [
    ('agrisciences',  'Faculty of AgriSciences',                    'agriculture'),
    ('education',     'Faculty of Education',                       'education'),
    ('medicine',      'Faculty of Medicine and Health Sciences',    'health'),
    ('theology',      'Faculty of Theology',                        'humanities'),
    ('arts',          'Faculty of Arts and Social Sciences',        'humanities'),
    ('engineering',   'Faculty of Engineering',                     'engineering'),
    ('military',      'Faculty of Military Science',                'other'),
    ('economy',       'Faculty of Economic and Management Sciences','business'),
    ('law',           'Faculty of Law',                             'law'),
    ('science',       'Faculty of Science',                         'science'),
    ('data-science',  'School for Data Science and Computational Thinking', 'ict'),
]

# PDFs we DON'T want to parse — these aren't programme catalogues
SKIP_PDF_KEYWORDS = (
    'paia-manual', 'paia_manual', 'privacy', 'pdf-empty',
    'registration-rules', 'registrasiereels',
    'application-step-step-guide', 'how-apply',
    'liptip', 'important-information-eng-updated',
    'phd-guidelines',
)

# PDFs we DO want — brochures, prospectuses, yearbooks, admission requirements
WANTED_PDF_KEYWORDS = (
    'brochure', 'pamphlet', 'prospect',
    'yearbook', 'jaarboek',
    'admission', 'admissions',
    'undergrad', 'undergraduate',
)


# ════════════════════════════════════════════════════════════════
# HTTP — needs cloudscraper to bypass SU's Cloudflare challenge
# ════════════════════════════════════════════════════════════════

def _scraper():
    return cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'darwin', 'desktop': True},
    )


def fetch_html(url: str, scraper, timeout: int = 30) -> str:
    try:
        r = scraper.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
        logger.warning(f'  fetch {url}: HTTP {r.status_code}')
        return ''
    except Exception as e:
        logger.warning(f'  fetch {url}: {e}')
        return ''


def fetch_pdf(url: str, scraper, timeout: int = 60) -> bytes:
    try:
        r = scraper.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.content[:4] == b'%PDF':
            return r.content
        logger.warning(f'  PDF {url}: HTTP {r.status_code} or not a PDF')
        return b''
    except Exception as e:
        logger.warning(f'  PDF {url}: {e}')
        return b''


# ════════════════════════════════════════════════════════════════
# Discovery — find PDF brochures per faculty
# ════════════════════════════════════════════════════════════════

def _normalise(href: str, base: str) -> str:
    h = (href or '').split('#')[0]
    if not h:
        return ''
    if h.startswith('/'):
        return urljoin('https://www.su.ac.za', h)
    if h.startswith('http'):
        return h
    return urljoin(base, h)


def _wanted_pdf(url: str) -> bool:
    u = url.lower()
    if not u.endswith('.pdf'):
        return False
    if any(k in u for k in SKIP_PDF_KEYWORDS):
        return False
    return any(k in u for k in WANTED_PDF_KEYWORDS)


# Yearbook filename slugs per faculty. SU publishes them under
# https://files.su.ac.za/public/registrars-division/documents/<YEAR-MONTH>/2026-yearbook-<slug>.pdf
# but the YEAR-MONTH varies per faculty, so we try a few candidate months.
YEARBOOK_FACULTY_SLUGS = {
    'agrisciences': 'agrisciences',
    'arts':         'arts-and-social-sciences',
    'economy':      'economic-and-management-sciences',
    'education':    'education',
    'engineering':  'engineering',
    'law':          'law',
    'medicine':     'medicine-and-health-sciences',
    'military':     'military-science',
    'science':      'science',
    'theology':     'theology',
}
YEARBOOK_YEAR = '2026'  # the academic year covered by the yearbook
YEARBOOK_CANDIDATE_MONTHS = [
    '2025-08', '2025-09', '2025-10', '2025-11', '2025-12',
    '2026-01', '2026-02', '2026-03',
]


def find_yearbook_url(scraper, faculty_slug: str) -> str:
    """
    Probe candidate month prefixes to find the actual yearbook URL.
    Uses a Range-limited GET (HEAD doesn't work past Cloudflare here).
    """
    fname_slug = YEARBOOK_FACULTY_SLUGS.get(faculty_slug)
    if not fname_slug:
        return ''
    for ym in YEARBOOK_CANDIDATE_MONTHS:
        url = (
            f'https://files.su.ac.za/public/registrars-division/documents/'
            f'{ym}/{YEARBOOK_YEAR}-yearbook-{fname_slug}.pdf'
        )
        try:
            # Range-limited GET — only fetch first 8 bytes to check existence
            r = scraper.get(url, timeout=10, allow_redirects=True,
                            headers={'Range': 'bytes=0-7'})
            if r.status_code in (200, 206) and r.content[:4] == b'%PDF':
                return url
        except Exception:
            continue
    return ''


# Per-faculty HTML programme listings (verified working).
# Some faculties expose richer content on department / "what-can-i-study" sub-pages.
FACULTY_HTML_PAGES = {
    'agrisciences':  ['/en/faculties/agrisciences/undergraduate'],
    'arts':          ['/en/faculties/arts'],  # arts publishes mainly via PDFs
    'economy':       ['/en/faculties/economy/prospective-students'],
    'education':     ['/en/faculties/education/undergraduate-programmes'],
    'engineering':   ['/en/faculties/engineering/prospective-students/undergraduate'],
    'law':           ['/en/faculties/law/programmes-0', '/en/faculties/law/programmes'],
    'medicine':      ['/en/faculties/medicine'],
    'military':      ['/en/faculties/military/programmes-0/undergraduate-programmes'],
    'science':       [
        '/en/faculties/science/undergraduate-programmes',
        '/en/faculties/science/what-can-i-study/undergraduate-programmes-biological-sciences',
        '/en/faculties/science/what-can-i-study/undergraduate-programmes-interdisciplinary-0',
        '/en/faculties/science/what-can-i-study/undergraduate-programmes-mathematical-sciences',
        '/en/faculties/science/what-can-i-study/undergraduate-programmes-physical-sciences',
    ],
    'theology':      ['/en/faculties/theology/programmes-0'],
    'data-science':  ['/en/faculties/data-science/study'],
}


def fetch_faculty_html_pages(scraper, faculty_slug: str) -> list[str]:
    """Fetch every programme-listing HTML page for a faculty and return their text."""
    paths = FACULTY_HTML_PAGES.get(faculty_slug, [])
    pages_text = []
    for path in paths:
        url = SU_BASE + path
        html = fetch_html(url, scraper)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            pages_text.append(soup.get_text(' ', strip=True))
        time.sleep(REQUEST_DELAY_SECONDS)
    return pages_text


def discover_faculty_pdfs(scraper) -> list[tuple[str, str, str]]:
    """
    For each faculty, collect brochure / yearbook / admissions PDFs.
    Strategy:
      1. Probe direct yearbook URL with Range-GET.
      2. Crawl the faculty overview + prospective-students pages for additional brochures.
    Returns list of (faculty_slug, faculty_name, pdf_url).
    """
    found = []
    for slug, name, _field in FACULTIES:
        seen_pdfs = set()

        # 1. Direct yearbook — probe candidate month prefixes
        yb_url = find_yearbook_url(scraper, slug)
        if yb_url:
            seen_pdfs.add(yb_url)
            found.append((slug, name, yb_url))
            logger.info(f'  {slug:15s}: yearbook found at {yb_url[-50:]}')

        # 2. Crawl public-facing pages for additional brochures
        urls_to_visit = [
            f'{SU_BASE}/en/faculties/{slug}',
            f'{SU_BASE}/en/faculties/{slug}/prospective-students',
            f'{SU_BASE}/en/faculties/{slug}/prospective-students/undergraduate',
        ]
        for u in urls_to_visit:
            html = fetch_html(u, scraper)
            if not html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            for a in soup.find_all('a', href=True):
                pdf = _normalise(a.get('href', ''), u)
                if _wanted_pdf(pdf) and pdf not in seen_pdfs:
                    seen_pdfs.add(pdf)
                    found.append((slug, name, pdf))
            time.sleep(REQUEST_DELAY_SECONDS)
        logger.info(f'  {slug:15s}: {len(seen_pdfs)} PDFs')
    return found


# ════════════════════════════════════════════════════════════════
# PDF parsing — reuse generic parser, tag results with faculty
# ════════════════════════════════════════════════════════════════

def _read_pdf_text(pdf_bytes: bytes) -> str:
    """Use pdfplumber if available, fall back to PyPDF2."""
    if not pdf_bytes:
        return ''
    try:
        import pdfplumber, io
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            return '\n\n'.join(p.extract_text() or '' for p in pdf.pages)
    except Exception:
        try:
            from PyPDF2 import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            return '\n\n'.join(p.extract_text() or '' for p in reader.pages)
        except Exception as e:
            logger.warning(f'  PDF text extraction failed: {e}')
            return ''


def parse_pdf_for_faculty(pdf_bytes: bytes, faculty_name: str, default_field: str) -> list[ParsedCourse]:
    """Parse a single SU faculty PDF and tag each programme with the faculty."""
    text = _read_pdf_text(pdf_bytes)
    if not text:
        return []

    # Use the generic regex-based parser
    courses = parse_text(text, institution_short_name='SU')

    # Override field with faculty default if classification gave 'other'
    for c in courses:
        if c.field == 'other' and default_field:
            c.field = default_field
        c.campus = 'Stellenbosch Main Campus'
        c.institution_short_name = 'SU'
        c.source_excerpt = f'SU | {faculty_name}'

    return courses


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_su_url(start_url: str = '', institution_short_name: str = 'SU') -> list[ParsedCourse]:
    """
    Build a complete SU programme catalogue:
      • For each faculty, fetch every known HTML programme-listing page and parse
        with the generic regex parser.
      • Then fetch any brochure / yearbook PDFs we discover or know about and
        parse those too.
    Results are deduplicated across all sources.
    """
    scraper = _scraper()

    # Warm up the Cloudflare challenge
    fetch_html(SU_BASE + '/en', scraper)
    time.sleep(1)

    all_courses: list[ParsedCourse] = []
    seen_names: set[str] = set()
    fac_default_field = {slug: f for slug, _, f in FACULTIES}
    fac_full_name = {slug: n for slug, n, _ in FACULTIES}

    def add_courses(courses, slug_label):
        new = 0
        for c in courses:
            key = c.name.lower().strip()
            if not key or key in seen_names or len(key) < 5:
                continue
            seen_names.add(key)
            c.institution_short_name = institution_short_name
            all_courses.append(c)
            new += 1
        logger.info(f'  → +{new} from {slug_label} (total {len(all_courses)})')

    # ── PASS 1: HTML programme pages per faculty ──────────────
    logger.info('SU pass 1: HTML programme pages…')
    for slug, fname, _ in FACULTIES:
        pages_text = fetch_faculty_html_pages(scraper, slug)
        for i, text in enumerate(pages_text):
            courses = parse_text(text, institution_short_name='SU')
            for c in courses:
                if c.field == 'other' and fac_default_field[slug] != 'other':
                    c.field = fac_default_field[slug]
                c.campus = 'Stellenbosch Main Campus'
                c.source_excerpt = f'SU | {fname} | HTML page {i+1}'
            add_courses(courses, f'{slug} html#{i+1}')

    # ── PASS 2: any brochure / yearbook PDFs we can find ──────
    logger.info('\nSU pass 2: brochure / yearbook PDFs…')
    pdf_refs = discover_faculty_pdfs(scraper)
    logger.info(f'  Found {len(pdf_refs)} PDF refs')
    for i, (slug, fname, pdf_url) in enumerate(pdf_refs, 1):
        if len(all_courses) >= MAX_PROGRAMMES:
            break
        logger.info(f'[{i}/{len(pdf_refs)}] {slug}: {pdf_url[-80:]}')
        pdf_bytes = fetch_pdf(pdf_url, scraper)
        if not pdf_bytes:
            continue
        courses = parse_pdf_for_faculty(
            pdf_bytes, fac_full_name[slug], fac_default_field[slug],
        )
        add_courses(courses, f'{slug} PDF')
        time.sleep(REQUEST_DELAY_SECONDS)

    logger.info(f'\nParsed {len(all_courses)} SU programmes total')
    return all_courses
