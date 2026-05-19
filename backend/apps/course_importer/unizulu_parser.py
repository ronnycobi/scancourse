"""University of Zululand (UniZulu) programme parser — static seed from 2026 sources.

Campuses: KwaDlangezwa (main) | Richards Bay
Sources: CAO programme list, FSAE/FCAL/FEDU/FHSS handbook snippets, aggregators.
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
        institution_short_name="UniZulu",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


# Shared subject blocks
_ENG4 = _s("English", 4)
_ENG3 = _s("English", 3)
_MATH4 = _s("Mathematics", 4)
_MATH3 = _s("Mathematics", 3)
_MATH5 = _s("Mathematics", 5)
_PHYS4 = _s("Physical Sciences", 4)
_PHYS5 = _s("Physical Sciences", 5)
_LIFE4 = _s("Life Sciences", 4)
_LIFE3 = _s("Life Sciences", 3)

KD = "KwaDlangezwa"
RB = "Richards Bay"
FHSS = "Humanities & Social Sciences"
FCAL = "Commerce, Administration & Law"
FEDU = "Education"
FSAE = "Science, Agriculture & Engineering"

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ Faculty of Humanities & Social Sciences — KwaDlangezwa ═══════════
    # All BA degrees: APS 26, English HL4/FAL3

    _pc("Bachelor of Arts in Development Studies",       "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ABS"),
    _pc("Bachelor of Arts in Sociology",                 "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ARD"),
    _pc("Bachelor of Arts in Industrial Sociology",      "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ARI"),
    _pc("Bachelor of Arts in Information Science",       "degree", "other",           KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ARK"),
    _pc("Bachelor of Arts in Correctional Studies",      "degree", "law",             KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ARM"),
    _pc("Bachelor of Arts in Environmental Planning and Development", "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-ARO"),
    _pc("Bachelor of Arts (Geography and History)",      "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BGE"),
    _pc("Bachelor of Arts (Geography and Tourism)",      "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BGT"),
    _pc("Bachelor of Arts (History and IsiZulu)",        "degree", "arts",            KD, 26, [_ENG4, _s("IsiZulu", 5)], faculty=FHSS, programme_code="ZU-M-BHI"),
    _pc("Bachelor of Arts in Intercultural Communication","degree","arts",            KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BIC"),
    _pc("Bachelor of Arts (Linguistics and English)",    "degree", "arts",            KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BLE"),
    _pc("Bachelor of Library and Information Science",   "degree", "other",           KD, 26, [_ENG4], duration_years=4, faculty=FHSS, programme_code="ZU-M-BLI"),
    _pc("Bachelor of Arts in Drama, Theatre and Performance", "degree", "arts",       KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BTP"),
    _pc("Bachelor of Tourism",                           "degree", "business",        KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BTT"),
    _pc("Bachelor of Arts (Anthropology and History)",   "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BNH"),
    _pc("Bachelor of Arts (Philosophy and Psychology)",  "degree", "arts",            KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-BPY"),
    _pc("Bachelor of Social Work",                       "degree", "social_sciences", KD, 26, [_ENG4], duration_years=4, faculty=FHSS, programme_code="ZU-M-BSX"),
    _pc("Bachelor of Social Sciences in Political and International Studies", "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-PIS"),
    _pc("Bachelor of Arts in Psychology",                "degree", "social_sciences", KD, 26, [_ENG4], faculty=FHSS, programme_code="ZU-M-PSY"),

    # ══ Faculty of Commerce, Administration & Law — KwaDlangezwa ══════════
    # BCom 3-year degrees: APS 28, Maths L4 + English L4

    _pc("Bachelor of Commerce",                          "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BC1"),
    _pc("Bachelor of Commerce in Accounting",            "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BCN"),
    _pc("Bachelor of Commerce in Accounting Science",    "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BAS"),
    _pc("Bachelor of Commerce (Accounting and Economics)","degree","business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BC7"),
    _pc("Bachelor of Commerce (Banking and Business Management)", "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BC8"),
    _pc("Bachelor of Commerce (Economics and Banking)",  "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BC9"),
    _pc("Bachelor of Commerce (Business Management and Accounting)", "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BMB"),
    _pc("Bachelor of Commerce (Business Management and Economics)",  "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BBO"),
    _pc("Bachelor of Commerce (Human Resource Management and Business Management)", "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BUS"),
    _pc("Bachelor of Commerce (Economics and Human Resource Management)", "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BER"),
    _pc("Bachelor of Commerce in Management Information Systems",    "degree", "technology", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BCS"),
    _pc("Bachelor of Commerce in Entrepreneurship",      "degree", "business", KD, 28, [_ENG4, _MATH4], faculty=FCAL, programme_code="ZU-M-BCU"),

    # BAdmin degrees: APS 28, English L4
    _pc("Bachelor of Administration",                    "degree", "business", KD, 28, [_ENG4], faculty=FCAL, programme_code="ZU-M-BAD"),
    _pc("Bachelor of Administration (Public Administration and Business Management)", "degree", "business", KD, 28, [_ENG4], faculty=FCAL, programme_code="ZU-M-PAB"),
    _pc("Bachelor of Administration (Public Administration and Economics)", "degree", "business", KD, 28, [_ENG4], faculty=FCAL, programme_code="ZU-M-BAE"),
    _pc("Bachelor of Administration (Public Administration and Political Science)", "degree", "business", KD, 28, [_ENG4], faculty=FCAL, programme_code="ZU-M-PAP"),
    _pc("Bachelor of Administration (Public Administration and Human Resources)", "degree", "business", KD, 28, [_ENG4], faculty=FCAL, programme_code="ZU-M-PHU"),

    # LLB: APS 32, English L5
    _pc("Bachelor of Laws", "degree", "law", KD, 32, [_s("English", 5)], duration_years=4, faculty=FCAL, programme_code="ZU-M-BL1"),

    # Richards Bay — Diplomas & Higher Certificates (FCAL)
    _pc("Higher Certificate in Accountancy",  "higher_certificate", "business", RB, 22, [_ENG3, _MATH3], duration_years=1, faculty=FCAL, programme_code="ZU-R-AC2"),
    _pc("Diploma in Co-Operatives Management","diploma",            "business", RB, 24, [_ENG3], faculty=FCAL, programme_code="ZU-R-CO3"),
    _pc("Diploma in Logistics Management",    "diploma",            "business", RB, 24, [_ENG3], faculty=FCAL, programme_code="ZU-R-LM3"),
    _pc("Diploma in Transport Management",    "diploma",            "business", RB, 24, [_ENG3], faculty=FCAL, programme_code="ZU-R-TP3"),
    _pc("Diploma in Media Studies",           "diploma",            "arts",     RB, 24, [_ENG4], faculty=FCAL, programme_code="ZU-R-MD4"),
    _pc("Diploma in Public Relations Management","diploma",         "arts",     RB, 24, [_ENG4], faculty=FCAL, programme_code="ZU-R-PR5"),
    _pc("Diploma in Tourism Management",      "diploma",            "business", RB, 24, [_ENG4], faculty=FCAL, programme_code="ZU-R-TM1"),

    # ══ Faculty of Education — KwaDlangezwa ═══════════════════════════════
    # All BEd: APS 26, 4 years

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", KD, 26,
        [_ENG4, _MATH3], duration_years=4, faculty=FEDU, programme_code="ZU-M-FPT"),

    _pc("Bachelor of Education in Intermediate Phase Teaching (Languages and Humanities)",
        "degree", "education", KD, 26,
        [_ENG4, _MATH3], duration_years=4, faculty=FEDU, programme_code="ZU-M-ILH"),

    _pc("Bachelor of Education in Intermediate Phase Teaching (Languages, Maths, Natural Sciences & Technology)",
        "degree", "education", KD, 26,
        [_ENG4, _MATH4], duration_years=4, faculty=FEDU, programme_code="ZU-M-ILM"),

    _pc("Bachelor of Education SP & FET Teaching (Economics and Management Sciences)",
        "degree", "education", KD, 26,
        [_ENG4, _MATH4], duration_years=4, faculty=FEDU, programme_code="ZU-M-SFC"),

    _pc("Bachelor of Education SP & FET Teaching (Humanities and Social Sciences)",
        "degree", "education", KD, 26,
        [_ENG4], duration_years=4, faculty=FEDU, programme_code="ZU-M-SFH"),

    _pc("Bachelor of Education SP & FET Teaching (Natural Sciences and Technology)",
        "degree", "education", KD, 26,
        [_ENG4, _MATH4, _PHYS4], duration_years=4, faculty=FEDU, programme_code="ZU-M-SFN"),

    # ══ Faculty of Science, Agriculture & Engineering ══════════════════════

    # BEng — Richards Bay (APS 30, Maths L5, Phys Sci L5)
    _pc("Bachelor of Engineering in Electrical Engineering",
        "degree", "engineering", RB, 30,
        [_ENG4, _MATH5, _PHYS5], duration_years=4, faculty=FSAE, programme_code="ZU-R-BEZ"),

    _pc("Bachelor of Engineering in Mechanical Engineering",
        "degree", "engineering", RB, 30,
        [_ENG4, _MATH5, _PHYS5], duration_years=4, faculty=FSAE, programme_code="ZU-R-BMZ"),

    _pc("Bachelor of Engineering in Electrical and Computer Engineering",
        "degree", "engineering", RB, 30,
        [_ENG4, _MATH5, _PHYS5], duration_years=4, faculty=FSAE, programme_code="ZU-R-BOE"),

    _pc("Bachelor of Engineering in Mechatronic Engineering",
        "degree", "engineering", KD, 30,
        [_ENG4, _MATH5, _PHYS5], duration_years=4, faculty=FSAE),

    # BSc double-majors — KwaDlangezwa (APS 28, Maths L5, Phys Sci L4)
    # Applied Mathematics series
    _pc("Bachelor of Science (Applied Mathematics and Computer Sciences)",  "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-AMC"),
    _pc("Bachelor of Science (Applied Mathematics and Hydrology)",          "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-AMH"),
    _pc("Bachelor of Science (Applied Mathematics and Mathematics)",        "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-AMM"),
    _pc("Bachelor of Science (Applied Mathematics and Statistics)",         "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-AMS"),
    _pc("Bachelor of Science (Applied Mathematics and Physics)",            "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-APH"),
    # Biochemistry series
    _pc("Bachelor of Science (Biochemistry and Botany)",                    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BBM"),
    _pc("Bachelor of Science (Biochemistry and Chemistry)",                 "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BC3"),
    _pc("Bachelor of Science (Biochemistry and Human Movement Science)",    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BH3"),
    _pc("Bachelor of Science (Biochemistry and Microbiology)",              "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BIM"),
    _pc("Bachelor of Science (Biochemistry and Zoology)",                   "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BZ3"),
    # Botany series
    _pc("Bachelor of Science (Botany and Geography)",                       "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BOG"),
    _pc("Bachelor of Science (Botany and Hydrology)",                       "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BOH"),
    _pc("Bachelor of Science (Botany and Microbiology)",                    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BOM"),
    _pc("Bachelor of Science (Botany and Zoology)",                         "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-BOZ"),
    # Chemistry series
    _pc("Bachelor of Science (Chemistry and Computer Science)",             "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CHC"),
    _pc("Bachelor of Science (Chemistry and Hydrology)",                    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CHH"),
    _pc("Bachelor of Science (Chemistry and Mathematics)",                  "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CHM"),
    _pc("Bachelor of Science (Chemistry and Physics)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CHP"),
    _pc("Bachelor of Science (Chemistry and Zoology)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CZM"),
    # Computer Science series
    _pc("Bachelor of Science (Computer Science and Statistics)",            "degree", "technology", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-COS"),
    _pc("Bachelor of Science (Computer Science and Physics)",               "degree", "technology", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CPH"),
    _pc("Bachelor of Science (Computer Science and Mathematics)",           "degree", "technology", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CSC"),
    _pc("Bachelor of Science (Computer Science and Hydrology)",             "degree", "technology", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-CSH"),
    # Geography series
    _pc("Bachelor of Science (Geography and Hydrology)",                    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-GEH"),
    _pc("Bachelor of Science (Geography and Physics)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-GEP"),
    _pc("Bachelor of Science (Geography and Statistics)",                   "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-GES"),
    _pc("Bachelor of Science (Geography and Zoology)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-GEZ"),
    # Human Movement Science
    _pc("Bachelor of Science (Human Movement Science and Physics)",         "degree", "health",  KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HMP"),
    _pc("Bachelor of Science (Human Movement Science and Zoology)",         "degree", "health",  KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HMZ"),
    # Hydrology series
    _pc("Bachelor of Science (Hydrology and Microbiology)",                 "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HYM"),
    _pc("Bachelor of Science (Hydrology and Physics)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HYP"),
    _pc("Bachelor of Science (Hydrology and Statistics)",                   "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HYS"),
    _pc("Bachelor of Science (Hydrology and Zoology)",                      "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-HYZ"),
    # Mathematics series
    _pc("Bachelor of Science (Mathematics and Statistics)",                 "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-MAS"),
    _pc("Bachelor of Science (Mathematics and Physics)",                    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-MPM"),
    # Microbiology series
    _pc("Bachelor of Science (Microbiology and Human Movement Science)",    "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-MIH"),
    _pc("Bachelor of Science (Microbiology and Zoology)",                   "degree", "science", KD, 28, [_ENG4, _MATH5, _PHYS4], faculty=FSAE, programme_code="ZU-M-MIZ"),

    # BSc Agriculture — KwaDlangezwa (APS 28)
    _pc("Bachelor of Science in Agriculture: Agronomy",
        "degree", "science", KD, 28,
        [_ENG4, _MATH3, _LIFE3], duration_years=4, faculty=FSAE, programme_code="ZU-M-SCA"),

    _pc("Bachelor of Science in Agriculture: Animal Science",
        "degree", "science", KD, 28,
        [_ENG4, _MATH3, _LIFE3], duration_years=4, faculty=FSAE, programme_code="ZU-M-SCK"),

    _pc("Bachelor of Science in Agricultural Economics: Agribusiness Management",
        "degree", "science", KD, 28,
        [_ENG4, _MATH4], duration_years=4, faculty=FSAE, programme_code="ZU-M-SCJ"),

    # Consumer Science — KwaDlangezwa (APS 28)
    _pc("Bachelor of Consumer Science: Extension and Rural Development",
        "degree", "science", KD, 28,
        [_ENG4, _LIFE4], duration_years=4, faculty=FSAE, programme_code="ZU-M-BPE"),

    _pc("Bachelor of Consumer Science: Hospitality and Tourism",
        "degree", "business", KD, 28,
        [_ENG4], duration_years=3, faculty=FSAE, programme_code="ZU-M-BPT"),

    # Nursing — KwaDlangezwa (APS 30)
    _pc("Bachelor of Nursing Science",
        "degree", "health", KD, 30,
        [_ENG4, _MATH4, _LIFE4], duration_years=4, faculty=FSAE, programme_code="ZU-M-BNS"),

    # Richards Bay — FSAE Diplomas
    _pc("Diploma in Hospitality Management",    "diploma", "business", RB, 24, [_ENG4], faculty=FSAE, programme_code="ZU-R-DHM"),
    _pc("Diploma in Sport and Exercise Technology", "diploma", "other", RB, 24, [_ENG4, _LIFE3], faculty=FSAE, programme_code="ZU-R-SET"),
]


# ---------------------------------------------------------------------------
def parse_unizulu() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_unizulu_url(url: str, institution_short_name: str = "UniZulu") -> List[ParsedCourse]:
    return parse_unizulu()
