"""Walter Sisulu University (WSU) programme parser — static seed from 2025 brochure."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
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
        institution_short_name="WSU",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


# ---------------------------------------------------------------------------
# SEED — derived from WSU 2025 Information Brochure (14 pages)
# ---------------------------------------------------------------------------

SEED: List[ParsedCourse] = [

    # ── Buffalo City (East London) ─ Engineering, Built Environment & IT ──

    _pc("Diploma in Building Technology", "diploma", "engineering",
        "East London", 24,
        [_s("English", 4), _s("Mathematics", 3), _s("Physical Sciences", 3)],
        faculty="Engineering & Technology"),

    _pc("Diploma in Civil Engineering", "diploma", "engineering",
        "East London", 24,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        faculty="Engineering & Technology"),

    _pc("Diploma in Electrical Engineering", "diploma", "engineering",
        "East London", 24,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        faculty="Engineering & Technology"),

    _pc("Diploma in Mechanical Engineering", "diploma", "engineering",
        "East London", 24,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        faculty="Engineering & Technology"),

    _pc("Diploma in ICT in Applications Development", "diploma", "technology",
        "East London", 22,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Applied & Computer Sciences"),

    _pc("Diploma in ICT in Business Analysis", "diploma", "technology",
        "East London", 22,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Applied & Computer Sciences"),

    _pc("Diploma in ICT in Communication Networks", "diploma", "technology",
        "East London", 22,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Applied & Computer Sciences"),

    _pc("Diploma in ICT in Support Services", "diploma", "technology",
        "East London", 22,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Applied & Computer Sciences"),

    # ── Butterworth (Ibika) ─ Management & Public Administration ──────────

    _pc("Higher Certificate in Versatile Broadcasting", "higher_certificate", "arts",
        "Butterworth", 18,
        [_s("English", 4)],
        duration_years=1,
        faculty="Management Sciences"),

    _pc("Diploma in Administrative Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 4), _s("Mathematics", 2)],
        faculty="Management Sciences"),

    _pc("Diploma in Hospitality Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Human Resources Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Journalism", "diploma", "arts",
        "Butterworth", 23,
        [_s("English", 4)],
        faculty="Management Sciences"),

    _pc("Diploma in Local Government Finance", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3), _s("Accounting", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3), _s("Accounting", 3), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Marketing Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Office Management and Technology", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Policing", "diploma", "law",
        "Butterworth", 23,
        [_s("English", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Public Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Public Relations Management", "diploma", "arts",
        "Butterworth", 23,
        [_s("English", 4)],
        faculty="Management Sciences"),

    _pc("Diploma in Small Business Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Sport Management", "diploma", "other",
        "Butterworth", 23,
        [_s("English", 3)],
        faculty="Management Sciences"),

    _pc("Diploma in Tourism Management", "diploma", "business",
        "Butterworth", 23,
        [_s("English", 4), _s("Mathematics", 3)],
        faculty="Management Sciences"),

    _pc("Bachelor of Administration", "degree", "business",
        "Butterworth", 27,
        [_s("English", 4)],
        duration_years=3,
        faculty="Management Sciences"),

    # ── Mthatha ─ Economic & Financial Sciences ───────────────────────────

    _pc("Diploma in Accountancy", "diploma", "business",
        "Mthatha", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Economic & Financial Sciences"),

    _pc("Diploma in Financial Information Systems", "diploma", "business",
        "Mthatha", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Economic & Financial Sciences"),

    _pc("Diploma in Internal Auditing", "diploma", "business",
        "Mthatha", 23,
        [_s("English", 3), _s("Mathematics", 3)],
        faculty="Economic & Financial Sciences"),

    _pc("Bachelor of Accounting", "degree", "business",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 4)],
        duration_years=3,
        faculty="Economic & Financial Sciences"),

    _pc("Bachelor of Accounting Sciences", "degree", "business",
        "Mthatha", 29,
        [_s("English", 5), _s("Mathematics", 4)],
        duration_years=3,
        faculty="Economic & Financial Sciences"),

    _pc("Bachelor of Commerce", "degree", "business",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=3,
        faculty="Economic & Financial Sciences"),

    _pc("Bachelor of Commerce in Business Management", "degree", "business",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=3,
        faculty="Economic & Financial Sciences"),

    _pc("Bachelor of Commerce in Economics", "degree", "business",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=3,
        faculty="Economic & Financial Sciences"),

    # ── Mthatha ─ Law, Humanities & Social Sciences ───────────────────────

    _pc("Diploma in Fashion", "diploma", "arts",
        "Mthatha", 21,
        [_s("English", 4), _s("Mathematics", 2)],
        faculty="Humanities & Social Sciences"),

    _pc("Diploma in Fine Art", "diploma", "arts",
        "Mthatha", 20,
        [_s("English", 3)],
        faculty="Humanities & Social Sciences"),

    _pc("Bachelor of Arts", "degree", "arts",
        "Mthatha", 26,
        [_s("English", 5)],
        duration_years=3,
        faculty="Humanities & Social Sciences"),

    _pc("Bachelor of Social Sciences", "degree", "social_sciences",
        "Mthatha", 26,
        [_s("English", 4)],
        duration_years=3,
        faculty="Humanities & Social Sciences"),

    _pc("Bachelor of Laws", "degree", "law",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=4,
        faculty="Law"),

    _pc("Bachelor of Psychology", "degree", "health",
        "Mthatha", 28,
        [_s("English", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Humanities & Social Sciences"),

    _pc("Bachelor of Social Work", "degree", "social_sciences",
        "Mthatha", 28,
        [_s("English", 4)],
        duration_years=4,
        faculty="Humanities & Social Sciences"),

    # ── Mthatha ─ Medicine & Health Sciences ──────────────────────────────

    _pc("Bachelor of Medical Sciences", "degree", "health",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Medicine & Health Sciences"),

    _pc("Bachelor of Medicine in Clinical Practice", "degree", "health",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Medicine & Health Sciences"),

    _pc("Bachelor of Nursing", "degree", "health",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 3), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Medicine & Health Sciences"),

    _pc("Bachelor of Health Sciences in Medical Orthotics and Prosthetics", "degree", "health",
        "Mthatha", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Medicine & Health Sciences"),

    _pc("Bachelor of Medicine and Bachelor of Surgery (MBChB)", "degree", "health",
        "Mthatha", 30,
        [_s("English", 5), _s("Mathematics", 5), _s("Physical Sciences", 5), _s("Life Sciences", 5)],
        duration_years=6,
        faculty="Medicine & Health Sciences"),

    # ── Mthatha ─ Natural Sciences ────────────────────────────────────────

    _pc("Diploma in Analytical Chemistry", "diploma", "science",
        "Mthatha", 24,
        [_s("English", 3), _s("Life Sciences", 3), _s("Physical Sciences", 3)],
        faculty="Natural Sciences"),

    _pc("Diploma in Consumer Sciences and Food Nutrition", "diploma", "science",
        "Mthatha", 23,
        [_s("English", 4), _s("Life Sciences", 3), _s("Physical Sciences", 3)],
        faculty="Natural Sciences"),

    _pc("Diploma in Pest Management", "diploma", "science",
        "Mthatha", 20,
        [_s("English", 4), _s("Mathematics", 3), _s("Life Sciences", 3)],
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Applied Mathematics", "degree", "science",
        "Mthatha", 26,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Applied Statistical Science", "degree", "science",
        "Mthatha", 26,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Biological Sciences", "degree", "science",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Chemistry", "degree", "science",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 5), _s("Physical Sciences", 5)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Computer Science", "degree", "technology",
        "Mthatha", 26,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Environmental Studies", "degree", "science",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Mathematics", "degree", "science",
        "Mthatha", 26,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Pest Management", "degree", "science",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Natural Sciences"),

    _pc("Bachelor of Science in Physics", "degree", "science",
        "Mthatha", 28,
        [_s("English", 4), _s("Mathematics", 5), _s("Physical Sciences", 5)],
        duration_years=3,
        faculty="Natural Sciences"),

    # ── Komani (Queenstown) ─ Education ───────────────────────────────────

    _pc("Diploma in Adult and Community Education and Training", "diploma", "education",
        "Komani", 22,
        [_s("English", 3), _s("Mathematics", 2)],
        faculty="Education"),

    _pc("Bachelor of Education in Foundation Phase Teaching", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("African Language", 4), _s("Mathematics", 2)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Arts & Culture)", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("African Language", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Consumer & Management Science)", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("Mathematics", 2)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Economic & Management Science)", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("Mathematics", 2), _s("Accounting", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Humanities)", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("African Language", 4), _s("History", 4), _s("Geography", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Languages)", "degree", "education",
        "Komani", 28,
        [_s("English", 5)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Maths, Science and Technology)", "degree", "education",
        "Komani", 28,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Technical and Vocational)", "degree", "education",
        "Komani", 28,
        [_s("English", 4)],
        duration_years=4,
        faculty="Education"),
]


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def parse_wsu() -> List[ParsedCourse]:
    """Return all WSU ParsedCourse records from the static seed."""
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_wsu_url(url: str, institution_short_name: str = "WSU") -> List[ParsedCourse]:
    """URL-based entry point (dispatcher compatibility)."""
    return parse_wsu()
