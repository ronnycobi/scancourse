"""
Vaal University of Technology (VUT) undergraduate programme scraper.

Source: https://www.vut.ac.za — faculty programme pages + Management Sciences
prospectus PDF (2026).

Strategy:
  VUT has one main campus (Vanderbijlpark) and ~38 entry-level programmes
  across four faculties. Programme pages and the faculty prospectus PDFs
  provide APS and subject requirements. We use a verified static seed
  cross-checked against live faculty pages.

Campuses: Vanderbijlpark (main), Secunda, Upington.
"""
import re
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from .parser import ParsedCourse, classify_field, USER_AGENT

logger = logging.getLogger(__name__)

BASE_URL = 'https://vut.ac.za'

# ── Verified static seed (2026) ───────────────────────────────────────────────
# APS values use the lower bound (with Mathematics / Technical Mathematics)
# excluding Life Orientation, as published per faculty programme pages / PDF.
# Advanced Diplomas have min_aps=0 (require a prior 360-credit Diploma).

SEED: list[dict] = [

    # ══════════════════════════════════════════════════════════════════════════
    # Faculty of Engineering and Technology
    # ══════════════════════════════════════════════════════════════════════════
    {
        'name': 'Diploma in Chemical Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Civil Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Mechanical Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Industrial Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Metallurgical Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Electronic Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Power Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Computer Systems Engineering',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 24,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Engineering and Technology',
    },
    {
        'name': 'Diploma in Operations Management',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 23,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 3}],
        'code': '', 'faculty': 'Engineering and Technology',
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Faculty of Applied and Computer Sciences
    # ══════════════════════════════════════════════════════════════════════════
    {
        'name': 'Diploma in Analytical Chemistry',
        'field': 'science', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Diploma in Biotechnology',
        'field': 'science', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 23,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Life Sciences', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Diploma in Agricultural Management',
        'field': 'agriculture', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3},
                     {'subject': 'Life Sciences', 'min_level': 3}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Diploma in Environmental Science',
        'field': 'science', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Diploma in Information Technology',
        'field': 'it', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 26,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Diploma in Non-Destructive Testing',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 19,
        'subjects': [{'subject': 'English', 'min_level': 3},
                     {'subject': 'Mathematics', 'min_level': 3},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },
    {
        'name': 'Bachelor of Health Sciences in Medical Laboratory Science',
        'field': 'health', 'level': 'degree', 'duration_years': 4.0,
        'min_aps': 27,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4},
                     {'subject': 'Life Sciences', 'min_level': 5},
                     {'subject': 'Physical Sciences', 'min_level': 4}],
        'code': '', 'faculty': 'Applied and Computer Sciences',
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Faculty of Human Sciences
    # ══════════════════════════════════════════════════════════════════════════
    {
        'name': 'Diploma in Graphic Design',
        'field': 'arts_design', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Photography',
        'field': 'arts_design', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Fashion',
        'field': 'arts_design', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Fine Art',
        'field': 'arts_design', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Advanced Diploma in Graphic Design',
        'field': 'arts_design', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Advanced Diploma in Photography',
        'field': 'arts_design', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Advanced Diploma in Fashion',
        'field': 'arts_design', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Advanced Diploma in Fine Art',
        'field': 'arts_design', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Food Service Management',
        'field': 'hospitality', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Tourism Management',
        'field': 'hospitality', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Ecotourism Management',
        'field': 'hospitality', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Life Sciences', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Public Relations Management',
        'field': 'media_communications', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Legal Assistance',
        'field': 'law', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 23,
        'subjects': [{'subject': 'English', 'min_level': 5},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Labour Law',
        'field': 'law', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 23,
        'subjects': [{'subject': 'English', 'min_level': 5},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Safety Management',
        'field': 'engineering', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 21,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Diploma in Policing',
        'field': 'social_sciences', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Bachelor of Education in Senior Phase and FET Teaching',
        'field': 'education', 'level': 'degree', 'duration_years': 4.0,
        'min_aps': 22,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 4}],
        'code': '', 'faculty': 'Human Sciences',
    },
    {
        'name': 'Bachelor of Communication Studies',
        'field': 'media_communications', 'level': 'degree', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 5},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Human Sciences',
    },

    # ══════════════════════════════════════════════════════════════════════════
    # Faculty of Management Sciences
    # APS 20 (Maths/Technical Maths) for all diplomas per prospectus PDF p.10
    # ══════════════════════════════════════════════════════════════════════════
    {
        'name': 'Diploma in Cost and Management Accounting',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Accounting', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Internal Auditing',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Accounting', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Financial Information Systems',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Accounting', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Human Resource Management',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Human Resource Management',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Logistics and Supply Chain Management',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Marketing',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Marketing Management',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Retail Business Management',
        'field': 'business', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Retail Business Management',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Diploma in Sport Management',
        'field': 'sport', 'level': 'diploma', 'duration_years': 3.0,
        'min_aps': 20,
        'subjects': [{'subject': 'English', 'min_level': 4},
                     {'subject': 'Mathematics', 'min_level': 3}],
        'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Sport Management',
        'field': 'sport', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Cost and Management Accounting',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Internal Auditing',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
    {
        'name': 'Advanced Diploma in Logistics and Supply Chain Management',
        'field': 'business', 'level': 'advanced_diploma', 'duration_years': 1.0,
        'min_aps': 0, 'subjects': [], 'code': '', 'faculty': 'Management Sciences',
    },
]

# Faculty programme pages (used for optional live APS enrichment)
PROG_PAGES = [
    f'{BASE_URL}/engineering-programmes-vaal-university-of-technology/',
    f'{BASE_URL}/applied-and-computer-sciences-programme/',
    f'{BASE_URL}/human-sciences-programmes-vaal-university-of-technology/',
    f'{BASE_URL}/management-sciences-programmes-vaal-university-of-technology/',
]

APS_RE = re.compile(
    r'(\d{2})\s*\+?\s*(?:APS|points?)',
    re.IGNORECASE,
)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({'User-Agent': USER_AGENT})
    return s


def parse_vut() -> list[ParsedCourse]:
    """Return all VUT undergraduate programmes as ParsedCourse objects."""
    courses: list[ParsedCourse] = []
    for entry in SEED:
        name  = entry['name']
        level = entry['level']
        field = entry.get('field') or classify_field(name + ' ' + entry.get('faculty', ''))

        subj = list(entry.get('subjects') or [])
        if not subj and level not in ('advanced_diploma',):
            from apps.courses.defaults import default_subjects_for
            subj = default_subjects_for(field, level)

        courses.append(ParsedCourse(
            name=name,
            field=field,
            level=level,
            duration_years=entry.get('duration_years', 3.0),
            min_aps=entry.get('min_aps', 0),
            campus='Vanderbijlpark',
            subject_requirements=subj,
            programme_code=entry.get('code', ''),
            institution_short_name='VUT',
            source_excerpt=f"Faculty: {entry.get('faculty', '')}",
        ))

    logger.info(f'VUT total: {len(courses)} programmes')
    return courses


def parse_vut_url(url: str, institution_short_name: str = 'VUT') -> list[ParsedCourse]:
    """URL-based entry point for the generic dispatcher."""
    return parse_vut()
