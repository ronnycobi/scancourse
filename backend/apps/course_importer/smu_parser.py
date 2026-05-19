"""Sefako Makgatho Health Sciences University (SMU) programme parser — static seed 2025/2026.

Single campus: Ga-Rankuwa, Gauteng (formerly MEDUNSA).
APS from best 6 NSC subjects; Life Orientation excluded.
Mathematical Literacy NOT accepted for any SMU programme.
5 schools: Medicine, Health Care Sciences, Oral Health Sciences, Science & Technology, Pharmacy.
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
    duration_years: int = 4,
    programme_code: str = "",
    faculty: str = "",
) -> ParsedCourse:
    return ParsedCourse(
        name=name,
        level=level,
        field=field,
        campus="Ga-Rankuwa",
        min_aps=min_aps,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="SMU",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


_E4 = _s("English", 4)
_E5 = _s("English", 5)
_E6 = _s("English", 6)
_M4 = _s("Mathematics", 4)
_M5 = _s("Mathematics", 5)
_M6 = _s("Mathematics", 6)
_P4 = _s("Physical Sciences", 4)
_P5 = _s("Physical Sciences", 5)
_P6 = _s("Physical Sciences", 6)
_L4 = _s("Life Sciences", 4)
_L5 = _s("Life Sciences", 5)
_L6 = _s("Life Sciences", 6)

SMED  = "School of Medicine"
SHCS  = "School of Health Care Sciences"
SOHS  = "School of Oral Health Sciences"
SST   = "School of Science and Technology"
SPHAR = "School of Pharmacy"

# Standard allied-health subject base (most HCS programmes)
_HCS_BASE = [_E4, _M4, _P4, _L4]
# BSc normal programme base
_BSC_NORM = [_E4, _M5, _P4, _L4]
# BSc extended programme base (lower APS, 4-year curriculum)
_BSC_EXT  = [_E4, _M4, _P4, _L4]

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ School of Medicine ══════════════════════════════════════════════════

    _pc("Bachelor of Medicine and Bachelor of Surgery (MBChB)",
        "degree", "health", 38,
        [_E6, _M6, _P6, _L6], 6, "MBCH01", SMED),

    # ══ School of Health Care Sciences ═════════════════════════════════════

    _pc("Bachelor of Nursing and Midwifery",
        "degree", "health", 25,
        _HCS_BASE, 4, "BNAM", SHCS),

    _pc("Bachelor of Occupational Therapy",
        "degree", "health", 25,
        _HCS_BASE, 4, "BOTA01", SHCS),

    _pc("Bachelor of Science in Physiotherapy",
        "degree", "health", 28,
        _HCS_BASE, 4, "BPT01", SHCS),

    _pc("Bachelor of Speech Language Pathology",
        "degree", "health", 25,
        [_E4, _M4, _L4], 4, "BSLP01", SHCS),

    _pc("Bachelor of Audiology",
        "degree", "health", 25,
        [_E4, _M4, _L4], 4, "BAUD01", SHCS),

    _pc("Bachelor of Science in Dietetics",
        "degree", "health", 25,
        _HCS_BASE, 4, "BDIA01", SHCS),

    _pc("Bachelor of Diagnostic Radiography",
        "degree", "health", 30,
        _HCS_BASE, 4, "BDR01", SHCS),

    # ══ School of Oral Health Sciences ══════════════════════════════════════

    _pc("Bachelor of Dental Surgery (BDS)",
        "degree", "health", 37,
        [_E5, _M6, _P6, _L6], 5, "BDS01", SOHS),

    _pc("Bachelor of Dental Therapy",
        "degree", "health", 26,
        _HCS_BASE, 3, "BDT01", SOHS),

    _pc("Bachelor of Oral Hygiene",
        "degree", "health", 28,
        _HCS_BASE, 3, "BOH01", SOHS),

    # ══ School of Science and Technology ════════════════════════════════════

    # Normal 3-year BSc streams
    _pc("Bachelor of Science in Life Sciences",
        "degree", "science", 25,
        _BSC_NORM, 3, "BSCG01", SST),

    _pc("Bachelor of Science in Mathematical Sciences",
        "degree", "science", 25,
        _BSC_NORM, 3, "BSCH01", SST),

    _pc("Bachelor of Science in Physical Sciences",
        "degree", "science", 25,
        _BSC_NORM, 3, "BSCI01", SST),

    _pc("Bachelor of Science in Occupational and Environmental Health Sciences",
        "degree", "health", 25,
        [_E4, _M5, _P4, _L5], 3, "BSCJ01", SST),

    # Extended 4-year BSc streams (lower APS entry, ECP)
    _pc("Bachelor of Science in Life Sciences (Extended Curriculum)",
        "degree", "science", 24,
        _BSC_EXT, 4, "BSCK01", SST),

    _pc("Bachelor of Science in Mathematical Sciences (Extended Curriculum)",
        "degree", "science", 24,
        _BSC_EXT, 4, "BSCL01", SST),

    _pc("Bachelor of Science in Physical Sciences (Extended Curriculum)",
        "degree", "science", 24,
        _BSC_EXT, 4, "BSCM01", SST),

    # ══ School of Pharmacy ══════════════════════════════════════════════════

    _pc("Bachelor of Pharmacy (BPharm)",
        "degree", "health", 32,
        [_E5, _M5, _P5, _L5], 4, "BPRA01", SPHAR),
]


# ---------------------------------------------------------------------------
def parse_smu() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_smu_url(url: str, institution_short_name: str = "SMU") -> List[ParsedCourse]:
    return parse_smu()
