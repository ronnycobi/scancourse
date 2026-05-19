"""
Pure-Python heuristic parser for SA university course data.

Extracts programmes from PDFs and URLs using:
- BeautifulSoup for HTML parsing
- PyPDF2 for PDF text extraction
- Regex patterns tuned to SA university prospectus conventions

NO AI. NO external APIs. Works offline once the page/PDF is fetched.
"""
import io
import re
import logging
from dataclasses import dataclass, field as dc_field, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
)


# ════════════════════════════════════════════════════════════════
# Output schema
# ════════════════════════════════════════════════════════════════

@dataclass
class ParsedCourse:
    name: str = ''
    field: str = 'other'
    level: str = 'degree'
    duration_years: Optional[float] = None
    fees_per_year: Optional[float] = None
    min_aps: int = 0
    description: str = ''
    career_opportunities: str = ''
    institution_short_name: str = ''
    campus: str = ''
    programme_code: str = ''
    application_deadline: str = ''
    subject_requirements: list = dc_field(default_factory=list)
    source_excerpt: str = ''

    def to_dict(self) -> dict:
        return asdict(self)


# ════════════════════════════════════════════════════════════════
# Heuristic patterns — tuned to SA university prospectus conventions
# ════════════════════════════════════════════════════════════════

# Programme name detector — SA-specific qualification prefixes
# We stop at words that signal "no longer part of the name"
NAME_STOP = r'(?=\s+(?:Duration|APS|Minimum|Closes?|Fees?|R\d|[Mm]athematics|English|Subject|3\s*year|4\s*year|2\s*year|Faculty|\(NQF|\d|$|\n)|[\.;:])'

PROGRAMME_NAME_PATTERNS = [
    (rf'(?:Bachelor of [A-Z][\w\s,&\-]{{3,80}}?){NAME_STOP}', 'degree'),
    (rf'(?:BCom|B\.Com\.?|Bcom)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'degree'),
    (rf'(?:BSc|B\.Sc\.?|Bsc)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'degree'),
    (rf'(?:BA|B\.A\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'degree'),
    (rf'(?:BEng|B\.Eng\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'degree'),
    (rf'(?:BEd|B\.Ed\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'degree'),
    (rf'(?:BTech|B\.Tech\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'advanced_diploma'),
    (r'\bLLB\b', 'degree'),
    (r'\bMBChB\b', 'degree'),
    (rf'(?:Advanced Diploma|Adv\.?\s*Dip\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'advanced_diploma'),
    (rf'(?:Diploma)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'diploma'),
    (rf'(?:Higher Certificate|Adv\.?\s*Cert\.?)\s+(?:in\s+)?[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'certificate'),
    (r'(?:National Certificate)\s*(?:\(Vocational\)|\(NC\(V\)\))?', 'nc_v'),
    (rf'\bN[1-6]\s+[A-Z][\w\s,&\-]{{2,60}}?{NAME_STOP}', 'n1_n6'),
]

# Field classifier — keyword maps to field code
FIELD_KEYWORDS = {
    'engineering': ['engineering', 'engineer', 'mechanical', 'electrical', 'civil', 'industrial', 'chemical engineering', 'mechatronic'],
    'health': ['medicine', 'medical', 'mbchb', 'nursing', 'health', 'pharmacy', 'physiotherapy', 'occupational therapy', 'dentistry', 'dietetic', 'biokinetic', 'optometry', 'audiology', 'radiography'],
    'business': ['accounting', 'commerce', 'bcom', 'business', 'finance', 'economics', 'marketing', 'human resource', 'logistics', 'supply chain', 'management', 'taxation', 'auditing'],
    'law': ['law', 'llb', 'legal', 'jurisprudence', 'forensic'],
    'humanities': ['humanities', 'sociology', 'psychology', 'political', 'history', 'geography', 'philosophy', 'religion', 'languages', 'linguistics', 'social work', 'anthropology', 'communication', 'media', 'journalism'],
    'science': ['biology', 'chemistry', 'physics', 'mathematics', 'statistics', 'environmental', 'biotechnology', 'biochemistry', 'microbiology', 'zoology', 'botany', 'astronomy', 'geology', 'oceanograph'],
    'education': ['education', 'teaching', 'bed', 'b.ed', 'foundation phase', 'intermediate phase', 'fet', 'sed'],
    'arts': ['arts', 'fine arts', 'graphic design', 'visual', 'music', 'theatre', 'drama', 'fashion', 'jewellery', 'film', 'photography', 'animation'],
    'agriculture': ['agriculture', 'agricultural', 'agri', 'horticulture', 'forestry', 'farm', 'crop'],
    'ict': ['computer science', 'information technology', 'computing', 'software', 'data science', 'informatics', 'cybersecurity', 'network', 'database administr'],
    'built_environment': ['architecture', 'construction', 'quantity surveying', 'town planning', 'urban planning', 'built environment', 'real estate', 'property'],
}

# APS — "APS: 28", "APS score 28", "Minimum APS of 28", "APS = 28"
APS_PATTERN = re.compile(
    r'(?:minimum\s+)?aps\s*(?:score|requirement|of)?\s*[:\-=]?\s*(\d{1,2})\b',
    re.IGNORECASE,
)

# Duration — "3 years", "3-year", "Duration: 3 years"
DURATION_PATTERN = re.compile(
    r'\b(\d(?:[.,]\d)?)\s*[\-]?\s*(?:year|yr)s?\b',
    re.IGNORECASE,
)

# Fees — "R65,000", "R 65 000", "R65 000.00 per annum"
FEES_PATTERN = re.compile(
    r'R\s*([\d\s,\.]{4,12})\s*(?:per\s+(?:annum|year)|p\.?a\.?|/year|year)',
    re.IGNORECASE,
)

# Subject requirements — only match when "Level" is explicit (or a % follows)
# This avoids false positives from course names like "Diploma in Information Technology 3"
SUBJECT_REQ_PATTERN = re.compile(
    r'(Mathematics(?:\s+Literacy)?|Mathematical Literacy|English(?:\s*HL|\s*FAL)?|'
    r'Afrikaans(?:\s*HL|\s*FAL)?|Physical Sciences?|Life Sciences?|'
    r'Geography|History|Accounting|Economics|Business Studies|'
    r'Information Technology|Computer Applications Technology)'
    r'\s*[:\-]?\s*Level\s+(\d)',
    re.IGNORECASE,
)

# Application deadline — "Closes 30 September 2025", "Application closing date: 30 September 2025"
DEADLINE_PATTERN = re.compile(
    r'(?:clos(?:es|ing)|deadline|application\s+(?:date|closes))[\s:]+(\d{1,2}\s+[A-Z][a-z]+\s+\d{4})',
    re.IGNORECASE,
)


# ════════════════════════════════════════════════════════════════
# Field/level classifiers
# ════════════════════════════════════════════════════════════════

def classify_field(text: str) -> str:
    """Best-guess field code based on keyword matches in the text."""
    blob = text.lower()
    scores = {}
    for field_code, keywords in FIELD_KEYWORDS.items():
        score = sum(blob.count(kw) for kw in keywords)
        if score:
            scores[field_code] = score
    if not scores:
        return 'other'
    return max(scores, key=scores.get)


def classify_level(programme_name: str) -> str:
    name_lower = programme_name.lower()
    if 'phd' in name_lower or 'doctorate' in name_lower or 'doctoral' in name_lower:
        return 'phd'
    if 'master' in name_lower or 'meng' in name_lower or 'mcom' in name_lower or 'msc' in name_lower:
        return 'masters'
    if 'honours' in name_lower or 'hons' in name_lower:
        return 'honours'
    if 'btech' in name_lower or 'b.tech' in name_lower or 'advanced diploma' in name_lower:
        return 'advanced_diploma'
    if 'advdip' in name_lower or 'adv dip' in name_lower or 'adv.dip' in name_lower:
        return 'advanced_diploma'
    if 'postgraduate diploma' in name_lower or 'pgdip' in name_lower or 'pg dip' in name_lower:
        return 'honours'  # PGDip is NQF level 8, same as Honours
    if 'diploma' in name_lower:
        return 'diploma'
    if 'higher certificate' in name_lower or 'advanced certificate' in name_lower:
        return 'certificate'
    if re.search(r'\bn[1-6]\b', name_lower):
        return 'n1_n6'
    if 'nc(v)' in name_lower or 'national certificate (vocational)' in name_lower:
        return 'nc_v'
    return 'degree'


# ════════════════════════════════════════════════════════════════
# Programme block detection
# ════════════════════════════════════════════════════════════════

def find_programme_names(text: str) -> list[tuple[int, str]]:
    """
    Scan text for likely programme name occurrences.
    Returns list of (start_index, full_match) tuples, deduplicated.
    """
    found = []
    seen_normalised = set()

    # Match degree-prefix patterns
    for pattern, _ in PROGRAMME_NAME_PATTERNS:
        for m in re.finditer(pattern, text):
            full = m.group(0).strip()
            if len(full) < 5:
                continue
            # Cleanup trailing crap
            full = re.sub(r'\s+', ' ', full)
            full = re.sub(r'[,\.;:\s]+$', '', full)
            # Limit name length
            if len(full) > 200:
                continue
            normalised = full.lower()
            if normalised in seen_normalised:
                continue
            seen_normalised.add(normalised)
            found.append((m.start(), full))

    found.sort(key=lambda x: x[0])
    return found


def extract_block_around(text: str, position: int, before: int = 30, after: int = 600) -> str:
    """Get a chunk of text around a programme name to look for its details."""
    start = max(0, position - before)
    end = min(len(text), position + after)
    return text[start:end]


def parse_programme_block(name: str, block: str) -> ParsedCourse:
    """Extract structured fields from a text block surrounding a programme name."""
    course = ParsedCourse(name=name)
    course.level = classify_level(name)
    course.field = classify_field(name + ' ' + block[:300])

    # APS
    aps_match = APS_PATTERN.search(block)
    if aps_match:
        try:
            course.min_aps = int(aps_match.group(1))
        except (ValueError, IndexError):
            pass

    # Duration
    dur_match = DURATION_PATTERN.search(block)
    if dur_match:
        try:
            course.duration_years = float(dur_match.group(1).replace(',', '.'))
        except (ValueError, IndexError):
            pass

    # Fees
    fees_match = FEES_PATTERN.search(block)
    if fees_match:
        try:
            raw = fees_match.group(1).replace(' ', '').replace(',', '').replace('.', '')
            course.fees_per_year = float(raw[:8])
        except (ValueError, IndexError):
            pass

    # Subject requirements
    seen_subjects = set()
    for sm in SUBJECT_REQ_PATTERN.finditer(block):
        subj = sm.group(1).strip().title()
        try:
            level = int(sm.group(2))
        except ValueError:
            continue
        if subj.lower() in seen_subjects or not (1 <= level <= 7):
            continue
        seen_subjects.add(subj.lower())
        course.subject_requirements.append({'subject': subj, 'min_level': level})

    # Deadline
    dl_match = DEADLINE_PATTERN.search(block)
    if dl_match:
        from datetime import datetime
        try:
            d = datetime.strptime(dl_match.group(1), '%d %B %Y').date()
            course.application_deadline = d.isoformat()
        except ValueError:
            pass

    # Description — first sentence after the name
    after_name = block[block.find(name) + len(name):] if name in block else block
    sentences = re.split(r'(?<=[.!?])\s+', after_name.strip())
    desc_parts = []
    for s in sentences[:3]:
        s = s.strip()
        if 30 < len(s) < 400 and not s.startswith(('APS', 'Duration', 'Closes', 'R')):
            desc_parts.append(s)
            if len(' '.join(desc_parts)) > 200:
                break
    course.description = ' '.join(desc_parts)[:1000]
    course.source_excerpt = block[:200].replace('\n', ' ')

    return course


# ════════════════════════════════════════════════════════════════
# Source fetchers
# ════════════════════════════════════════════════════════════════

def fetch_url_text(url: str, timeout: int = 30) -> str:
    """Fetch a URL and return clean text."""
    logger.info(f'Fetching {url}')
    resp = requests.get(url, timeout=timeout, headers={'User-Agent': USER_AGENT})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'iframe', 'noscript']):
        tag.decompose()
    return soup.get_text('\n', strip=True)


def read_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF given as bytes."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages_text = []
    for i, page in enumerate(reader.pages):
        try:
            pages_text.append(page.extract_text() or '')
        except Exception as e:
            logger.warning(f'Page {i+1} read error: {e}')
    return '\n\n'.join(pages_text)


# ════════════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════════════

def parse_text(text: str, institution_short_name: str = '') -> list[ParsedCourse]:
    """Run the heuristic parser on a chunk of text."""
    if not text:
        return []
    matches = find_programme_names(text)
    courses = []
    seen_names = set()
    for pos, name in matches:
        normalised = re.sub(r'\s+', ' ', name).lower().strip()
        if normalised in seen_names:
            continue
        seen_names.add(normalised)

        block = extract_block_around(text, pos)
        course = parse_programme_block(name, block)
        course.institution_short_name = institution_short_name
        courses.append(course)
    return courses


def parse_url(url: str, institution_short_name: str = '') -> list[ParsedCourse]:
    """Dispatch URL parsing — institution-specific crawlers for UP/Wits, generic fallback otherwise."""
    inst_upper = (institution_short_name or '').upper()
    url_lower = (url or '').lower()

    if inst_upper == 'UP' or 'up.ac.za' in url_lower:
        from .up_parser import parse_up_url
        return parse_up_url(url, institution_short_name or 'UP')

    if inst_upper == 'WITS' or 'wits.ac.za' in url_lower:
        from .wits_parser import parse_wits_url
        return parse_wits_url(url, institution_short_name or 'Wits')

    if inst_upper == 'UCT' or 'uct.ac.za' in url_lower:
        from .uct_parser import parse_uct_url
        return parse_uct_url(url, institution_short_name or 'UCT')

    if inst_upper == 'SU' or 'sun.ac.za' in url_lower or 'su.ac.za' in url_lower:
        from .su_parser import parse_su_url
        return parse_su_url(url, institution_short_name or 'SU')

    if inst_upper == 'UKZN' or 'ukzn.ac.za' in url_lower:
        from .ukzn_parser import parse_ukzn_url
        return parse_ukzn_url(url, institution_short_name or 'UKZN')

    if inst_upper == 'NMU' or 'mandela.ac.za' in url_lower:
        from .nmu_parser import parse_nmu_url
        return parse_nmu_url(url, institution_short_name or 'NMU')

    if inst_upper == 'NWU' or 'nwu.ac.za' in url_lower or 'studies.nwu.ac.za' in url_lower:
        from .nwu_parser import parse_nwu_url
        return parse_nwu_url(url, institution_short_name or 'NWU')

    if inst_upper == 'RHODES' or 'ru.ac.za' in url_lower:
        from .rhodes_parser import parse_rhodes_url
        return parse_rhodes_url(url, institution_short_name or 'Rhodes')

    if inst_upper == 'UWC' or 'uwc.ac.za' in url_lower:
        from .uwc_parser import parse_uwc_url
        return parse_uwc_url(url, institution_short_name or 'UWC')

    if inst_upper == 'UFS' or 'ufs.ac.za' in url_lower:
        from .ufs_parser import parse_ufs_url
        return parse_ufs_url(url, institution_short_name or 'UFS')

    if inst_upper == 'DUT' or 'dut.ac.za' in url_lower:
        from .dut_parser import parse_dut_url
        return parse_dut_url(url, institution_short_name or 'DUT')

    if inst_upper == 'CPUT' or 'cput.ac.za' in url_lower:
        from .cput_parser import parse_cput_url
        return parse_cput_url(url, institution_short_name or 'CPUT')

    if inst_upper == 'TUT' or 'tut.ac.za' in url_lower:
        from .tut_parser import parse_tut_url
        return parse_tut_url(url, institution_short_name or 'TUT')

    if inst_upper == 'MUT' or 'mut.ac.za' in url_lower:
        from .mut_parser import parse_mut_url
        return parse_mut_url(url, institution_short_name or 'MUT')

    if inst_upper == 'VUT' or 'vut.ac.za' in url_lower:
        from .vut_parser import parse_vut_url
        return parse_vut_url(url, institution_short_name or 'VUT')

    if inst_upper == 'WSU' or 'wsu.ac.za' in url_lower:
        from .wsu_parser import parse_wsu_url
        return parse_wsu_url(url, institution_short_name or 'WSU')

    if inst_upper == 'UFH' or 'ufh.ac.za' in url_lower:
        from .ufh_parser import parse_ufh_url
        return parse_ufh_url(url, institution_short_name or 'UFH')

    if inst_upper == 'SPU' or 'spu.ac.za' in url_lower:
        from .spu_parser import parse_spu_url
        return parse_spu_url(url, institution_short_name or 'SPU')

    if inst_upper == 'UNIZULU' or 'unizulu.ac.za' in url_lower:
        from .unizulu_parser import parse_unizulu_url
        return parse_unizulu_url(url, institution_short_name or 'UniZulu')

    if inst_upper == 'UL' or 'ul.ac.za' in url_lower:
        from .ul_parser import parse_ul_url
        return parse_ul_url(url, institution_short_name or 'UL')

    if inst_upper == 'UMP' or 'ump.ac.za' in url_lower:
        from .ump_parser import parse_ump_url
        return parse_ump_url(url, institution_short_name or 'UMP')

    if inst_upper == 'CUT' or 'cut.ac.za' in url_lower:
        from .cut_parser import parse_cut_url
        return parse_cut_url(url, institution_short_name or 'CUT')

    if inst_upper == 'UNIVEN' or 'univen.ac.za' in url_lower:
        from .univen_parser import parse_univen_url
        return parse_univen_url(url, institution_short_name or 'UNIVEN')

    if inst_upper == 'SMU' or 'smu.ac.za' in url_lower:
        from .smu_parser import parse_smu_url
        return parse_smu_url(url, institution_short_name or 'SMU')

    if inst_upper == 'UNISA' or 'unisa.ac.za' in url_lower:
        from .unisa_parser import parse_unisa_url
        return parse_unisa_url(url, institution_short_name or 'UNISA')

    text = fetch_url_text(url)
    return parse_text(text, institution_short_name)


def detect_institution(text: str) -> str:
    """Auto-detect the SA university based on text content."""
    blob = text.lower()
    fingerprints = {
        'UJ':    ['university of johannesburg', 'uj.ac.za'],
        'UCT':   ['university of cape town', 'uct.ac.za'],
        'Wits':  ['witwatersrand', 'wits.ac.za'],
        'UP':    ['university of pretoria', 'up.ac.za'],
        'SU':    ['stellenbosch', 'sun.ac.za'],
        'UKZN':  ['kwazulu-natal', 'ukzn.ac.za'],
        'NMU':   ['nelson mandela university', 'mandela.ac.za'],
        'NWU':    ['north-west university', 'nwu.ac.za', 'studies.nwu.ac.za'],
        'Rhodes': ['rhodes university', 'ru.ac.za'],
        'UWC':    ['university of the western cape', 'uwc.ac.za'],
        'UFS':    ['university of the free state', 'ufs.ac.za'],
        'DUT':    ['durban university of technology', 'dut.ac.za'],
        'CPUT':   ['cape peninsula university of technology', 'cput.ac.za'],
        'TUT':   ['tshwane university of technology', 'tut.ac.za'],
        'MUT':   ['mangosuthu university of technology', 'mut.ac.za'],
        'VUT':   ['vaal university of technology', 'vut.ac.za'],
        'WSU':   ['walter sisulu university', 'wsu.ac.za'],
        'UFH':   ['university of fort hare', 'ufh.ac.za'],
        'SPU':     ['sol plaatje university', 'spu.ac.za'],
        'UniZulu': ['university of zululand', 'unizulu.ac.za'],
        'UL':      ['university of limpopo', 'ul.ac.za'],
        'UMP':     ['university of mpumalanga', 'ump.ac.za'],
        'CUT':     ['central university of technology', 'cut.ac.za'],
        'UNIVEN':  ['university of venda', 'univen.ac.za'],
        'SMU':     ['sefako makgatho', 'smu.ac.za'],
        'UNISA':   ['university of south africa', 'unisa.ac.za'],
        'CPUT':    ['cape peninsula university', 'cput.ac.za'],
    }
    for short, markers in fingerprints.items():
        if any(m in blob for m in markers):
            return short
    return ''


def parse_pdf_bytes(pdf_bytes: bytes, institution_short_name: str = '') -> list[ParsedCourse]:
    """
    Dispatch to institution-specific parser if we have one, else use the generic regex parser.
    If no institution given, try to auto-detect from the PDF content.
    """
    inst_upper = (institution_short_name or '').upper()

    # Auto-detect if not provided
    if not inst_upper:
        # Read just the first few pages of text for fingerprinting
        try:
            sample_text = read_pdf_text(pdf_bytes)[:8000]
            detected = detect_institution(sample_text)
            if detected:
                logger.info(f'Auto-detected institution: {detected}')
                inst_upper = detected.upper()
                institution_short_name = detected
        except Exception as e:
            logger.warning(f'Auto-detect failed: {e}')

    if inst_upper == 'UJ':
        from .uj_parser import parse_uj_pdf
        return parse_uj_pdf(pdf_bytes, institution_short_name or 'UJ')

    # Generic fallback for unknown institutions
    text = read_pdf_text(pdf_bytes)
    return parse_text(text, institution_short_name)
