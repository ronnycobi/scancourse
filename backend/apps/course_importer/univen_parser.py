"""University of Venda (UNIVEN) programme parser — static seed from 2026/2027 prospectus data.

Single campus: Thohoyandou, Limpopo.
APS from best 6 NSC subjects; Life Orientation excluded.
Mathematical Literacy NOT accepted for BSc, BEng, BNursing or BCom Accounting Sciences.
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
        campus="Thohoyandou",
        min_aps=min_aps,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="UNIVEN",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


_E4 = _s("English", 4)
_E5 = _s("English", 5)
_M3 = _s("Mathematics", 3)
_M4 = _s("Mathematics", 4)
_M5 = _s("Mathematics", 5)
_M6 = _s("Mathematics", 6)
_P4 = _s("Physical Sciences", 4)
_P5 = _s("Physical Sciences", 5)
_P6 = _s("Physical Sciences", 6)
_L4 = _s("Life Sciences", 4)
_G4 = _s("Geography", 4)

FSEA = "Science, Engineering & Agriculture"
FHS  = "Health Sciences"
FMCL = "Management, Commerce & Law"
FHSE = "Humanities, Social Sciences & Education"

# Shared subject profiles
_AGR_BASE  = [_E4, _M4, _P4, _L4]   # all BSc Agric standard specialisations
_BSC_BASIC = [_E4, _M4, _P4]         # maths/physics/cs combinations
_BSC_BIO   = [_E4, _M4, _P4, _L4]   # biochem/biology combinations

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ Faculty of Science, Engineering & Agriculture ══════════════════════

    # BSc Agriculture — 7 specialisations (APS 26, 4 years each)
    _pc("Bachelor of Science in Agriculture (Agricultural Economics)",
        "degree", "science", 26, _AGR_BASE, 4, "AGBAAE", FSEA),
    _pc("Bachelor of Science in Agriculture (Agribusiness Management)",
        "degree", "science", 26, _AGR_BASE, 4, "AGBAAM", FSEA),
    _pc("Bachelor of Science in Agriculture (Animal Science)",
        "degree", "science", 26, _AGR_BASE, 4, "AGBAAS", FSEA),
    _pc("Bachelor of Science in Agriculture (Horticultural Sciences)",
        "degree", "science", 26, _AGR_BASE, 4, "AGBAHS", FSEA),
    _pc("Bachelor of Science in Agriculture (Plant Production)",
        "degree", "science", 26, _AGR_BASE, 4, "AGBAPP", FSEA),
    _pc("Bachelor of Science in Soil Science",
        "degree", "science", 26, _AGR_BASE, 4, "AGBASS", FSEA),
    _pc("Bachelor of Science in Forestry",
        "degree", "science", 26, _AGR_BASE, 4, "AGBBFR", FSEA),

    # Agricultural engineering & food science (APS 32)
    _pc("Bachelor of Science in Agricultural and Biosystems Engineering",
        "degree", "engineering", 32,
        [_E4, _M6, _P6, _L4], 4, "AGBABE", FSEA),
    _pc("Bachelor of Science in Food Science and Technology",
        "degree", "science", 32,
        [_E4, _M5, _P5, _L4], 4, faculty=FSEA),

    # Environmental Sciences
    _pc("Bachelor of Environmental Sciences",
        "degree", "science", 32,
        [_E4, _M3, _L4], 3, "ESBBES", FSEA),
    _pc("Bachelor of Environmental Sciences in Disaster Risk Reduction",
        "degree", "science", 26,
        [_E4, _P4, _G4], 3, "ESBBDR", FSEA),
    _pc("Bachelor of Earth Sciences in Mining and Environmental Geology",
        "degree", "science", 35,
        [_E4, _M5, _P5], 4, "ESBMEG", FSEA),
    _pc("Bachelor of Earth Sciences in Hydrology and Water Resources",
        "degree", "science", 35,
        [_E5, _M5, _P5], 4, "ESBHWR", FSEA),
    _pc("Bachelor of Urban and Regional Planning",
        "degree", "science", 35,
        [_E4, _M5, _P5], 4, "ESBURP", FSEA),

    # BSc Mathematical & Natural Sciences — 13 combinations (APS 26)
    _pc("Bachelor of Science (Biochemistry and Microbiology)",
        "degree", "science", 26, _BSC_BIO,  3, "MNBBSA", FSEA),
    _pc("Bachelor of Science (Biochemistry and Biology)",
        "degree", "science", 26, _BSC_BIO,  3, "MNBBSD", FSEA),
    _pc("Bachelor of Science (Microbiology and Botany)",
        "degree", "science", 26, _BSC_BIO,  3, "MNBBSE", FSEA),
    _pc("Bachelor of Science (Mathematics and Applied Mathematics)",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSF", FSEA),
    _pc("Bachelor of Science (Mathematics and Physics)",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSH", FSEA),
    _pc("Bachelor of Science (Mathematics and Statistics)",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSI", FSEA),
    _pc("Bachelor of Science (Physics and Chemistry)",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSJ", FSEA),
    _pc("Bachelor of Science (Chemistry and Mathematics)",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSK", FSEA),
    _pc("Bachelor of Science (Chemistry and Biochemistry)",
        "degree", "science", 26, _BSC_BIO,  3, "MNBBSL", FSEA),
    _pc("Bachelor of Science in Chemistry",
        "degree", "science", 26, _BSC_BASIC, 3, "MNBBSN", FSEA),
    _pc("Bachelor of Science (Botany and Zoology)",
        "degree", "science", 26, _BSC_BIO,  3, "MNBBSO", FSEA),
    _pc("Bachelor of Science in Computer Science",
        "degree", "technology", 26, _BSC_BASIC, 3, "MNBBSP", FSEA),
    _pc("Bachelor of Science (Computer Science and Mathematics)",
        "degree", "technology", 26, _BSC_BASIC, 3, "MNBBSQ", FSEA),

    # Diploma
    _pc("Diploma in Freshwater Technology",
        "diploma", "science", 24,
        [_s("English", 2), _L4], 3, "MNDDFT", FSEA),

    # ══ Faculty of Health Sciences ══════════════════════════════════════════

    _pc("Bachelor of Nursing",
        "degree", "health", 36,
        [_E4, _M4, _P4, _L4], 4, "SHBBN", FHS),
    _pc("Bachelor of Science in Nutrition",
        "degree", "health", 34,
        [_E4, _M4, _P4, _L4], 4, "SHBBSN", FHS),
    _pc("Bachelor of Science in Sports and Exercise Science",
        "degree", "health", 34,
        [_E4, _M4, _P4, _L4], 4, "SHBSES", FHS),
    _pc("Bachelor of Science in Recreation and Leisure Studies",
        "degree", "health", 34,
        [_E4, _L4, _P4], 3, "SHBRLS", FHS),
    _pc("Bachelor of Psychology",
        "degree", "social_sciences", 36,
        [_E4, _L4], 4, "SHBBP", FHS),
    _pc("Diploma in Nursing",
        "diploma", "health", 28,
        [_E4, _M3, _P4, _L4], 3, "SHDPN", FHS),

    # ══ Faculty of Management, Commerce & Law ══════════════════════════════

    _pc("Bachelor of Administration",
        "degree", "business", 32,
        [_E4], 3, "MSBBAD", FMCL),
    _pc("Bachelor of Commerce in Accounting Sciences",
        "degree", "business", 35,
        [_E4, _M4], 4, "MSBCAS", FMCL),
    _pc("Bachelor of Commerce in Accounting",
        "degree", "business", 32,
        [_E4, _M4, _s("Accounting", 4)], 3, "MSBBCA", FMCL),
    _pc("Bachelor of Commerce in Business Information Systems",
        "degree", "technology", 32,
        [_E4, _M3], 3, "MSBIS", FMCL),
    _pc("Bachelor of Commerce in Business Management",
        "degree", "business", 32,
        [_E4, _s("Business Studies", 4)], 3, "MSBCBM", FMCL),
    _pc("Bachelor of Commerce in Cost and Management Accounting",
        "degree", "business", 32,
        [_E4, _M4, _s("Accounting", 4)], 3, "MSBCMA", FMCL),
    _pc("Bachelor of Commerce in Economics",
        "degree", "business", 32,
        [_E4, _M4, _s("Economics", 4)], 3, "MSBBCE", FMCL),
    _pc("Bachelor of Commerce in Human Resource Management",
        "degree", "business", 32,
        [_E4], 3, "MSBHR", FMCL),
    _pc("Bachelor of Commerce in Industrial Psychology",
        "degree", "business", 32,
        [_E4], 3, "MSBCIP", FMCL),
    _pc("Bachelor of Commerce in Tourism Management",
        "degree", "business", 32,
        [_E4], 3, "MSBTRM", FMCL),
    _pc("Baccalaureus Legum (LLB)",
        "degree", "law", 38,
        [_E5], 4, "LWBBL", FMCL),
    _pc("Bachelor of Arts in Criminal Justice",
        "degree", "law", 34,
        [_E4], 3, "LWBACJ", FMCL),

    # ══ Faculty of Humanities, Social Sciences & Education ══════════════════

    _pc("Bachelor of Arts",
        "degree", "arts", 30,
        [_E4], 3, "HSBBA", FHSE),
    _pc("Bachelor of Arts in Media Studies",
        "degree", "arts", 30,
        [_E4, _s("African Language", 4)], 3, "HSBAMS", FHSE),
    _pc("Bachelor of Arts in Development Studies",
        "degree", "social_sciences", 30,
        [_E4, _s("History", 4)], 3, "HSBADS", FHSE),
    _pc("Bachelor of Arts in International Relations",
        "degree", "social_sciences", 30,
        [_E4, _s("History", 4)], 3, "HSBAIR", FHSE),
    _pc("Bachelor of Arts in Language Practice",
        "degree", "arts", 30,
        [_E4, _s("African Language", 4)], 4, "HSBALP", FHSE),
    _pc("Bachelor of Arts in Youth in Development",
        "degree", "social_sciences", 30,
        [_E4], 4, "HSBAYD", FHSE),
    _pc("Bachelor of Arts (History)",
        "degree", "arts", 30,
        [_E4, _s("History", 4)], 3, "HSBBAH", FHSE),
    _pc("Bachelor of Indigenous Knowledge Systems",
        "degree", "arts", 30,
        [_E4, _s("African Language", 4)], 4, "HSBIKS", FHSE),
    _pc("Bachelor of Theology",
        "degree", "arts", 30,
        [_E4], 3, "HSBBT", FHSE),
    _pc("Bachelor of Social Work",
        "degree", "social_sciences", 35,
        [_E4], 4, "HSBBSW", FHSE),
    _pc("Bachelor of Arts (English and Literature)",
        "degree", "arts", 30,
        [_E5, _s("African Language", 4)], 3, "HSBAEL", FHSE),

    # BEd programmes (APS 36, 4 years)
    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", 36,
        [_E4], 4, "SEBEFP", FHSE),
    _pc("Bachelor of Education SP & FET Teaching (Sciences)",
        "degree", "education", 36,
        [_E4, _M4, _P4, _L4], 4, "SEBESP", FHSE),
    _pc("Bachelor of Education SP & FET Teaching (Commerce)",
        "degree", "education", 36,
        [_E4, _s("Accounting", 4), _s("Economics", 4)], 4, "SEBECP", FHSE),
    _pc("Bachelor of Education SP & FET Teaching (Humanities)",
        "degree", "education", 36,
        [_E4, _s("History", 4)], 4, "SEBELP", FHSE),
]


# ---------------------------------------------------------------------------
def parse_univen() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_univen_url(url: str, institution_short_name: str = "UNIVEN") -> List[ParsedCourse]:
    return parse_univen()
