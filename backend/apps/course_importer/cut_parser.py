"""Central University of Technology (CUT) programme parser — static seed from website 2025/2026.

Campuses: Bloemfontein (main) | Welkom
General minimum APS: 27. Life Orientation counts max 1 point.
Mathematical Literacy NOT accepted for Engineering or Health Sciences.
"""
from __future__ import annotations
from typing import List
from .parser import ParsedCourse


def _s(subject: str, min_level: int) -> dict:
    return {"subject": subject, "min_level": min_level}


def _pc(
    name: str,
    level: str,
    field: str,
    campus: str,
    min_aps: int,
    subjects: List[dict],
    duration_years: int = 3,
    programme_code: str = "",
    faculty: str = "",
) -> ParsedCourse:
    return ParsedCourse(
        name=name,
        level=level,
        field=field,
        campus=campus,
        min_aps=min_aps,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="CUT",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


_E3 = _s("English", 3)
_E4 = _s("English", 4)
_E5 = _s("English", 5)
_M2 = _s("Mathematics", 2)
_M3 = _s("Mathematics", 3)
_M4 = _s("Mathematics", 4)
_M5 = _s("Mathematics", 5)
_P4 = _s("Physical Sciences", 4)
_P5 = _s("Physical Sciences", 5)
_L4 = _s("Life Sciences", 4)

BFN = "Bloemfontein"
WLK = "Welkom"

FEBIT = "Engineering, Built Environment & IT"
FHES  = "Health & Environmental Sciences"
FH    = "Humanities"
FMS   = "Management Sciences"


def _both(name, level, field, min_aps, subjects, duration_years=3, faculty=""):
    """Convenience: return one entry per campus."""
    return [
        _pc(name, level, field, BFN, min_aps, subjects, duration_years, faculty=faculty),
        _pc(name, level, field, WLK, min_aps, subjects, duration_years, faculty=faculty),
    ]


# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ Faculty of Engineering, Built Environment & IT ═════════════════════

    # Higher Certificates — Bloemfontein only
    _pc("Higher Certificate in Construction",
        "higher_certificate", "engineering", BFN, 27,
        [_M4, _P4], duration_years=1, faculty=FEBIT),

    _pc("Higher Certificate in Renewable Energy Technologies",
        "higher_certificate", "engineering", BFN, 27,
        [_M4, _P4], duration_years=1, faculty=FEBIT),

    _pc("Higher Certificate in Mathematics for Engineering Technology",
        "higher_certificate", "engineering", BFN, 22,
        [_E3, _M2, _P4], duration_years=1, faculty=FEBIT),

    # Diplomas — Bloemfontein only
    _pc("Diploma in Engineering Technology in Electrical Engineering",
        "diploma", "engineering", BFN, 27,
        [_E3, _M4, _P4], duration_years=3, faculty=FEBIT),

    _pc("Diploma in Engineering Technology in Mechanical Engineering",
        "diploma", "engineering", BFN, 27,
        [_E3, _M4, _P4], duration_years=3, faculty=FEBIT),

    _pc("Diploma in Computer Networking",
        "diploma", "technology", BFN, 27,
        [_E4, _M3], duration_years=3, faculty=FEBIT),

    # Engineering degrees — Bloemfontein only
    _pc("Bachelor of Engineering Technology in Civil Engineering",
        "degree", "engineering", BFN, 32,
        [_E4, _M5, _P4], duration_years=3, faculty=FEBIT),

    _pc("Bachelor of Engineering Technology in Mechanical Engineering",
        "degree", "engineering", BFN, 32,
        [_E3, _M5, _P4], duration_years=3, faculty=FEBIT),

    _pc("Bachelor of Construction Management",
        "degree", "engineering", BFN, 32,
        [_E5, _M5, _P5], duration_years=3, faculty=FEBIT),

    _pc("Bachelor of Quantity Surveying",
        "degree", "engineering", BFN, 32,
        [_E5, _M5, _P5], duration_years=3, faculty=FEBIT),

    _pc("Bachelor of Hydrology and Water Resources Management",
        "degree", "science", BFN, 28,
        [_M4, _P4, _L4], duration_years=3, faculty=FEBIT),

    _pc("Bachelor of Health and Safety Management in Construction",
        "degree", "engineering", BFN, 32,
        [_E5, _M5, _P5], duration_years=3, faculty=FEBIT),

    # IT — both campuses
    *_both("Higher Certificate in Information Technology",
           "higher_certificate", "technology", 27,
           [_E4], duration_years=1, faculty=FEBIT),

    *_both("Diploma in Information Technology",
           "diploma", "technology", 27,
           [_E4, _M3], duration_years=3, faculty=FEBIT),

    # ══ Faculty of Health & Environmental Sciences — Bloemfontein ══════════

    _pc("Higher Certificate in Dental Assisting",
        "higher_certificate", "health", BFN, 27,
        [_E3, _L4], duration_years=1, faculty=FHES),

    _pc("Diploma in Agricultural Management",
        "diploma", "science", BFN, 27,
        [_E4, _L4], duration_years=3, faculty=FHES),

    _pc("Diploma in Somatology",
        "diploma", "health", BFN, 27,
        [_E4, _L4], duration_years=3, faculty=FHES),

    _pc("Bachelor of Health Sciences in Clinical Technology",
        "degree", "health", BFN, 30,
        [_E4, _M4, _P4, _L4], duration_years=4, faculty=FHES),

    _pc("Bachelor of Health Science in Medical Laboratory Sciences",
        "degree", "health", BFN, 30,
        [_E4, _M4, _P4, _L4], duration_years=4, faculty=FHES),

    _pc("Bachelor of Environmental Health",
        "degree", "health", BFN, 30,
        [_E4, _M4, _P4, _L4], duration_years=4, faculty=FHES),

    _pc("Bachelor of Radiography in Diagnostics",
        "degree", "health", BFN, 30,
        [_E4, _M4, _P4, _L4], duration_years=4, faculty=FHES),

    # ══ Faculty of Humanities ═══════════════════════════════════════════════

    _pc("Diploma in Design and Studio Art",
        "diploma", "arts", BFN, 27,
        [_E4], duration_years=3, faculty=FH),

    # Language Practice — both campuses
    *_both("Diploma in Language Practice and Media Studies",
           "diploma", "arts", 27,
           [_E5, _s("African Language", 5)], duration_years=3, faculty=FH),

    # BEd Foundation Phase — both campuses
    *_both("Bachelor of Education in Foundation Phase Teaching",
           "degree", "education", 27,
           [_E4, _s("African Language", 4)], duration_years=4, faculty=FH),

    # BEd SP & FET — both campuses (except Technology which is BFN only)
    *_both("Bachelor of Education SP & FET Teaching (Computer Science)",
           "degree", "education", 27,
           [_E4, _M4], duration_years=4, faculty=FH),

    *_both("Bachelor of Education SP & FET Teaching (Economic and Management Sciences)",
           "degree", "education", 27,
           [_E4, _M4, _s("Accounting", 4)], duration_years=4, faculty=FH),

    *_both("Bachelor of Education SP & FET Teaching (Language Education)",
           "degree", "education", 27,
           [_E4, _s("African Language", 4)], duration_years=4, faculty=FH),

    *_both("Bachelor of Education SP & FET Teaching (Mathematics)",
           "degree", "education", 27,
           [_E4, _M4, _P4], duration_years=4, faculty=FH),

    *_both("Bachelor of Education SP & FET Teaching (Natural Sciences)",
           "degree", "education", 27,
           [_E4, _M4, _P4, _L4], duration_years=4, faculty=FH),

    _pc("Bachelor of Education SP & FET Teaching (Technology)",
        "degree", "education", BFN, 27,
        [_E4, _M4], duration_years=4, faculty=FH),

    # ══ Faculty of Management Sciences ════════════════════════════════════

    _pc("Higher Certificate in Community Development Work",
        "higher_certificate", "social_sciences", BFN, 27,
        [_E4], duration_years=1, faculty=FMS),

    # Diplomas — both campuses
    *_both("Diploma in Human Resources Management",
           "diploma", "business", 27,
           [_E4], duration_years=3, faculty=FMS),

    *_both("Diploma in Management",
           "diploma", "business", 27,
           [_E4], duration_years=3, faculty=FMS),

    *_both("Diploma in Marketing",
           "diploma", "business", 27,
           [_E4], duration_years=3, faculty=FMS),

    *_both("Diploma in Office Management and Technology",
           "diploma", "business", 27,
           [_E4], duration_years=3, faculty=FMS),

    *_both("Diploma in Public Management",
           "diploma", "business", 27,
           [_E4], duration_years=3, faculty=FMS),

    # Hospitality & Tourism — Bloemfontein only
    _pc("Diploma in Hospitality Management",
        "diploma", "business", BFN, 27,
        [_E4], duration_years=3, faculty=FMS),

    _pc("Diploma in Tourism Management",
        "diploma", "business", BFN, 28,
        [_E4], duration_years=3, faculty=FMS),

    # Bachelor degrees — both campuses
    *_both("Bachelor of Management Sciences in Accountancy",
           "degree", "business", 27,
           [_E4, _s("Accounting", 5), _M3], duration_years=4, faculty=FMS),

    _pc("Bachelor of Management Sciences in Internal Auditing",
        "degree", "business", BFN, 27,
        [_E4, _s("Accounting", 5), _M3], duration_years=4, faculty=FMS),
]


# ---------------------------------------------------------------------------
def parse_cut() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_cut_url(url: str, institution_short_name: str = "CUT") -> List[ParsedCourse]:
    return parse_cut()
