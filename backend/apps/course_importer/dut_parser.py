"""
DUT (Durban University of Technology) undergraduate programme scraper.

Strategy:
  1. Crawl faculty pages → extract department links.
  2. On each department page, find links to career-leaflet / requirement PDFs.
  3. Parse each PDF (text-layer) for: programme name, NQF level, APS points,
     NSC subject requirements, campus/location, CAO code.
  4. Merge with a static seed list for completeness.

Campuses: Durban (Steve Biko / ML Sultan / City), Midlands (Pietermaritzburg).
"""
import re
import io
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, classify_level, USER_AGENT

logger = logging.getLogger(__name__)

BASE = 'https://www.dut.ac.za'

FACULTY_URLS = [
    f'{BASE}/faculty/accounting_and_informatics/',
    f'{BASE}/faculty/applied_sciences/',
    f'{BASE}/faculty/engineering/',
    f'{BASE}/faculty/health_sciences/',
    f'{BASE}/faculty/management/',
    f'{BASE}/faculty/arts_and_design/',
]

# Known department page URLs (fallback if faculty crawl misses them)
DEPT_URLS = [
    # Accounting & Informatics
    f'{BASE}/faculty/accounting_and_informatics/information_technology/',
    f'{BASE}/faculty/accounting_and_informatics/financial_accounting/',
    f'{BASE}/faculty/accounting_and_informatics/auditing_and_taxation/',
    f'{BASE}/faculty/accounting_and_informatics/information_systems/',
    f'{BASE}/faculty/accounting_and_informatics/management_accounting/',
    f'{BASE}/faculty/accounting_and_informatics/finance_and_information_management/',
    # Applied Sciences
    f'{BASE}/faculty/applied_sciences/biotechnology_and_food_technology/',
    f'{BASE}/faculty/applied_sciences/chemistry/',
    f'{BASE}/faculty/applied_sciences/consumer_sciences_food_and_nutrition/',
    f'{BASE}/faculty/applied_sciences/horticulture/',
    f'{BASE}/faculty/applied_sciences/maritime_studies/',
    f'{BASE}/faculty/applied_sciences/sport_studies/',
    f'{BASE}/faculty/applied_sciences/textile-science-and-apparel-technology/',
    # Engineering
    f'{BASE}/faculty/engineering/mechanical_engineering/',
    f'{BASE}/faculty/engineering/chemical_engineering/',
    f'{BASE}/faculty/engineering/civil_engineering/',
    f'{BASE}/faculty/engineering/civil_engineering_and_geomatics/',
    f'{BASE}/faculty/engineering/electrical_power_engineering/',
    f'{BASE}/faculty/engineering/electronic_and_computer_engineering/',
    f'{BASE}/faculty/engineering/industrial_engineering/',
    f'{BASE}/faculty/engineering/architecture/',
    f'{BASE}/faculty/engineering/construction_management/',
    f'{BASE}/faculty/engineering/town_and_regional_planning/',
    # Health Sciences
    f'{BASE}/faculty/health_sciences/nursing/',
    f'{BASE}/faculty/health_sciences/emergency_medical_care_and_rescue/',
    f'{BASE}/faculty/health_sciences/chiropractic/',
    f'{BASE}/faculty/health_sciences/homoeopathy/',
    f'{BASE}/faculty/health_sciences/dental_sciences/',
    f'{BASE}/faculty/health_sciences/radiography/',
    f'{BASE}/faculty/health_sciences/somatology/',
    f'{BASE}/faculty/health_sciences/environmental_health/',
    f'{BASE}/faculty/health_sciences/medical_laboratory_sciences/',
    f'{BASE}/faculty/health_sciences/optometry/',
    f'{BASE}/faculty/health_sciences/biomedical_technology/',
    # Management
    f'{BASE}/faculty/management/hospitality_and_tourism/',
    f'{BASE}/faculty/management/applied_law/',
    f'{BASE}/faculty/management/human_resource_management/',
    f'{BASE}/faculty/management/marketing_and_retail/',
    f'{BASE}/faculty/management/public_management_and_economics/',
    f'{BASE}/faculty/management/sport_management/',
    # Arts & Design
    f'{BASE}/faculty/arts_and_design/fine-art-and-jewellery-design/',
    f'{BASE}/faculty/arts_and_design/graphic_design/',
    f'{BASE}/faculty/arts_and_design/fashion/',
    f'{BASE}/faculty/arts_and_design/photography/',
    f'{BASE}/faculty/arts_and_design/interior_design/',
    f'{BASE}/faculty/arts_and_design/music/',
]

# Static seed for core programmes (filled from published DUT requirements)
# (name, faculty, campus, duration, min_aps, subjects)
KNOWN_PROGRAMMES = [
    # Applied Sciences
    ('Bachelor of Applied Science in Biotechnology',          'Applied Sciences', 'Durban', 3, 28, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'Life Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Diploma in Biotechnology',                              'Applied Sciences', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    ('Advanced Diploma in Biotechnology',                    'Applied Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Chemistry',                                  'Applied Sciences', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3},{'subject':'English','min_level':3}]),
    ('Advanced Diploma in Chemistry',                        'Applied Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Consumer Science Food and Nutrition',        'Applied Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    ('Diploma in Horticulture',                               'Applied Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':3},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Maritime Studies',                           'Applied Sciences', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3}]),
    ('Diploma in Sport Development',                         'Applied Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    # Engineering
    ('Bachelor of Engineering Technology in Mechanical Engineering',       'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Engineering Technology in Chemical Engineering',         'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Engineering Technology in Civil Engineering',            'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Engineering Technology in Electrical Power Engineering', 'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Engineering Technology in Electronic and Computer Engineering', 'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Engineering Technology in Industrial Engineering',       'Engineering', 'Durban', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4},{'subject':'English','min_level':4}]),
    ('Diploma in Architecture',                              'Engineering', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3},{'subject':'English','min_level':4}]),
    ('Diploma in Civil Engineering',                         'Engineering', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3},{'subject':'English','min_level':3}]),
    ('Diploma in Construction Management',                   'Engineering', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3}]),
    ('Diploma in Quantity Surveying',                        'Engineering', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':3}]),
    ('Diploma in Town and Regional Planning',                'Engineering', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    # Health Sciences
    ('Bachelor of Nursing',                                  'Health Sciences', 'Durban', 4, 28, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':4}]),
    ('Diploma in Emergency Medical Care',                    'Health Sciences', 'Durban', 3, 22, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Chiropractic',                             'Health Sciences', 'Durban', 6, 30, [{'subject':'English','min_level':4},{'subject':'Life Sciences','min_level':5},{'subject':'Mathematics','min_level':4}]),
    ('Bachelor of Homoeopathy',                              'Health Sciences', 'Durban', 5, 28, [{'subject':'English','min_level':4},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':4}]),
    ('Diploma in Dental Technology',                         'Health Sciences', 'Durban', 3, 20, [{'subject':'English','min_level':3},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Dental Assisting',                          'Health Sciences', 'Durban', 2, 18, [{'subject':'English','min_level':3}]),
    ('Bachelor of Health Sciences in Radiography',           'Health Sciences', 'Durban', 4, 28, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Diploma in Somatology',                                'Health Sciences', 'Durban', 3, 20, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    ('Diploma in Environmental Health',                      'Health Sciences', 'Durban', 3, 22, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':3},{'subject':'Mathematics','min_level':3}]),
    ('Bachelor of Medical Laboratory Science',               'Health Sciences', 'Durban', 4, 28, [{'subject':'English','min_level':4},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Bachelor of Optometry',                                'Health Sciences', 'Durban', 4, 30, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':5},{'subject':'Physical Sciences','min_level':4}]),
    ('Diploma in Biomedical Technology',                     'Health Sciences', 'Durban', 3, 22, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':4}]),
    # Management Sciences
    ('Diploma in Catering Management',                       'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':2}]),
    ('Advanced Diploma in Catering Management',              'Management Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Hospitality Management',                    'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Tourism Management',                        'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Advanced Diploma in Tourism Management',               'Management Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Human Resource Management',                 'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Advanced Diploma in Human Resource Management',        'Management Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Marketing',                                 'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Advanced Diploma in Marketing',                        'Management Sciences', 'Durban', 1, 18, [{'subject':'English','min_level':3}]),
    ('Diploma in Public Management',                         'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Sport Management',                          'Management Sciences', 'Durban', 3, 18, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':3}]),
    # Accounting & Informatics
    ('Diploma in Accounting',                                'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4},{'subject':'Accounting','min_level':3}]),
    ('Advanced Diploma in Accounting',                       'Accounting and Informatics', 'Durban', 1, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':3}]),
    ('Diploma in Financial Information Systems',             'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Bachelor of Information and Communication Technology', 'Accounting and Informatics', 'Durban', 3, 24, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Diploma in ICT Applications Development',              'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Diploma in Information Systems',                       'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'English','min_level':4}]),
    ('Diploma in Internal Auditing',                         'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Diploma in Management Accounting',                     'Accounting and Informatics', 'Durban', 3, 18, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    # Arts & Design
    ('Diploma in Fine Art',                                  'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4}]),
    ('Diploma in Graphic Design',                            'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Fashion',                                   'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4}]),
    ('Diploma in Photography',                               'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4}]),
    ('Diploma in Interior Design',                           'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4}]),
    ('Diploma in Music Technology',                          'Arts and Design', 'Durban', 3, 18, [{'subject':'English','min_level':4}]),
    # Midlands campus
    ('Diploma in Civil Engineering',                         'Engineering', 'Midlands', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3}]),
    ('Diploma in Electrical Engineering',                    'Engineering', 'Midlands', 3, 18, [{'subject':'Mathematics','min_level':3},{'subject':'Physical Sciences','min_level':3}]),
    ('Bachelor of Engineering Technology in Civil Engineering', 'Engineering', 'Midlands', 4, 26, [{'subject':'Mathematics','min_level':4},{'subject':'Physical Sciences','min_level':4}]),
    ('Diploma in Human Resource Management',                 'Management Sciences', 'Midlands', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Public Management',                         'Management Sciences', 'Midlands', 3, 18, [{'subject':'English','min_level':4},{'subject':'Mathematics','min_level':3}]),
    ('Diploma in Accounting',                                'Accounting and Informatics', 'Midlands', 3, 18, [{'subject':'Mathematics','min_level':4},{'subject':'English','min_level':4}]),
    ('Bachelor of Nursing',                                  'Health Sciences', 'Midlands', 4, 28, [{'subject':'English','min_level':3},{'subject':'Life Sciences','min_level':4},{'subject':'Mathematics','min_level':4}]),
]

PDF_PROG_PATTERN = re.compile(
    r'\b(Bachelor of (?:Applied Science|Engineering Technology|Health Sciences?|Nursing|'
    r'Chiropractic|Homoeopathy|Optometry|Medical Laboratory Science|'
    r'Information and Communication Technology|[A-Z][A-Za-z\s,&\-]{3,60})'
    r'|BICT\b'
    r'|BAppSc\b'
    r'|BEngTech\b'
    r'|(?:Advanced\s+)?Diploma in [A-Z][A-Za-z\s,&\-]{3,60}'
    r'|Higher Certificate in [A-Z][A-Za-z\s,&\-]{3,60})'
    r'(?=[\s,\.\(\n]|$)',
)

APS_PATTERN = re.compile(
    r'(\d{2})\s*\+?\s*points?\s*(?:\(excl|or\s+more)'
    r'|(?:minimum\s+(?:APS|AP)\s*(?:score\s+)?(?:of\s+)?(\d{2}))',
    re.IGNORECASE,
)

SUBJECT_LEVEL_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical\s+Literacy|Physical\s+Science[s]?|'
    r'Life\s+Science[s]?|English(?:\s+(?:HL|FAL|Home))?|Afrikaans|Accounting|'
    r'Economics|Business\s+Studies|Geography|History|Technical\s+Mathematics|'
    r'Technical\s+Science[s]?|Information\s+Technology|Computer\s+Applications\s+Technology)'
    r'[^.\n]{0,50}?\b(\d)\b(?:\s*(?:rating|level|NSC|or\s+higher))?',
    re.IGNORECASE,
)

CAMPUS_PATTERN = re.compile(r'Location\s*:\s*([^\n\r]+)', re.IGNORECASE)
NQF_PATTERN    = re.compile(r'NQF\s+Level\s*:\s*(\d+)',  re.IGNORECASE)
CAO_PATTERN    = re.compile(r'CAO\s+Code[s]?\s*:\s*(DU-[A-Z]-\w+)', re.IGNORECASE)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def _fetch(url: str, session: requests.Session, timeout: int = 20) -> Optional[requests.Response]:
    try:
        r = session.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r
    except Exception as e:
        logger.debug(f'Fetch error {url}: {e}')
    return None


def _get_dept_links(faculty_url: str, session: requests.Session) -> list[str]:
    """Scrape a faculty page and return department URLs."""
    resp = _fetch(faculty_url, session)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if not href.startswith('http'):
            href = BASE + href if href.startswith('/') else faculty_url + href
        if '/faculty/' in href and href != faculty_url:
            links.add(href.rstrip('/') + '/')
    return list(links)


def _get_pdf_links(dept_url: str, session: requests.Session) -> list[str]:
    """Scrape a department page and return PDF career-leaflet URLs."""
    resp = _fetch(dept_url, session)
    if not resp:
        return []
    soup = BeautifulSoup(resp.text, 'html.parser')
    pdfs = set()
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.lower().endswith('.pdf') and ('career_leaflet' in href or 'wp-content' in href):
            pdfs.add(href)
    return list(pdfs)


def _parse_pdf(url: str, faculty_hint: str, session: requests.Session) -> Optional[ParsedCourse]:
    """Download a PDF and extract a single ParsedCourse from it."""
    try:
        import pdfplumber
    except ImportError:
        return None

    resp = _fetch(url, session, timeout=30)
    if not resp or not resp.content:
        return None

    try:
        with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
            pages = pdf.pages[:6]
            text = '\n'.join(p.extract_text() or '' for p in pages)
    except Exception as e:
        logger.debug(f'PDF parse error {url}: {e}')
        return None

    if not text.strip():
        return None

    # Programme name — first matching pattern in the text
    name = ''
    m = PDF_PROG_PATTERN.search(text)
    if m:
        name = re.sub(r'\s+', ' ', m.group(0)).strip()
        name = re.sub(r'[,;:\s]+$', '', name)

    # Try filename if no match
    if not name or len(name) < 6:
        fname = url.split('/')[-1].replace('.pdf', '').replace('-', ' ').replace('_', ' ')
        fname = re.sub(r'%20', ' ', fname).strip()
        # Rough quality check
        if any(k in fname.lower() for k in ['diploma', 'bachelor', 'certificate', 'bsc', 'beng']):
            name = fname.title()

    if not name or len(name) < 6:
        return None

    # APS / points
    aps = 0
    for aps_m in APS_PATTERN.finditer(text):
        val_str = aps_m.group(1) or aps_m.group(2)
        if val_str:
            try:
                v = int(val_str)
                if 15 <= v <= 45:
                    aps = v
                    break
            except ValueError:
                pass

    # Subject requirements
    subjects = []
    seen_s = set()
    for sm in SUBJECT_LEVEL_PATTERN.finditer(text[:3000]):  # first 3000 chars for reqs page
        subj = re.sub(r'\s+', ' ', sm.group(1)).strip().title()
        try:
            lvl = int(sm.group(2))
        except ValueError:
            continue
        if not (1 <= lvl <= 7) or subj.lower() in seen_s:
            continue
        seen_s.add(subj.lower())
        subjects.append({'subject': subj, 'min_level': lvl})

    # Campus / location
    campus = 'Durban'
    loc_m = CAMPUS_PATTERN.search(text)
    if loc_m:
        loc_text = loc_m.group(1).strip().lower()
        if 'midland' in loc_text or 'pietermaritzburg' in loc_text or 'pmb' in loc_text:
            campus = 'Midlands'

    # NQF level → programme level/type
    nqf_m = NQF_PATTERN.search(text)
    nqf = int(nqf_m.group(1)) if nqf_m else 0

    # Duration
    dur = _duration_for(name, nqf)

    # CAO code
    cao_m = CAO_PATTERN.search(text)
    prog_code = cao_m.group(1) if cao_m else ''

    return ParsedCourse(
        name=name,
        field=classify_field(name + ' ' + faculty_hint),
        level=classify_level(name),
        duration_years=dur,
        min_aps=aps,
        campus=campus,
        subject_requirements=subjects,
        programme_code=prog_code,
        institution_short_name='DUT',
        source_excerpt=f'PDF: {url.split("/")[-1]}',
    )


def _duration_for(name: str, nqf: int = 0) -> float:
    name_l = name.lower()
    m = re.search(r'\b(\d)\s*-?\s*(?:year|yr)', name_l)
    if m:
        return float(m.group(1))
    if 'advanced diploma' in name_l:
        return 1.0
    if 'higher certificate' in name_l:
        return 1.0
    if 'chiropractic' in name_l:
        return 6.0
    if 'homoeopathy' in name_l:
        return 5.0
    if any(k in name_l for k in ['beng', 'engineering technology', 'nursing', 'optometry',
                                   'radiograph', 'medical laboratory', 'dental assisting']):
        return 4.0
    if nqf == 7:
        return 3.0
    if nqf == 6:
        return 3.0
    if 'diploma' in name_l:
        return 3.0
    return 3.0


def parse_dut() -> list[ParsedCourse]:
    """Main entry point — scrape all DUT undergraduate programmes."""
    session = _session()
    pdf_urls: set[str] = set()
    seen_depts: set[str] = set()

    # Step 1: Crawl faculties → departments → collect PDF links
    all_dept_urls = set(DEPT_URLS)
    for fac_url in FACULTY_URLS:
        dept_links = _get_dept_links(fac_url, session)
        all_dept_urls.update(dept_links)

    for dept_url in sorted(all_dept_urls):
        if dept_url in seen_depts:
            continue
        seen_depts.add(dept_url)
        pdfs = _get_pdf_links(dept_url, session)
        pdf_urls.update(pdfs)

    logger.info(f'Found {len(pdf_urls)} PDF career leaflets')

    # Step 2: Parse each PDF
    pdf_courses: list[ParsedCourse] = []
    for pdf_url in sorted(pdf_urls):
        # Infer faculty from URL path
        fac_hint = 'DUT'
        url_l = pdf_url.lower()
        if 'fmsc' in url_l or 'management' in url_l or 'catering' in url_l or 'tourism' in url_l:
            fac_hint = 'Management Sciences'
        elif 'fas' in url_l or 'applied' in url_l or 'biotech' in url_l or 'chem' in url_l:
            fac_hint = 'Applied Sciences'
        elif 'ebe' in url_l or 'engineer' in url_l or 'mechanic' in url_l or 'civil' in url_l:
            fac_hint = 'Engineering'
        elif 'hsc' in url_l or 'health' in url_l or 'nursing' in url_l:
            fac_hint = 'Health Sciences'
        elif 'fai' in url_l or 'account' in url_l or 'ict' in url_l or 'informat' in url_l:
            fac_hint = 'Accounting and Informatics'
        elif 'art' in url_l or 'design' in url_l or 'graphic' in url_l:
            fac_hint = 'Arts and Design'

        course = _parse_pdf(pdf_url, fac_hint, session)
        if course and len(course.name) > 5:
            pdf_courses.append(course)

    logger.info(f'Extracted {len(pdf_courses)} courses from PDFs')

    # Step 3: Merge PDF courses + static seed
    def _norm(n: str) -> str:
        n = re.sub(r'\s+', ' ', n).lower().strip()
        n = re.sub(r'\s*\(extended\)$', '', n)
        return n

    merged: dict[tuple, ParsedCourse] = {}

    for c in pdf_courses:
        key = (_norm(c.name), c.campus)
        if key not in merged:
            merged[key] = c

    for name, faculty, campus, duration, min_aps, subjects in KNOWN_PROGRAMMES:
        key = (_norm(name), campus)
        if key in merged:
            if not merged[key].min_aps:
                merged[key].min_aps = min_aps
            if not merged[key].subject_requirements:
                merged[key].subject_requirements = list(subjects)
            merged[key].name = name
        else:
            merged[key] = ParsedCourse(
                name=name,
                field=classify_field(name + ' ' + faculty),
                level=classify_level(name),
                duration_years=duration,
                min_aps=min_aps,
                campus=campus,
                subject_requirements=list(subjects),
                institution_short_name='DUT',
                source_excerpt=f'Faculty: {faculty}',
                description=f'Offered by the Faculty of {faculty} at Durban University of Technology.',
            )

    # Step 4: Apply APS floor for anything still missing
    from apps.courses.defaults import default_subjects_for
    result = []
    for c in merged.values():
        if not c.min_aps:
            c.min_aps = _aps_floor(c.name)
        if not c.subject_requirements:
            c.subject_requirements = default_subjects_for(c.field, c.level)
        result.append(c)

    logger.info(f'DUT total: {len(result)} programmes')
    return result


def _aps_floor(name: str) -> int:
    name_l = name.lower()
    if any(k in name_l for k in ['chiropractic', 'optometry', 'medicine']):
        return 30
    if any(k in name_l for k in ['bachelor of applied science', 'bappsc', 'bengtech',
                                   'engineering technology', 'nursing', 'radiograph',
                                   'medical lab', 'homoeopathy']):
        return 26
    if 'bachelor' in name_l and 'advanced diploma' not in name_l:
        return 24
    return 18  # Diploma / Advanced Diploma default


def parse_dut_url(url: str, institution_short_name: str = 'DUT') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_dut()
