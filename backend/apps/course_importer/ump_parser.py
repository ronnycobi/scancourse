"""University of Mpumalanga (UMP) programme parser — static seed from official PDF and website.

Campuses: Mbombela (main) | Siyabuswa
Source: UMP Undergraduate Programmes PDF + individual programme pages (2025/2026).
APS note: Life Orientation counts as half its level in APS calculation.
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
        institution_short_name="UMP",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


_E4 = _s("English", 4)
_E5 = _s("English", 5)
_M2 = _s("Mathematics", 2)
_M3 = _s("Mathematics", 3)
_M4 = _s("Mathematics", 4)
_P3 = _s("Physical Sciences", 3)
_P4 = _s("Physical Sciences", 4)
_L4 = _s("Life Sciences", 4)
_G4 = _s("Geography", 4)

MB = "Mbombela"
SY = "Siyabuswa"

FEDB = "Economics, Development & Business Sciences"
FANS = "Agriculture & Natural Sciences"
FED  = "Education"

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ Faculty of Economics, Development & Business Sciences ═════════════

    # School of Hospitality & Tourism Management
    _pc("Higher Certificate in Event Management",
        "higher_certificate", "business", MB, 19,
        [_E4, _M2],
        duration_years=1, faculty=FEDB),

    _pc("Diploma in Hospitality Management",
        "diploma", "business", MB, 26,
        [_E4, _M3],
        duration_years=3, faculty=FEDB),

    _pc("Diploma in Hospitality Management",
        "diploma", "business", SY, 26,
        [_E4, _M3],
        duration_years=3, faculty=FEDB),

    _pc("Diploma in Culinary Arts",
        "diploma", "business", MB, 26,
        [_E4, _M3],
        duration_years=3, faculty=FEDB),

    _pc("Diploma in Culinary Arts",
        "diploma", "business", SY, 26,
        [_E4, _M3],
        duration_years=3, faculty=FEDB),

    # School of Development Studies
    _pc("Bachelor of Development Studies",
        "degree", "social_sciences", MB, 32,
        [_E4, _M2, _s("Geography", 4)],
        duration_years=3, faculty=FEDB),

    _pc("Bachelor of Commerce",
        "degree", "business", MB, 30,
        [_E4, _M4],
        duration_years=3, faculty=FEDB),

    _pc("Bachelor of Administration",
        "degree", "business", MB, 32,
        [_E4, _s("African Language", 4), _M2],
        duration_years=3, faculty=FEDB),

    _pc("Bachelor of Laws",
        "degree", "law", MB, 33,
        [_E4, _s("African Language", 4), _M3],
        duration_years=4, faculty=FEDB),

    # School of Social Sciences
    _pc("Bachelor of Arts",
        "degree", "arts", MB, 28,
        [_E4, _M2],
        duration_years=3, faculty=FEDB),

    _pc("Bachelor of Social Work",
        "degree", "social_sciences", MB, 32,
        [_E4, _M2],
        duration_years=4, faculty=FEDB),

    _pc("Bachelor of Arts in Media, Communication and Culture",
        "degree", "arts", MB, 32,
        [_E4, _s("African Language", 4), _M2],
        duration_years=3, faculty=FEDB),

    # ══ Faculty of Agriculture & Natural Sciences ══════════════════════════

    # School of Agricultural Sciences
    _pc("Diploma in Agriculture in Plant Production",
        "diploma", "science", MB, 23,
        [_E4, _M3, _L4],
        duration_years=3, faculty=FANS),

    _pc("Diploma in Agriculture in Plant Production",
        "diploma", "science", SY, 23,
        [_E4, _M3, _L4],
        duration_years=3, faculty=FANS),

    _pc("Diploma in Animal Production",
        "diploma", "science", MB, 24,
        [_E4, _M3, _P3, _L4],
        duration_years=3, faculty=FANS),

    _pc("Diploma in Animal Production",
        "diploma", "science", SY, 24,
        [_E4, _M3, _P3, _L4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Agriculture in Agricultural Extension and Rural Resource Management",
        "degree", "science", MB, 26,
        [_E4, _M4, _L4, _P4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Science in Agriculture",
        "degree", "science", MB, 30,
        [_E4, _M4, _L4, _P4],
        duration_years=4, faculty=FANS),

    _pc("Bachelor of Science in Forestry",
        "degree", "science", MB, 30,
        [_E4, _M4, _P4, _L4],
        duration_years=4, faculty=FANS),

    # School of Biology & Environmental Sciences
    _pc("Diploma in Nature Conservation",
        "diploma", "science", MB, 30,
        [_E4, _M2, _L4, _G4],
        duration_years=3, faculty=FANS),

    _pc("Diploma in Nature Conservation",
        "diploma", "science", SY, 30,
        [_E4, _M2, _L4, _G4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Science in Environmental Science",
        "degree", "science", MB, 30,
        [_E4, _M4, _L4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Science",
        "degree", "science", MB, 30,
        [_E4, _M4, _P4],
        duration_years=3, faculty=FANS),

    # School of Computing & Mathematical Sciences
    _pc("Higher Certificate in ICT in User Support",
        "higher_certificate", "technology", MB, 20,
        [_E4, _M2],
        duration_years=1, faculty=FANS),

    _pc("Higher Certificate in ICT in User Support",
        "higher_certificate", "technology", SY, 20,
        [_E4, _M2],
        duration_years=1, faculty=FANS),

    _pc("Diploma in ICT in Applications Development",
        "diploma", "technology", MB, 24,
        [_E4, _M4],
        duration_years=3, faculty=FANS),

    _pc("Diploma in ICT in Applications Development",
        "diploma", "technology", SY, 24,
        [_E4, _M4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Information and Communication Technology",
        "degree", "technology", MB, 32,
        [_E4, _M4],
        duration_years=3, faculty=FANS),

    _pc("Bachelor of Information and Communication Technology",
        "degree", "technology", SY, 32,
        [_E4, _M4],
        duration_years=3, faculty=FANS),

    # ══ Faculty of Education ═══════════════════════════════════════════════

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", MB, 26,
        [_E5, _s("African Language", 4), _M4],
        duration_years=4, faculty=FED),

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", SY, 26,
        [_E5, _s("African Language", 4), _M4],
        duration_years=4, faculty=FED),
]


# ---------------------------------------------------------------------------
def parse_ump() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_ump_url(url: str, institution_short_name: str = "UMP") -> List[ParsedCourse]:
    return parse_ump()
