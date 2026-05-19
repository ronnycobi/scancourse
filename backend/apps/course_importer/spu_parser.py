"""Sol Plaatje University (SPU) programme parser — static seed from 2026 prospectus PDF."""
from __future__ import annotations
from typing import List
from .parser import ParsedCourse


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

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
        campus="Kimberley",
        min_aps=min_aps,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="SPU",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


# ---------------------------------------------------------------------------
# SEED — from SPU 2026 Undergraduate Prospectus PDF
# Single campus: Kimberley, Northern Cape
# All Bachelor degrees: APS 30 | All Diplomas & Higher Certs: APS 25
# Advanced Diplomas and PGCE require prior qualifications — excluded.
# ---------------------------------------------------------------------------

SEED: List[ParsedCourse] = [

    # ── Faculty of Education ──────────────────────────────────────────────

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", 30,
        [_s("English", 4), _s("African Language", 4), _s("Mathematics", 3)],
        duration_years=4, programme_code="EDU720",
        faculty="Education"),

    _pc("Bachelor of Education in Intermediate Phase Teaching (Maths, Science & Technology)",
        "degree", "education", 30,
        [_s("English", 4), _s("African Language", 4), _s("Mathematics", 4),
         _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4, programme_code="EDU723",
        faculty="Education"),

    _pc("Bachelor of Education in Intermediate Phase Teaching (Languages & Social Sciences)",
        "degree", "education", 30,
        [_s("English", 4), _s("African Language", 4), _s("Geography", 4)],
        duration_years=4, programme_code="EDU724",
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Life Sciences, Natural Sciences & Mathematics)",
        "degree", "education", 30,
        [_s("English", 4), _s("Mathematics", 4), _s("Life Sciences", 4)],
        duration_years=4, programme_code="EDU740",
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Languages & History)",
        "degree", "education", 30,
        [_s("English", 4), _s("African Language", 4), _s("History", 4)],
        duration_years=4, programme_code="EDU741",
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (History, Social Sciences & Language)",
        "degree", "education", 30,
        [_s("English", 4), _s("African Language", 4), _s("Geography", 4), _s("History", 4)],
        duration_years=4, programme_code="EDU742",
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Accounting, Economics & Business Studies)",
        "degree", "education", 30,
        [_s("English", 4), _s("Accounting", 4), _s("Economics", 4)],
        duration_years=4, programme_code="EDU743",
        faculty="Education"),

    # ── Faculty of Economic & Management Sciences ─────────────────────────

    _pc("Bachelor of Commerce in Accounting",
        "degree", "business", 30,
        [_s("English", 4), _s("Mathematics", 5)],
        duration_years=3,
        faculty="Economic & Management Sciences"),

    _pc("Bachelor of Commerce in Economics",
        "degree", "business", 30,
        [_s("English", 4), _s("Mathematics", 5)],
        duration_years=3,
        faculty="Economic & Management Sciences"),

    _pc("Diploma in Retail Business Management",
        "diploma", "business", 25,
        [_s("English", 4), _s("Mathematics", 3), _s("Business Studies", 4)],
        duration_years=3,
        faculty="Economic & Management Sciences"),

    _pc("Higher Certificate in Entrepreneurship",
        "higher_certificate", "business", 25,
        [_s("English", 4), _s("Mathematics", 3), _s("Business Studies", 3)],
        duration_years=1,
        faculty="Economic & Management Sciences"),

    # ── Faculty of Humanities ─────────────────────────────────────────────

    _pc("Bachelor of Arts",
        "degree", "arts", 30,
        [_s("English", 4), _s("Mathematics", 2)],
        duration_years=3,
        faculty="Humanities"),

    _pc("Higher Certificate in Heritage Studies",
        "higher_certificate", "arts", 25,
        [_s("English", 4), _s("Mathematics", 2)],
        duration_years=1,
        faculty="Humanities"),

    _pc("Higher Certificate in Court Interpreting",
        "higher_certificate", "arts", 25,
        [_s("English", 4), _s("African Language", 4)],
        duration_years=1,
        faculty="Humanities"),

    # ── Faculty of Natural & Applied Sciences ─────────────────────────────

    _pc("Bachelor of Science",
        "degree", "science", 30,
        [_s("English", 4), _s("Mathematics", 4),
         _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Natural & Applied Sciences"),

    _pc("Bachelor of Science in Data Science",
        "degree", "technology", 30,
        [_s("English", 4), _s("Mathematics", 5)],
        duration_years=3,
        faculty="Natural & Applied Sciences"),

    _pc("Bachelor of Environmental Science",
        "degree", "science", 30,
        [_s("English", 4), _s("Mathematics", 4),
         _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Natural & Applied Sciences"),

    _pc("Diploma in Information and Communication Technology in Applications Development",
        "diploma", "technology", 25,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=3,
        faculty="Natural & Applied Sciences"),

    _pc("Diploma in Agriculture",
        "diploma", "science", 25,
        [_s("English", 4), _s("Mathematics", 3),
         _s("Physical Sciences", 3), _s("Life Sciences", 3)],
        duration_years=3,
        faculty="Natural & Applied Sciences"),
]


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def parse_spu() -> List[ParsedCourse]:
    """Return all SPU ParsedCourse records from the static seed."""
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_spu_url(url: str, institution_short_name: str = "SPU") -> List[ParsedCourse]:
    """URL-based entry point (dispatcher compatibility)."""
    return parse_spu()
