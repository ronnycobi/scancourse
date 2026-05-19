"""
Mangosuthu University of Technology (MUT) undergraduate programme scraper.

Source: https://www.mut.ac.za — department pages

Strategy:
  MUT has one campus (Umlazi, Durban South) and ~25 entry-level programmes
  across three faculties. The website lists programmes per department page with
  varying levels of APS/subject detail. We use a verified static seed (cross-
  checked against each department page) supplemented by a lightweight web
  scraper that picks up any APS values embedded in live department pages.

Campus: Umlazi (Durban).
"""
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.mut.ac.za'

# All known undergraduate entry-level programmes at MUT (2026)
# ECP variants are collapsed into the standard programme (same APS / subjects).
# Advanced Diplomas are included (level='advanced_diploma', min_aps=0).
SEED: list[dict] = [
    # ── Faculty of Applied and Health Sciences ────────────────────────────────
    {
        'name':           'Diploma in Agriculture: Crop Production',
        'field':          'agriculture',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Life Sciences',      'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 3},
                           {'subject': 'Physical Sciences',  'min_level': 3}],
        'code':           'CROPDP',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Diploma in Agriculture: Animal Production',
        'field':          'agriculture',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Life Sciences',      'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 3},
                           {'subject': 'Physical Sciences',  'min_level': 3}],
        'code':           'ANIPEC',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Advanced Diploma in Agriculture: Animal Production',
        'field':          'agriculture',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           'ADVAGA',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Bachelor of Health Sciences in Medical Laboratory Science',
        'field':          'health',
        'level':          'degree',
        'duration_years': 4.0,
        'min_aps':        28,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Life Sciences',      'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Bachelor of Science in Environmental Health',
        'field':          'health',
        'level':          'degree',
        'duration_years': 4.0,
        'min_aps':        28,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Life Sciences',      'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Diploma in Information Technology',
        'field':          'it',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        24,
        'subjects':       [{'subject': 'English',     'min_level': 3},
                           {'subject': 'Mathematics',  'min_level': 3}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Advanced Diploma in Information and Communication Technology in Applications Development',
        'field':          'it',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Diploma in Analytical Chemistry',
        'field':          'science',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Advanced Diploma in Chemistry',
        'field':          'science',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           'ADVACH',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Diploma in Nature Conservation',
        'field':          'science',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        28,
        'subjects':       [{'subject': 'English',       'min_level': 4},
                           {'subject': 'Life Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Bachelor of Applied Science in Nature Conservation',
        'field':          'science',
        'level':          'degree',
        'duration_years': 3.0,
        'min_aps':        32,
        'subjects':       [{'subject': 'English',       'min_level': 5},
                           {'subject': 'Life Sciences',  'min_level': 5},
                           {'subject': 'Mathematics',    'min_level': 3}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Advanced Diploma in Nature Conservation',
        'field':          'science',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Diploma in Community Extension',
        'field':          'social_sciences',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Life Sciences',      'min_level': 4}],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },
    {
        'name':           'Advanced Diploma in Agricultural Extension and Community Development',
        'field':          'agriculture',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Applied and Health Sciences',
    },

    # ── Faculty of Engineering ────────────────────────────────────────────────
    {
        'name':           'Diploma in Chemical Engineering',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Advanced Diploma in Chemical Engineering',
        'field':          'engineering',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Civil Engineering',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Surveying',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Electrical Engineering',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           'ELENDI',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Mechanical Engineering',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',           'min_level': 4},
                           {'subject': 'Mathematics',        'min_level': 4},
                           {'subject': 'Physical Sciences',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Advanced Diploma in Mechanical Engineering',
        'field':          'engineering',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Construction Management',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',     'min_level': 4},
                           {'subject': 'Mathematics',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },
    {
        'name':           'Diploma in Quantity Surveying',
        'field':          'engineering',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English',     'min_level': 4},
                           {'subject': 'Mathematics',  'min_level': 4}],
        'code':           '',
        'faculty':        'Engineering',
    },

    # ── Faculty of Management Sciences ────────────────────────────────────────
    {
        'name':           'Diploma in Accounting',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        25,
        'subjects':       [{'subject': 'English',     'min_level': 5},
                           {'subject': 'Accounting',   'min_level': 4},
                           {'subject': 'Mathematics',  'min_level': 4}],
        'code':           'ACOECP',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Public Finance and Accounting',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        25,
        'subjects':       [{'subject': 'English',    'min_level': 5},
                           {'subject': 'Accounting',  'min_level': 4},
                           {'subject': 'Mathematics', 'min_level': 4}],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Local Government Finance',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        22,
        'subjects':       [{'subject': 'English',    'min_level': 4},
                           {'subject': 'Mathematics', 'min_level': 3}],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Accounting',
        'field':          'business',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Cost and Management Accounting',
        'field':          'business',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Human Resource Management',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        25,
        'subjects':       [{'subject': 'English',     'min_level': 4},
                           {'subject': 'Accounting',   'min_level': 3},
                           {'subject': 'Mathematics',  'min_level': 3}],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Human Resource Management',
        'field':          'business',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Marketing',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        25,
        'subjects':       [{'subject': 'English',     'min_level': 4},
                           {'subject': 'Mathematics',  'min_level': 4}],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Marketing',
        'field':          'business',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Office Management and Technology',
        'field':          'business',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        20,
        'subjects':       [{'subject': 'English', 'min_level': 3}],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Office Management and Technology',
        'field':          'business',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           '',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Diploma in Public Management',
        'field':          'social_sciences',
        'level':          'diploma',
        'duration_years': 3.0,
        'min_aps':        25,
        'subjects':       [{'subject': 'English', 'min_level': 3}],
        'code':           'PUBLAS',
        'faculty':        'Management Sciences',
    },
    {
        'name':           'Advanced Diploma in Public Management',
        'field':          'social_sciences',
        'level':          'advanced_diploma',
        'duration_years': 1.0,
        'min_aps':        0,
        'subjects':       [],
        'code':           'ADVPUM',
        'faculty':        'Management Sciences',
    },
]

# Department pages to scrape for live APS updates
DEPT_URLS = [
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-agriculture/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-biomedical-sciences-2/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-chemistry/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-community-extension/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-environmental-health-2/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-information-and-communication-technology/',
    f'{BASE_URL}/faculty-of-applied-and-health-sciences/department-of-nature-conservation/',
    f'{BASE_URL}/faculties/department-of-construction-management-quantity-surveying/',
    f'{BASE_URL}/faculties/department-of-civil-engineering-and-survey/',
    f'{BASE_URL}/faculties/department-of-chemical-engineering/',
    f'{BASE_URL}/faculties/department-of-electrical-engineering/',
    f'{BASE_URL}/faculties/department-of-mechanical-engineering/',
    f'{BASE_URL}/faculty-of-management-sciences/department-of-accounting-and-law/',
    f'{BASE_URL}/faculty-of-management-sciences/department-of-human-resource-management/',
    f'{BASE_URL}/faculty-of-management-sciences/department-of-marketing/',
    f'{BASE_URL}/faculty-of-management-sciences/department-of-office-technology/',
    f'{BASE_URL}/faculty-of-management-sciences/department-of-public-administration-and-economics/',
]

# Regex to find APS in department page text
APS_RE = re.compile(
    r'(?:minimum\s+(?:of\s+)?|APS\s*(?:of\s*|score\s*)?)(\d{2})\s*(?:points?|APS)',
    re.IGNORECASE,
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _fetch(url: str, session: requests.Session) -> Optional[BeautifulSoup]:
    try:
        r = session.get(url, timeout=20)
        if r.status_code == 200:
            return BeautifulSoup(r.text, 'html.parser')
    except Exception as e:
        logger.debug(f'Fetch error {url}: {e}')
    return None


def _scrape_dept_aps(session: requests.Session) -> dict[str, int]:
    """
    Scrape department pages for APS overrides keyed by lower-cased programme
    name fragment (first 6 significant words).
    """
    aps_map: dict[str, int] = {}
    for url in DEPT_URLS:
        soup = _fetch(url, session)
        if not soup:
            continue
        text = soup.get_text('\n', strip=True)
        for m in APS_RE.finditer(text):
            try:
                v = int(m.group(1))
                if 15 <= v <= 45:
                    # Find surrounding programme name (look backwards ~200 chars)
                    start = max(0, m.start() - 200)
                    context = text[start:m.start()].lower()
                    for entry in SEED:
                        key = entry['name'].lower()
                        # Match if any 3-word fragment of the name appears in context
                        words = key.split()[:6]
                        if len(words) >= 3 and ' '.join(words[:3]) in context:
                            aps_map[key] = v
                            break
            except ValueError:
                pass
    return aps_map


def parse_mut() -> list[ParsedCourse]:
    """Return all MUT undergraduate programmes as ParsedCourse objects."""
    session = _session()

    # Attempt live APS enrichment from department pages
    logger.info('MUT: scraping department pages for APS overrides ...')
    live_aps = _scrape_dept_aps(session)
    logger.info(f'MUT: found {len(live_aps)} live APS overrides')

    courses: list[ParsedCourse] = []
    for entry in SEED:
        name  = entry['name']
        level = entry['level']
        field = entry.get('field') or classify_field(name + ' ' + entry.get('faculty', ''))

        # Apply live APS if found, else fall back to seed
        aps = live_aps.get(name.lower(), entry['min_aps'])

        subj = entry.get('subjects') or []
        if not subj and level not in ('advanced_diploma',):
            from apps.courses.defaults import default_subjects_for
            subj = default_subjects_for(field, level)

        courses.append(ParsedCourse(
            name=name,
            field=field,
            level=level,
            duration_years=entry.get('duration_years', 3.0),
            min_aps=aps,
            campus='Umlazi',
            subject_requirements=subj,
            programme_code=entry.get('code', ''),
            institution_short_name='MUT',
            source_excerpt=f"Faculty: {entry.get('faculty', '')} | Code: {entry.get('code', '')}",
        ))

    logger.info(f'MUT total: {len(courses)} programmes')
    return courses


def parse_mut_url(url: str, institution_short_name: str = 'MUT') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_mut()
