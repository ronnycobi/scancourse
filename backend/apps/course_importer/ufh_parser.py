"""University of Fort Hare (UFH) programme parser — static seed from 2025/2026 prospectus data."""
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
        institution_short_name="UFH",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


# ---------------------------------------------------------------------------
# SEED — derived from UFH 2025/2026 prospectus and official website
# Campuses: Alice (main), East London, Bhisho
# ---------------------------------------------------------------------------

SEED: List[ParsedCourse] = [

    # ── Faculty of Social Sciences & Humanities (East London) ─────────────

    _pc("Diploma in Fine Art", "diploma", "arts",
        "East London", 22,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Arts", "degree", "arts",
        "East London", 26,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Arts in Philosophy, Politics and Law", "degree", "arts",
        "East London", 26,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Social Science", "degree", "social_sciences",
        "East London", 26,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Social Science in Communication", "degree", "social_sciences",
        "East London", 26,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Fine Arts", "degree", "arts",
        "East London", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Music", "degree", "arts",
        "East London", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Social Work", "degree", "social_sciences",
        "East London", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Library and Information Science", "degree", "other",
        "East London", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Social Science in Human Settlement", "degree", "social_sciences",
        "East London", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Theology", "degree", "arts",
        "Alice", 25,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    _pc("Bachelor of Applied Communication Management", "degree", "arts",
        "East London", 25,
        [_s("English", 4)],
        faculty="Social Sciences & Humanities"),

    # ── Faculty of Education (Alice primary; also East London and Bhisho) ─

    _pc("Bachelor of Education in Foundation Phase Teaching", "degree", "education",
        "Alice", 26,
        [_s("English", 4), _s("Mathematics", 3)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education in Intermediate Phase Teaching", "degree", "education",
        "Alice", 26,
        [_s("English", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Social Science)", "degree", "education",
        "Alice", 28,
        [_s("English", 4), _s("History", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Natural Sciences)", "degree", "education",
        "Alice", 30,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4)],
        duration_years=4,
        faculty="Education"),

    _pc("Bachelor of Education SP & FET Teaching (Commerce)", "degree", "education",
        "Alice", 28,
        [_s("English", 4), _s("Accounting", 4)],
        duration_years=4,
        faculty="Education"),

    # ── Faculty of Law (East London) ──────────────────────────────────────

    _pc("Bachelor of Laws", "degree", "law",
        "East London", 30,
        [_s("English", 5)],
        duration_years=4,
        faculty="Law"),

    _pc("Bachelor of Commerce in Law", "degree", "law",
        "East London", 27,
        [_s("English", 4), _s("Mathematics", 4)],
        duration_years=3,
        faculty="Law"),

    # ── Faculty of Management & Commerce (East London, Alice, Bhisho) ─────

    _pc("Bachelor of Commerce", "degree", "business",
        "East London", 26,
        [_s("English", 4), _s("Mathematics", 4)],
        duration_years=3,
        faculty="Management & Commerce"),

    _pc("Bachelor of Commerce in Accounting", "degree", "business",
        "East London", 30,
        [_s("English", 4), _s("Mathematics", 5)],
        duration_years=3,
        faculty="Management & Commerce"),

    _pc("Bachelor of Commerce in Information Systems", "degree", "technology",
        "East London", 26,
        [_s("English", 4), _s("Mathematics", 4)],
        duration_years=3,
        faculty="Management & Commerce"),

    _pc("Bachelor of Administration in Public Administration", "degree", "business",
        "East London", 24,
        [_s("English", 4)],
        duration_years=3,
        faculty="Management & Commerce"),

    # ── Faculty of Science & Agriculture (Alice) ──────────────────────────

    _pc("Bachelor of Science", "degree", "science",
        "Alice", 30,
        [_s("English", 4), _s("Mathematics", 5), _s("Physical Sciences", 5)],
        duration_years=3,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Agriculture", "degree", "science",
        "Alice", 26,
        [_s("English", 4), _s("Mathematics", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Crop Science", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Agricultural Economics", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Animal Production", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Soil Science", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Horticulture Science", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    _pc("Bachelor of Science in Agriculture: Livestock and Pasture Management", "degree", "science",
        "Alice", 27,
        [_s("English", 4), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Science & Agriculture"),

    # ── Faculty of Health Sciences (East London) ──────────────────────────

    _pc("Bachelor of Nursing", "degree", "health",
        "East London", 30,
        [_s("English", 4), _s("Life Sciences", 4), _s("Mathematics", 4)],
        duration_years=4,
        faculty="Health Sciences"),

    _pc("Bachelor of Health Sciences in Human Movement Science", "degree", "health",
        "East London", 28,
        [_s("English", 4), _s("Life Sciences", 4)],
        duration_years=3,
        faculty="Health Sciences"),

    _pc("Bachelor of Science in Speech-Language Pathology", "degree", "health",
        "East London", 30,
        [_s("English", 5), _s("Mathematics", 4), _s("Physical Sciences", 4), _s("Life Sciences", 4)],
        duration_years=4,
        faculty="Health Sciences"),
]


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

def parse_ufh() -> List[ParsedCourse]:
    """Return all UFH ParsedCourse records from the static seed."""
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_ufh_url(url: str, institution_short_name: str = "UFH") -> List[ParsedCourse]:
    """URL-based entry point (dispatcher compatibility)."""
    return parse_ufh()
