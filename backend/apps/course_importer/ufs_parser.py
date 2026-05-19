"""
UFS (University of the Free State) undergraduate programme scraper.

Strategy:
  1. Fetch known faculty/department HTML pages to extract APS from prose text.
  2. Download key PDF yearbooks via pdfplumber for structured programme data.
  3. Merge with a comprehensive static seed list for complete coverage.

Campuses: Bloemfontein (main), Qwaqwa, South Campus (ODeL/distance).
"""
import re
import io
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE = 'https://www.ufs.ac.za'

# ── Known HTML pages with inline APS / programme data ───────────────────────
PROGRAMME_PAGES = [
    # (url, faculty_name, campus)
    (f'{BASE}/humanities/faculty-of-the-humanities-home/academic-information/ba-programme',
     'Humanities', 'Bloemfontein'),
    (f'{BASE}/humanities/faculty-of-the-humanities-home/academic-information/bsocsci-programme',
     'Humanities', 'Bloemfontein'),
    (f'{BASE}/law/faculty-of-law-home/admissions/LLB',
     'Law', 'Bloemfontein'),
    (f'{BASE}/edu/faculty-of-education/general/undergraduate-studies',
     'Education', 'Bloemfontein'),
    (f'{BASE}/health/faculty-of-health-sciences-home/academic-information/undergraduate-admission',
     'Health Sciences', 'Bloemfontein'),
    (f'{BASE}/natagri/departments-and-divisions/agricultural-economics-home/prospective-students',
     'Natural and Agricultural Sciences', 'Bloemfontein'),
    (f'{BASE}/econ/departments-and-divisions/economics-home/general/department-home-page/programmes',
     'Economic and Management Sciences', 'Bloemfontein'),
    (f'{BASE}/econ/departments-and-divisions/school-of-accountancy-home/general/department-home-page',
     'Economic and Management Sciences', 'Bloemfontein'),
    (f'{BASE}/theology/faculty-of-theology-and-religion-home/academic-information/undergraduate',
     'Theology and Religion', 'Bloemfontein'),
]

# ── PDF yearbooks (text-layer, parseable with pdfplumber) ────────────────────
PDF_SOURCES = [
    (f'{BASE}/docs/librariesprovider20/rule-books/2026/the-humanities_rule-book_2026.pdf',
     'Humanities', 'Bloemfontein'),
    (f'{BASE}/docs/librariesprovider21/rulebooks/ufs---law-combined-rulebook-2026.pdf',
     'Law', 'Bloemfontein'),
    (f'{BASE}/docs/librariesprovider24/2026-documents/education-2026-rulebook.pdf',
     'Education', 'Bloemfontein'),
]

# ── Comprehensive static seed ────────────────────────────────────────────────
# (full_name, faculty, campus, duration_years, min_aps, subjects)
KNOWN_PROGRAMMES = [
    # ── Economic and Management Sciences ──────────────────────────────────────
    ('Bachelor of Commerce in Accounting',                        'Economic and Management Sciences', 'Bloemfontein', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Accounting (Extended)',             'Economic and Management Sciences', 'Bloemfontein', 4, 22, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':3}]),
    ('Bachelor of Commerce in Economics',                         'Economic and Management Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Finance',                           'Economic and Management Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Business Management',               'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Human Resource Management',         'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Information Technology Management', 'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Marketing Management',              'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Supply Chain Management',           'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Transport Economics',               'Economic and Management Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Public Administration',             'Economic and Management Sciences', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Administration',                                'Economic and Management Sciences', 'Bloemfontein', 3, 22, [{'subject':'English','min_level':4}]),
    ('Bachelor of Commerce in Financial Business Analytics',      'Economic and Management Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    # Qwaqwa
    ('Bachelor of Commerce in Accounting',                        'Economic and Management Sciences', 'Qwaqwa', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Administration',                                'Economic and Management Sciences', 'Qwaqwa', 3, 22, [{'subject':'English','min_level':4}]),

    # ── Education ─────────────────────────────────────────────────────────────
    ('Bachelor of Education in Foundation Phase Teaching',        'Education', 'Bloemfontein', 4, 30, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Education in Intermediate Phase Teaching',      'Education', 'Bloemfontein', 4, 30, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Education in Senior Phase and Further Education and Training Teaching', 'Education', 'Bloemfontein', 4, 30, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Education in Senior Phase and Further Education and Training Teaching', 'Education', 'Qwaqwa', 4, 30, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),

    # ── Health Sciences ───────────────────────────────────────────────────────
    ('Bachelor of Medicine and Bachelor of Surgery',              'Health Sciences', 'Bloemfontein', 6, 38, [{'subject':'Mathematics','min_level':5},{'subject':'Life Sciences','min_level':5},{'subject':'Physical Sciences','min_level':5}]),
    ('Bachelor of Medical Science in Radiation Sciences',         'Health Sciences', 'Bloemfontein', 4, 30, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Occupational Therapy',                          'Health Sciences', 'Bloemfontein', 4, 32, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Science in Dietetics',                          'Health Sciences', 'Bloemfontein', 4, 30, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Science in Physiotherapy',                      'Health Sciences', 'Bloemfontein', 4, 34, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':5}]),
    ('Bachelor of Biokinetics',                                   'Health Sciences', 'Bloemfontein', 4, 28, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Optometry',                                     'Health Sciences', 'Bloemfontein', 4, 34, [{'subject':'Mathematics','min_level':5},{'subject':'Physical Sciences','min_level':5}]),
    ('Bachelor of Sport Coaching',                                'Health Sciences', 'Bloemfontein', 4, 26, [{'subject':'English','min_level':4},{'subject':'Life Sciences','min_level':3}]),
    ('Bachelor of Nursing',                                       'Health Sciences', 'Bloemfontein', 4, 28, [{'subject':'Mathematics','min_level':3},{'subject':'Life Sciences','min_level':4}]),
    ('Bachelor of Social Work',                                   'Health Sciences', 'Bloemfontein', 4, 26, [{'subject':'English','min_level':4}]),

    # ── Humanities ────────────────────────────────────────────────────────────
    ('Bachelor of Arts',                                          'Humanities', 'Bloemfontein', 3, 30, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts (Extended)',                               'Humanities', 'Bloemfontein', 4, 25, [{'subject':'English','min_level':3}]),
    ('Bachelor of Social Science',                                'Humanities', 'Bloemfontein', 3, 30, [{'subject':'English','min_level':4}]),
    ('Bachelor of Social Science (Extended)',                     'Humanities', 'Bloemfontein', 4, 25, [{'subject':'English','min_level':3}]),
    ('Bachelor of Arts in Communication Science',                 'Humanities', 'Bloemfontein', 3, 30, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts in Information Science',                   'Humanities', 'Bloemfontein', 3, 28, [{'subject':'English','min_level':4}]),
    ('Bachelor of Drama Arts',                                    'Humanities', 'Bloemfontein', 3, 28, [{'subject':'English','min_level':4}]),
    ('Bachelor of Music',                                         'Humanities', 'Bloemfontein', 4, 28, [{'subject':'English','min_level':4}]),
    # Qwaqwa campus
    ('Bachelor of Arts',                                          'Humanities', 'Qwaqwa', 3, 28, [{'subject':'English','min_level':4}]),

    # ── Law ───────────────────────────────────────────────────────────────────
    ('Bachelor of Laws',                                          'Law', 'Bloemfontein', 4, 33, [{'subject':'English','min_level':6},{'subject':'Mathematics','min_level':3}]),

    # ── Natural and Agricultural Sciences ────────────────────────────────────
    ('Bachelor of Science',                                       'Natural and Agricultural Sciences', 'Bloemfontein', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Science (Extended)',                            'Natural and Agricultural Sciences', 'Bloemfontein', 4, 22, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3}]),
    ('Bachelor of Science in Agriculture',                        'Natural and Agricultural Sciences', 'Bloemfontein', 4, 26, [{'subject':'Mathematics','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    ('Bachelor of Agricultural Management',                       'Natural and Agricultural Sciences', 'Bloemfontein', 3, 24, [{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Consumer Science: Food Management',             'Natural and Agricultural Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    ('Bachelor of Consumer Science: Fashion Management and Retailing', 'Natural and Agricultural Sciences', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Environmental Science',                         'Natural and Agricultural Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Life Sciences','min_level':3}]),
    ('Bachelor of Science in Geoinformatics',                     'Natural and Agricultural Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4}]),
    ('Bachelor of Science in Software Engineering',               'Natural and Agricultural Sciences', 'Bloemfontein', 3, 28, [{'subject':'Mathematics','min_level':5}]),
    ('Bachelor of Science in Computer Science and Informatics',   'Natural and Agricultural Sciences', 'Bloemfontein', 3, 26, [{'subject':'Mathematics','min_level':4}]),
    # Qwaqwa
    ('Bachelor of Science',                                       'Natural and Agricultural Sciences', 'Qwaqwa', 3, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),

    # ── Theology and Religion ────────────────────────────────────────────────
    ('Bachelor of Theology',                                      'Theology and Religion', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts in Theology',                              'Theology and Religion', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Arts in Religious Studies',                     'Theology and Religion', 'Bloemfontein', 3, 24, [{'subject':'English','min_level':4}]),
    ('Bachelor of Theology',                                      'Theology and Religion', 'Qwaqwa', 3, 22, [{'subject':'English','min_level':4}]),
]

APS_PATTERN = re.compile(
    r'(?:minimum\s+)?(?:APS|AP)\s*(?:score|Score|points?)?\s*(?:of|:|\=)?\s*(\d{2})\b',
    re.IGNORECASE,
)

DEGREE_PATTERN = re.compile(
    r'\b(Bachelor of [A-Z][A-Za-z\s,&\-()]{3,80}?'
    r'|Diploma in [A-Z][A-Za-z\s,&\-()]{3,60}?'
    r'|Higher Certificate in [A-Z][A-Za-z\s,&\-()]{3,60}?'
    r'|Advanced Certificate in [A-Z][A-Za-z\s,&\-()]{3,60}?'
    r'|LLB\b'
    r'|BTheo\b'
    r'|MBChB\b)'
    r'(?=[\s,\.\(\n]|$)',
)

SUBJECT_LEVEL_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English|Afrikaans|Accounting|Economics|Biology|Chemistry|Physics)'
    r'[^.]{0,30}?[Ll]evel\s+(\d)',
    re.IGNORECASE,
)

SUBJECT_PERCENT_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English|Afrikaans|Accounting|Economics|Biology|Chemistry|Physics)'
    r'[^.]{0,30}?(\d{2})\s*%',
    re.IGNORECASE,
)


def _pct_to_level(pct: int) -> int:
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


def _fetch(url: str, session: requests.Session, timeout: int = 25) -> Optional[requests.Response]:
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r
        logger.debug(f'  {r.status_code}: {url}')
    except Exception as e:
        logger.debug(f'  Error fetching {url}: {e}')
    return None


def _extract_aps(text: str) -> int:
    """Extract first valid APS score from a block of text."""
    for m in APS_PATTERN.finditer(text):
        try:
            val = int(m.group(1))
            if 18 <= val <= 45:
                return val
        except ValueError:
            pass
    return 0


def _extract_subjects(text: str) -> list[dict]:
    reqs = []
    seen = set()

    for m in SUBJECT_LEVEL_PATTERN.finditer(text):
        subj = re.sub(r'\s+', ' ', m.group(1).strip()).title()
        try:
            level = int(m.group(2))
        except ValueError:
            continue
        if not (1 <= level <= 7) or subj.lower() in seen:
            continue
        seen.add(subj.lower())
        reqs.append({'subject': subj, 'min_level': level})

    if not reqs:
        for m in SUBJECT_PERCENT_PATTERN.finditer(text):
            subj = re.sub(r'\s+', ' ', m.group(1).strip()).title()
            try:
                pct = int(m.group(2))
            except ValueError:
                continue
            level = _pct_to_level(pct)
            if subj.lower() in seen:
                continue
            seen.add(subj.lower())
            reqs.append({'subject': subj, 'min_level': level})

    return reqs


def _scrape_html_page(url: str, faculty: str, campus: str,
                      session: requests.Session) -> list[ParsedCourse]:
    """Scrape a UFS HTML page, extract programme names + APS from prose text."""
    resp = _fetch(url, session)
    if not resp:
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    # Remove nav/header/footer noise
    for tag in soup(['nav', 'header', 'footer', 'script', 'style', 'aside']):
        tag.decompose()

    main = (soup.find('main') or soup.find('div', id=re.compile(r'content|main', re.I))
            or soup.find('div', class_=re.compile(r'content|main|body', re.I)) or soup)
    text = main.get_text('\n', strip=True)

    # Extract programme names
    courses = []
    seen = set()
    for m in DEGREE_PATTERN.finditer(text):
        name = re.sub(r'\s+', ' ', m.group(0)).strip()
        name = re.sub(r'[,;\.\s]+$', '', name)
        if len(name) < 8 or name.lower() in seen:
            continue
        seen.add(name.lower())

        # Find APS near this occurrence
        start = max(0, m.start() - 100)
        end   = min(len(text), m.end() + 600)
        block = text[start:end]

        aps = _extract_aps(block)
        subjects = _extract_subjects(block)
        duration = _duration_for(name)

        c = ParsedCourse(
            name=name,
            field=classify_field(name + ' ' + faculty),
            level=classify_level(name),
            duration_years=duration,
            min_aps=aps,
            campus=campus,
            subject_requirements=subjects,
            institution_short_name='UFS',
            source_excerpt=f'Faculty: {faculty}',
        )
        courses.append(c)

    logger.info(f'  HTML {faculty}: {len(courses)} programmes')
    return courses


def _scrape_pdf(url: str, faculty: str, campus: str,
                session: requests.Session) -> list[ParsedCourse]:
    """Download a PDF yearbook and extract programme names + APS."""
    try:
        import pdfplumber
    except ImportError:
        logger.warning('pdfplumber not installed — skipping PDF scraping')
        return []

    resp = _fetch(url, session, timeout=60)
    if not resp:
        return []

    logger.info(f'  Parsing PDF ({len(resp.content)//1024}KB): {url.split("/")[-1]}')
    try:
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages_text = []
            for page in pdf.pages[:60]:  # first 60 pages
                t = page.extract_text() or ''
                if t.strip():
                    pages_text.append(t)
            text = '\n'.join(pages_text)
    except Exception as e:
        logger.warning(f'  PDF parse error: {e}')
        return []

    courses = []
    seen = set()
    for m in DEGREE_PATTERN.finditer(text):
        name = re.sub(r'\s+', ' ', m.group(0)).strip()
        name = re.sub(r'[,;\.\s]+$', '', name)
        if len(name) < 8 or name.lower() in seen:
            continue
        seen.add(name.lower())

        start = max(0, m.start() - 100)
        end   = min(len(text), m.end() + 800)
        block = text[start:end]

        aps = _extract_aps(block)
        subjects = _extract_subjects(block)
        duration = _duration_for(name)

        c = ParsedCourse(
            name=name,
            field=classify_field(name + ' ' + faculty),
            level=classify_level(name),
            duration_years=duration,
            min_aps=aps,
            campus=campus,
            subject_requirements=subjects,
            institution_short_name='UFS',
            source_excerpt=f'Faculty: {faculty} (yearbook)',
        )
        courses.append(c)

    logger.info(f'  PDF {faculty}: {len(courses)} programmes')
    return courses


def _duration_for(name: str) -> float:
    name_l = name.lower()
    m = re.search(r'\b(\d)\s*-?\s*(?:year|yr)', name_l)
    if m:
        return float(m.group(1))
    if any(k in name_l for k in ['mbchb', 'medicine and surgery', 'medicine & surgery']):
        return 6.0
    if any(k in name_l for k in ['laws', 'llb', 'pharmacy', 'bpharm', 'education', 'bed',
                                   'occupational therapy', 'physiotherapy', 'optometry',
                                   'nursing', 'music', 'agriculture']):
        return 4.0
    if 'higher certificate' in name_l or 'higher cert' in name_l:
        return 1.0
    if 'advanced certificate' in name_l:
        return 1.0
    if 'diploma' in name_l:
        return 3.0
    return 3.0


def parse_ufs() -> list[ParsedCourse]:
    """Main entry point — scrape all UFS undergraduate programmes."""
    session = _session()
    all_raw: list[ParsedCourse] = []

    # Step 1: Scrape known HTML pages
    for url, faculty, campus in PROGRAMME_PAGES:
        try:
            courses = _scrape_html_page(url, faculty, campus, session)
            all_raw.extend(courses)
        except Exception as e:
            logger.error(f'Error scraping {url}: {e}')

    # Step 2: Try PDF yearbooks
    for url, faculty, campus in PDF_SOURCES:
        try:
            courses = _scrape_pdf(url, faculty, campus, session)
            all_raw.extend(courses)
        except Exception as e:
            logger.error(f'Error parsing PDF {url}: {e}')

    # Step 3: Merge with static seed
    # Key: (normalised_name, campus)
    def _norm(n: str) -> str:
        n = re.sub(r'\s*\(extended\)\s*$', '', n, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', n).lower().strip()

    merged: dict[tuple, ParsedCourse] = {}

    # Add scraped courses
    for c in all_raw:
        key = (_norm(c.name), c.campus)
        if key not in merged:
            merged[key] = c

    # Merge/add seed programmes
    for name, faculty, campus, duration, min_aps, subjects in KNOWN_PROGRAMMES:
        key = (_norm(name), campus)
        if key in merged:
            # Enrich scraped with seed APS/subjects
            if not merged[key].min_aps:
                merged[key].min_aps = min_aps
            if not merged[key].subject_requirements:
                merged[key].subject_requirements = list(subjects)
            merged[key].name = name          # prefer clean seed name
            merged[key].duration_years = duration
        else:
            merged[key] = ParsedCourse(
                name=name,
                field=classify_field(name + ' ' + faculty),
                level=classify_level(name),
                duration_years=duration,
                min_aps=min_aps,
                campus=campus,
                subject_requirements=list(subjects),
                institution_short_name='UFS',
                source_excerpt=f'Faculty: {faculty}',
                description=f'Offered by the Faculty of {faculty} at the University of the Free State.',
            )

    # Step 4: Apply defaults for any still-missing data
    from apps.courses.defaults import default_subjects_for
    result = []
    for c in merged.values():
        if not c.min_aps:
            c.min_aps = _faculty_aps_floor(c.source_excerpt, c.name)
        if not c.subject_requirements:
            c.subject_requirements = default_subjects_for(c.field, c.level)
        result.append(c)

    logger.info(f'UFS total: {len(result)} programmes')
    return result


def _faculty_aps_floor(source: str, name: str) -> int:
    src = (source or '').lower()
    name_l = name.lower()
    if 'health' in src or 'mbchb' in name_l or 'medicine' in name_l:
        return 30
    if 'law' in src or 'llb' in name_l:
        return 30
    if 'natural' in src or 'agriculture' in src or 'natagri' in src:
        return 26
    if 'economic' in src or 'management' in src or 'econ' in src:
        return 24
    if 'education' in src:
        return 28
    if 'humanities' in src:
        return 26
    if 'theology' in src:
        return 22
    return 24


def parse_ufs_url(url: str, institution_short_name: str = 'UFS') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_ufs()
