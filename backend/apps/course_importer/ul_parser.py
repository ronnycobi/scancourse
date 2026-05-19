"""University of Limpopo (UL) programme parser — static seed from 2026 prospectus.

Single campus: Turfloop (Sovenga, near Polokwane), Limpopo.
ECP (Extended Curriculum Programme) pathways are excluded — mainstream entry only.
APS excludes Life Orientation.
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
        campus="Turfloop",
        min_aps=min_aps,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="UL",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


_E4 = _s("English", 4)
_E5 = _s("English", 5)
_M3 = _s("Mathematics", 3)
_M4 = _s("Mathematics", 4)
_M5 = _s("Mathematics", 5)
_P4 = _s("Physical Sciences", 4)
_P5 = _s("Physical Sciences", 5)
_L3 = _s("Life Sciences", 3)
_L4 = _s("Life Sciences", 4)
_L5 = _s("Life Sciences", 5)

FH   = "Humanities"
FML  = "Management & Law"
FSA  = "Science & Agriculture"
FHS  = "Health Sciences"

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ Faculty of Humanities — School of Education ════════════════════════
    # All BEd: APS 24, 4 years

    _pc("Bachelor of Education SP & FET Teaching (Languages and Life Orientation)",
        "degree", "education", 24,
        [_E4, _s("African Language", 4)],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Education SP & FET Teaching (Languages and Social Sciences)",
        "degree", "education", 24,
        [_E4, _s("History", 4)],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Education SP & FET Teaching (Economics and Management Studies)",
        "degree", "education", 24,
        [_E4, _s("Accounting", 4)],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Education SP & FET Teaching (Mathematics, Science and Technology)",
        "degree", "education", 24,
        [_E4, _M4, _P4],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", 24,
        [_E4, _M3],
        duration_years=4, faculty=FH),

    # ══ Faculty of Humanities — School of Social Sciences ══════════════════

    _pc("Bachelor of Arts (Criminology and Psychology)",
        "degree", "social_sciences", 23,
        [_E4, _M3],
        faculty=FH),

    _pc("Bachelor of Arts (Cultural Studies)",
        "degree", "arts", 23,
        [_E4, _s("African Language", 4), _M3],
        faculty=FH),

    _pc("Bachelor of Arts (Sociology and Anthropology)",
        "degree", "social_sciences", 23,
        [_E4, _M3],
        faculty=FH),

    _pc("Bachelor of Arts (Political Studies)",
        "degree", "social_sciences", 25,
        [_E4],
        faculty=FH),

    _pc("Bachelor of Social Work",
        "degree", "social_sciences", 23,
        [_E4, _M3],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Psychology",
        "degree", "social_sciences", 23,
        [_E4, _M3],
        duration_years=4, faculty=FH),

    # ══ Faculty of Humanities — School of Languages & Communication ════════

    _pc("Bachelor of Arts (Languages)",
        "degree", "arts", 25,
        [_E4, _s("African Language", 5)],
        faculty=FH),

    _pc("Bachelor of Arts (Translation and Linguistics)",
        "degree", "arts", 25,
        [_E4, _s("African Language", 5)],
        faculty=FH),

    _pc("Bachelor of Arts (Performing Arts)",
        "degree", "arts", 25,
        [_E4, _s("African Language", 5)],
        faculty=FH),

    _pc("Bachelor of Information Studies",
        "degree", "other", 25,
        [_E4, _s("African Language", 5)],
        duration_years=4, faculty=FH),

    _pc("Bachelor of Arts in Contemporary English and Multilingual Studies",
        "degree", "arts", 25,
        [_E4, _s("Northern Sotho", 5)],
        faculty=FH),

    _pc("Bachelor of Arts in Communication Studies",
        "degree", "arts", 25,
        [_E4, _s("African Language", 5)],
        faculty=FH),

    _pc("Bachelor of Arts in Media Studies",
        "degree", "arts", 25,
        [_E4, _s("African Language", 5)],
        faculty=FH),

    # ══ Faculty of Management & Law — School of Accountancy ════════════════

    _pc("Bachelor of Accountancy",
        "degree", "business", 30,
        [_E4, _M4],
        duration_years=4, faculty=FML),

    _pc("Bachelor of Commerce in Accountancy",
        "degree", "business", 28,
        [_E4, _M4],
        faculty=FML),

    # ══ Faculty of Management & Law — School of Economics & Management ═════

    _pc("Bachelor of Commerce in Human Resource Management",
        "degree", "business", 26,
        [_E4, _M3],
        faculty=FML),

    _pc("Bachelor of Commerce in Business Management",
        "degree", "business", 26,
        [_E4, _M3],
        faculty=FML),

    _pc("Bachelor of Commerce in Economics",
        "degree", "business", 26,
        [_E4, _M3, _s("Economics", 4)],
        faculty=FML),

    _pc("Bachelor of Administration",
        "degree", "business", 26,
        [_E4],
        faculty=FML),

    _pc("Bachelor of Administration in Local Government",
        "degree", "business", 26,
        [_E4],
        faculty=FML),

    _pc("Bachelor of Development (Planning and Management)",
        "degree", "social_sciences", 26,
        [_E4, _M3, _s("Economics", 4)],
        faculty=FML),

    # ══ Faculty of Management & Law — School of Law ════════════════════════

    _pc("Bachelor of Laws",
        "degree", "law", 30,
        [_E5],
        duration_years=4, faculty=FML),

    # ══ Faculty of Science & Agriculture — School of Agriculture ═══════════

    _pc("Bachelor of Agricultural Management",
        "degree", "science", 24,
        [_E4, _M3, _L4, _s("Geography", 4)],
        faculty=FSA),

    _pc("Bachelor of Science in Agriculture (Agricultural Economics)",
        "degree", "science", 24,
        [_E4, _M4, _L4],
        duration_years=4, faculty=FSA),

    _pc("Bachelor of Science in Agriculture (Plant Production)",
        "degree", "science", 24,
        [_E4, _M4, _P4, _L4],
        duration_years=4, faculty=FSA),

    _pc("Bachelor of Science in Agriculture (Animal Production)",
        "degree", "science", 24,
        [_E4, _M4, _P4, _L4],
        duration_years=4, faculty=FSA),

    _pc("Bachelor of Science in Agriculture (Soil Science)",
        "degree", "science", 25,
        [_E4, _M4, _P5, _L4],
        duration_years=4, faculty=FSA),

    _pc("Bachelor of Science in Environmental and Resource Studies",
        "degree", "science", 24,
        [_E4, _M4, _P4, _L4],
        duration_years=4, faculty=FSA),

    _pc("Bachelor of Science in Water and Sanitation Sciences",
        "degree", "science", 24,
        [_E4, _M5, _P5, _L4],
        duration_years=4, faculty=FSA),

    # ══ Faculty of Science & Agriculture — School of Mathematical & Computer

    _pc("Bachelor of Science (Mathematical Sciences)",
        "degree", "science", 24,
        [_E4, _M5],
        faculty=FSA),

    _pc("Bachelor of Science in Computer Science",
        "degree", "technology", 27,
        [_E4, _M4, _P4],
        faculty=FSA),

    # ══ Faculty of Science & Agriculture — School of Molecular & Life Sci ══

    _pc("Bachelor of Science (Life Sciences)",
        "degree", "science", 26,
        [_E4, _M5, _P5, _L4],
        faculty=FSA),

    # ══ Faculty of Science & Agriculture — School of Physical & Mineral Sci

    _pc("Bachelor of Science (Physical Sciences)",
        "degree", "science", 26,
        [_E4, _M5, _P5],
        faculty=FSA),

    _pc("Bachelor of Science in Geology",
        "degree", "science", 26,
        [_E4, _M5, _P5],
        faculty=FSA),

    # ══ Faculty of Health Sciences — School of Medicine ════════════════════

    _pc("Bachelor of Medicine and Bachelor of Surgery (MBChB)",
        "degree", "health", 27,
        [_E4, _M5, _P5, _L5],
        duration_years=6, faculty=FHS),

    # ══ Faculty of Health Sciences — School of Health Care Sciences ════════

    _pc("Bachelor of Science in Dietetics",
        "degree", "health", 26,
        [_E4, _M4, _P5, _L5],
        duration_years=4, faculty=FHS),

    _pc("Bachelor of Optometry",
        "degree", "health", 27,
        [_E4, _M5, _P5, _L5],
        duration_years=4, faculty=FHS),

    _pc("Bachelor of Science in Medical Sciences",
        "degree", "health", 26,
        [_E4, _M4, _P5, _L5],
        duration_years=4, faculty=FHS),

    _pc("Bachelor of Nursing",
        "degree", "health", 26,
        [_E4, _M4, _P5, _L5],
        duration_years=4, faculty=FHS),

    _pc("Bachelor of Pharmacy",
        "degree", "health", 27,
        [_E4, _M5, _P5, _L5],
        duration_years=4, faculty=FHS),
]


# ---------------------------------------------------------------------------
def parse_ul() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_ul_url(url: str, institution_short_name: str = "UL") -> List[ParsedCourse]:
    return parse_ul()
