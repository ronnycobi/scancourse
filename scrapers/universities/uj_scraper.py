"""
UJ (University of Johannesburg) course scraper.

UJ publishes its programmes in a structured "Find a Programme" listing.
We walk the listing pages, extract each programme's URL, then fetch
each detail page for: name, faculty, duration, APS, subject requirements.

Usage:
    python uj_scraper.py                    # Just print results
    python uj_scraper.py --import           # Push to Scancourse API
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('uj_scraper')

UJ_BASE = 'https://www.uj.ac.za'
PROGRAMME_INDEX = f'{UJ_BASE}/study-at-uj/find-a-programme/'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
    'Accept-Language': 'en-ZA,en;q=0.9',
}

session = requests.Session()
session.headers.update(HEADERS)


# ════════════════════════════════════════════════════════════════
# Field classifier — maps UJ faculty names to Scancourse field codes
# ════════════════════════════════════════════════════════════════

FACULTY_TO_FIELD = {
    'engineering': 'engineering',
    'built environment': 'built_environment',
    'science': 'science',
    'health science': 'health',
    'humanities': 'humanities',
    'art': 'arts',
    'design': 'arts',
    'architecture': 'built_environment',
    'commerce': 'business',
    'management': 'business',
    'economic': 'business',
    'finance': 'business',
    'business': 'business',
    'law': 'law',
    'education': 'education',
    'computing': 'ict',
    'computer': 'ict',
    'information technology': 'ict',
    'agriculture': 'agriculture',
}

LEVEL_HINTS = {
    'higher certificate': 'certificate',
    'advanced certificate': 'certificate',
    'diploma': 'diploma',
    'advanced diploma': 'advanced_diploma',
    'bachelor': 'degree',
    'b.': 'degree',
    'b sc': 'degree',
    'bcom': 'degree',
    'beng': 'degree',
    'btech': 'advanced_diploma',
    'llb': 'degree',
    'mbchb': 'degree',
    'honours': 'honours',
    'master': 'masters',
    'phd': 'phd',
    'doctorate': 'phd',
}


def classify_field(faculty_name: str, programme_name: str) -> str:
    blob = (faculty_name + ' ' + programme_name).lower()
    for keyword, field in FACULTY_TO_FIELD.items():
        if keyword in blob:
            return field
    return 'other'


def classify_level(programme_name: str) -> str:
    name_lower = programme_name.lower()
    for hint, level in LEVEL_HINTS.items():
        if hint in name_lower:
            return level
    return 'degree'


# ════════════════════════════════════════════════════════════════
# Scraper
# ════════════════════════════════════════════════════════════════

def fetch(url: str, retries: int = 3) -> BeautifulSoup | None:
    for attempt in range(retries):
        try:
            time.sleep(1.0 + attempt * 0.5)  # politeness delay
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            logger.warning(f'  Retry {attempt+1}/{retries}: {e}')
    return None


def discover_programme_urls() -> list[str]:
    """Walk the programme index pages, return all programme detail URLs."""
    logger.info(f'Fetching programme index: {PROGRAMME_INDEX}')
    soup = fetch(PROGRAMME_INDEX)
    if not soup:
        return []

    urls = set()

    # UJ's programme finder lists links to programme detail pages
    for a in soup.find_all('a', href=True):
        href = a['href']
        # UJ programme URLs typically contain '/programme/' or '/qualification/'
        if any(p in href for p in ('/programme/', '/qualification/', '/study-at-uj/find-a-programme/')):
            full = urljoin(PROGRAMME_INDEX, href)
            if 'find-a-programme' not in full or full != PROGRAMME_INDEX:
                urls.add(full)

    logger.info(f'Discovered {len(urls)} programme URLs')
    return sorted(urls)


def extract_programme(url: str) -> dict | None:
    """Extract a single programme's details from its page."""
    soup = fetch(url)
    if not soup:
        return None

    # Title — usually in <h1> or <h2>
    title = None
    for tag in ('h1', 'h2'):
        el = soup.find(tag)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break
    if not title:
        return None

    # Faculty / department
    faculty = ''
    for keyword in ('Faculty', 'College', 'School'):
        el = soup.find(string=re.compile(keyword, re.I))
        if el and el.parent:
            txt = el.parent.get_text(strip=True)[:200]
            if keyword.lower() in txt.lower():
                faculty = txt
                break

    full_text = soup.get_text(' ', strip=True)

    # APS — UJ lists "APS: 28" or "Minimum APS: 28" or "APS score 28"
    aps_match = re.search(r'(?:minimum\s+)?aps\s*(?:score|requirement|of)?\s*[:\-=]?\s*(\d{1,2})', full_text, re.I)
    min_aps = int(aps_match.group(1)) if aps_match else 0

    # Duration
    dur_match = re.search(r'(\d(?:[.,]\d)?)\s*(year|yr)s?', full_text, re.I)
    duration_years = float(dur_match.group(1).replace(',', '.')) if dur_match else None

    # Description
    description = ''
    for p in soup.find_all('p'):
        txt = p.get_text(strip=True)
        if 50 < len(txt) < 600:
            description = txt
            break

    return {
        'name': title.strip()[:300],
        'field': classify_field(faculty, title),
        'level': classify_level(title),
        'duration_years': duration_years,
        'description': description,
        'institution_short_name': 'UJ',
        'min_aps': min_aps,
        'application_url': url,
        'source_url': url,
        'faculty_raw': faculty,
    }


def scrape_uj(limit: int | None = None) -> list[dict]:
    urls = discover_programme_urls()
    if limit:
        urls = urls[:limit]

    programmes = []
    for i, url in enumerate(urls, 1):
        logger.info(f'[{i}/{len(urls)}] {url}')
        prog = extract_programme(url)
        if prog and prog['name']:
            programmes.append(prog)

    return programmes


# ════════════════════════════════════════════════════════════════
# Push to Scancourse API
# ════════════════════════════════════════════════════════════════

def import_to_api(programmes: list[dict], api_url: str, token: str):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    created_courses, created_offerings = 0, 0

    # 1. Get UJ institution id
    resp = requests.get(f'{api_url}/institutions/?search=UJ', headers=headers, timeout=15)
    insts = resp.json().get('results', [])
    uj_inst = next((i for i in insts if i.get('short_name') == 'UJ'), None)
    if not uj_inst:
        logger.error('UJ institution not found in DB. Run seed_data.py first.')
        return

    for prog in programmes:
        # Idempotent — search by name first
        resp = requests.get(f'{api_url}/courses/?search={prog["name"][:40]}', headers=headers, timeout=15)
        existing = resp.json().get('results', [])
        course_id = existing[0]['id'] if existing else None

        if not course_id:
            course_data = {
                'name': prog['name'],
                'field': prog['field'],
                'level': prog['level'],
                'duration_years': prog['duration_years'],
                'description': prog.get('description', ''),
            }
            resp = requests.post(f'{api_url}/courses/', json=course_data, headers=headers, timeout=15)
            if resp.status_code in (200, 201):
                course_id = resp.json().get('id')
                created_courses += 1
                logger.info(f'  + Course: {prog["name"]}')

        # TODO: Create CourseOffering linking course to UJ — needs an admin endpoint
        # For now, this is logged but not pushed (offerings are admin-only).

    logger.info(f'\nDone: {created_courses} courses created.')


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Stop after N programmes (for testing)')
    parser.add_argument('--output', default='uj_courses.json', help='Save results to file')
    parser.add_argument('--import', dest='do_import', action='store_true', help='Push to Scancourse API')
    parser.add_argument('--api-url', default='http://localhost:8000/api/v1')
    parser.add_argument('--token', default='', help='JWT token for API auth')
    args = parser.parse_args()

    programmes = scrape_uj(limit=args.limit)

    with open(args.output, 'w') as f:
        json.dump(programmes, f, indent=2)
    logger.info(f'\nSaved {len(programmes)} programmes to {args.output}')

    print(f'\n=== Sample (first 3) ===')
    for p in programmes[:3]:
        print(f'  • {p["name"]}  [APS {p["min_aps"]}, {p["field"]}, {p["level"]}]')

    if args.do_import:
        if not args.token:
            print('\nERROR: --import needs --token (JWT from /api/v1/auth/login/)')
            sys.exit(1)
        import_to_api(programmes, args.api_url, args.token)
