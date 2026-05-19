"""University of South Africa (UNISA) programme parser — static seed 2025/2026.

Distance learning only — no physical campus; campus value set to "Distance Learning".
No APS gate: min_aps=0 for all programmes. Entry is via NSC endorsement type:
  - Higher Certificate: NSC with Higher Certificate admission
  - Diploma / Advanced Diploma: NSC with Diploma admission
  - Degree: NSC with Bachelor's admission
Subject requirements are translated from UNISA's percentage minimums to NSC levels:
  30% ≈ level 2 | 40% ≈ level 3 | 50% ≈ level 4
Duration = minimum expected completion time (not the maximum allowable years).
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
    subjects: List[dict],
    duration_years: int,
    programme_code: str = "",
    faculty: str = "",
) -> ParsedCourse:
    return ParsedCourse(
        name=name,
        level=level,
        field=field,
        campus="Distance Learning",
        min_aps=0,
        subject_requirements=subjects,
        duration_years=duration_years,
        programme_code=programme_code,
        institution_short_name="UNISA",
        source_excerpt=f"Faculty: {faculty}" if faculty else "",
        description="",
    )


# Subject shorthands — based on UNISA percentage minimums → NSC levels
_E2 = _s("English", 2)   # 30% minimum
_E3 = _s("English", 3)   # 40% minimum
_E4 = _s("English", 4)   # 50% minimum
_M3 = _s("Mathematics", 3)   # 40% minimum
_M4 = _s("Mathematics", 4)   # 50% minimum
_P4 = _s("Physical Sciences", 4)
_L3 = _s("Life Sciences", 3)
_L4 = _s("Life Sciences", 4)
_AC4 = _s("Accounting", 4)

# College names
CACC  = "College of Accounting Sciences"
CEDU  = "College of Education"
CSET  = "College of Science, Engineering & Technology"
CEMS  = "College of Economic & Management Sciences"
CLAW  = "College of Law"
CHSC  = "College of Human Sciences"
CAES  = "College of Agriculture & Environmental Sciences"

# Common subject bundles
_HC_LANG   = [_E3]           # Higher Certificate — lang 40%
_DIP_LANG  = [_E4]           # Diploma — lang 50%
_DEG_LANG  = [_E4]           # Degree — lang 50%
_ENG_DIP   = [_E4, _M4]      # Engineering diplomas — lang+math 50%
_SCI_DEG   = [_E4, _M4]      # Science degrees
_AGR_DEG   = [_E4, _P4]      # Agriculture degrees — physical sciences 50%

# ---------------------------------------------------------------------------
SEED: List[ParsedCourse] = [

    # ══ College of Accounting Sciences ══════════════════════════════════════

    _pc("Higher Certificate in Accounting Sciences",
        "higher_certificate", "business", [_E3], 1, "98201", CACC),

    _pc("Diploma in Accounting Sciences",
        "diploma", "business", [_E4, _M3], 3, "98200", CACC),

    _pc("Advanced Diploma in Accounting Sciences (Financial Accounting)",
        "advanced_diploma", "business", [_E4, _M3], 2, "98230-FAC", CACC),

    _pc("Advanced Diploma in Accounting Sciences (Internal Auditing)",
        "advanced_diploma", "business", [_E4, _M3], 2, "98230-AUI", CACC),

    _pc("Advanced Diploma in Accounting Sciences (Management Accounting)",
        "advanced_diploma", "business", [_E4, _M3], 2, "98230-MA1", CACC),

    _pc("Advanced Diploma in Accounting Sciences (Taxation)",
        "advanced_diploma", "business", [_E4, _M3], 2, "98230-TAX", CACC),

    _pc("Bachelor of Accounting Sciences (Financial Accounting)",
        "degree", "business", [_E4, _M4], 4, "98302-FA1", CACC),

    _pc("Bachelor of Accounting Sciences (Internal Auditing)",
        "degree", "business", [_E4, _M4], 4, "98303-AUI", CACC),

    _pc("Bachelor of Accounting Sciences (Management Accounting)",
        "degree", "business", [_E4, _M4], 4, "98304-MA1", CACC),

    _pc("Bachelor of Accounting Sciences (Taxation)",
        "degree", "business", [_E4, _M4], 4, "98318-TAX", CACC),

    # ══ College of Education ════════════════════════════════════════════════

    _pc("Higher Certificate in Education",
        "higher_certificate", "education", [_E3], 1, "90093", CEDU),

    _pc("Diploma in Early Childhood Care and Education",
        "diploma", "education", [_E4], 3, "90187", CEDU),

    _pc("Advanced Diploma in Adult Education and Training",
        "advanced_diploma", "education", [_E4], 2, "90190", CEDU),

    _pc("Bachelor of Education in Foundation Phase Teaching",
        "degree", "education", [_E4, _M3], 4, "90102", CEDU),

    _pc("Bachelor of Education in Intermediate Phase Teaching",
        "degree", "education", [_E4, _M3], 4, "90103", CEDU),

    _pc("Bachelor of Education in Senior Phase and FET Teaching",
        "degree", "education", [_E4], 4, "90104", CEDU),

    # ══ College of Science, Engineering & Technology ════════════════════════

    _pc("Higher Certificate in Mathematics and Statistics",
        "higher_certificate", "science", [_E3, _M3], 1, "90129", CSET),

    _pc("Higher Certificate in Physical Sciences",
        "higher_certificate", "science", [_E3, _M3], 1, "90101", CSET),

    _pc("Diploma in Chemical Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90130", CSET),

    _pc("Diploma in Civil Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90137", CSET),

    _pc("Diploma in Electrical Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90138", CSET),

    _pc("Diploma in Industrial Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90136", CSET),

    _pc("Diploma in Mechanical Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90132", CSET),

    _pc("Diploma in Mining Engineering",
        "diploma", "engineering", _ENG_DIP, 3, "90140", CSET),

    _pc("Diploma in Information Technology",
        "diploma", "technology", [_E4, _M3], 3, "98806-ITE", CSET),

    _pc("Advanced Diploma in Chemical Engineering",
        "advanced_diploma", "engineering", _ENG_DIP, 2, "90128", CSET),

    _pc("Advanced Diploma in Electrical Engineering",
        "advanced_diploma", "engineering", _ENG_DIP, 2, "90126", CSET),

    _pc("Advanced Diploma in Mechanical Engineering",
        "advanced_diploma", "engineering", _ENG_DIP, 2, "90133", CSET),

    _pc("Advanced Diploma in Mining Engineering",
        "advanced_diploma", "engineering", _ENG_DIP, 2, "90131", CSET),

    _pc("Bachelor of Science (Applied Mathematics and Computer Science)",
        "degree", "science", _SCI_DEG, 4, "98801-AMC", CSET),

    _pc("Bachelor of Science (Mathematics and Computer Science)",
        "degree", "technology", _SCI_DEG, 4, "98801-MCS", CSET),

    _pc("Bachelor of Science (Mathematics and Statistics)",
        "degree", "science", _SCI_DEG, 4, "98801-MAS", CSET),

    _pc("Bachelor of Science (Chemistry and Physics)",
        "degree", "science", _SCI_DEG, 4, "98801-CAP", CSET),

    _pc("Bachelor of Science (Mathematics and Physics)",
        "degree", "science", _SCI_DEG, 4, "98801-MAP", CSET),

    _pc("Bachelor of Science in Computing",
        "degree", "technology", _SCI_DEG, 4, "98906-COM", CSET),

    _pc("Bachelor of Science in Informatics",
        "degree", "technology", _SCI_DEG, 4, "98907-INF", CSET),

    # ══ College of Economic & Management Sciences ════════════════════════════

    _pc("Higher Certificate in Economic and Management Sciences",
        "higher_certificate", "business", [_E3], 1, "98237", CEMS),

    _pc("Higher Certificate in Marketing",
        "higher_certificate", "business", [_E3], 1, "98229", CEMS),

    _pc("Higher Certificate in Tourism Management",
        "higher_certificate", "business", [_E3], 1, "98226", CEMS),

    _pc("Diploma in Human Resource Management",
        "diploma", "business", _DIP_LANG, 3, "98211", CEMS),

    _pc("Diploma in Marketing Management",
        "diploma", "business", _DIP_LANG, 3, "98202", CEMS),

    _pc("Diploma in Public Administration and Management",
        "diploma", "business", _DIP_LANG, 3, "98203", CEMS),

    _pc("Diploma in Tourism Management",
        "diploma", "business", _DIP_LANG, 3, "98223", CEMS),

    _pc("Diploma in Safety Management",
        "diploma", "business", _DIP_LANG, 3, "90107", CEMS),

    _pc("Bachelor of Administration",
        "degree", "business", _DEG_LANG, 4, "98315", CEMS),

    _pc("Bachelor of Business Administration",
        "degree", "business", [_E4, _M4], 4, "98316", CEMS),

    _pc("Bachelor of Commerce (General)",
        "degree", "business", [_E4, _M4], 4, "98314-GEN", CEMS),

    _pc("Bachelor of Commerce in Business Management",
        "degree", "business", [_E4, _M4], 4, "98310-BSM", CEMS),

    _pc("Bachelor of Commerce in Economics",
        "degree", "business", [_E4, _M4], 4, "98305-ECS", CEMS),

    _pc("Bachelor of Commerce in Financial Management",
        "degree", "business", [_E4, _M4], 4, "98309-FMS", CEMS),

    _pc("Bachelor of Commerce in Human Resource Management",
        "degree", "business", [_E4, _M4], 4, "98311-HRM", CEMS),

    _pc("Bachelor of Commerce in Marketing Management",
        "degree", "business", [_E4, _M4], 4, "98312-MKT", CEMS),

    _pc("Bachelor of Commerce in Public Administration",
        "degree", "business", [_E4, _M4], 4, "98313-PAD", CEMS),

    # ══ College of Law ═══════════════════════════════════════════════════════

    _pc("Higher Certificate in Criminal Justice",
        "higher_certificate", "law", [_E2], 1, "90006", CLAW),

    _pc("Higher Certificate in Law",
        "higher_certificate", "law", [_E2], 1, "98751", CLAW),

    _pc("Diploma in Law",
        "diploma", "law", _DIP_LANG, 3, "98750", CLAW),

    _pc("Diploma in Policing",
        "diploma", "law", _DIP_LANG, 3, "98220", CLAW),

    _pc("Diploma in Corrections Management",
        "diploma", "law", _DIP_LANG, 3, "98218", CLAW),

    _pc("Bachelor of Arts in Criminology",
        "degree", "law", _DEG_LANG, 4, "98681", CLAW),

    _pc("Bachelor of Commerce in Law",
        "degree", "law", [_E4, _M4], 4, "90123-LAW", CLAW),

    _pc("Bachelor of Laws (LLB)",
        "degree", "law", [_E4], 4, "98680-NEW", CLAW),

    # ══ College of Human Sciences ════════════════════════════════════════════

    _pc("Higher Certificate in Social Auxiliary Work",
        "higher_certificate", "social_sciences", [_E3], 1, "90011", CHSC),

    _pc("Bachelor of Arts in Psychology",
        "degree", "social_sciences", _DEG_LANG, 4, "90180", CHSC),

    _pc("Bachelor of Arts in Community Development",
        "degree", "social_sciences", _DEG_LANG, 4, "98618", CHSC),

    _pc("Bachelor of Arts in International Relations",
        "degree", "social_sciences", _DEG_LANG, 4, "99302", CHSC),

    _pc("Bachelor of Arts in Development Studies",
        "degree", "social_sciences", _DEG_LANG, 4, "99312", CHSC),

    _pc("Bachelor of Arts in Communication Studies",
        "degree", "arts", _DEG_LANG, 4, "90186", CHSC),

    _pc("Bachelor of Arts in Creative Writing",
        "degree", "arts", _DEG_LANG, 4, "99313", CHSC),

    _pc("Bachelor of Arts in Politics, Philosophy and Economics",
        "degree", "social_sciences", _DEG_LANG, 4, "90079", CHSC),

    _pc("Bachelor of Social Work",
        "degree", "social_sciences", _DEG_LANG, 4, "90088", CHSC),

    _pc("Bachelor of Theology",
        "degree", "arts", _DEG_LANG, 4, "90160", CHSC),

    _pc("Bachelor of Information Science",
        "degree", "technology", _DEG_LANG, 4, "90188", CHSC),

    _pc("Bachelor of Music",
        "degree", "arts", _DEG_LANG, 4, "90089", CHSC),

    # ══ College of Agriculture & Environmental Sciences ═══════════════════

    _pc("Higher Certificate in Life and Environmental Sciences",
        "higher_certificate", "science", [_E3, _L3], 1, "98366", CAES),

    _pc("Higher Certificate in Animal Welfare",
        "higher_certificate", "science", [_E3], 1, "90098", CAES),

    _pc("Diploma in Agricultural Management",
        "diploma", "science", [_E4, _L3], 3, "90097", CAES),

    _pc("Diploma in Animal Health",
        "diploma", "science", [_E4, _L3], 3, "98026", CAES),

    _pc("Diploma in Nature Conservation",
        "diploma", "science", [_E4, _L3], 3, "98024", CAES),

    _pc("Advanced Diploma in Agricultural Management",
        "advanced_diploma", "science", [_E4, _L3], 2, "98027", CAES),

    _pc("Advanced Diploma in Nature Conservation",
        "advanced_diploma", "science", [_E4, _L3], 2, "98028", CAES),

    _pc("Bachelor of Science in Agricultural Science (Animal Science)",
        "degree", "science", _AGR_DEG, 4, "90082-ANS", CAES),

    _pc("Bachelor of Science in Agricultural Science (Plant Science)",
        "degree", "science", _AGR_DEG, 4, "90082-PLS", CAES),

    _pc("Bachelor of Science in Life Sciences (Biochemistry and Microbiology)",
        "degree", "science", _AGR_DEG, 4, "98053-BMB", CAES),

    _pc("Bachelor of Science in Life Sciences (Biotechnology)",
        "degree", "science", _AGR_DEG, 4, "98053-BTE", CAES),

    _pc("Bachelor of Science in Environmental Management",
        "degree", "science", _AGR_DEG, 4, "98052", CAES),

    _pc("Bachelor of Consumer Science in Food and Nutrition",
        "degree", "health", [_E4, _L4], 4, "98005-FNT", CAES),

    _pc("Bachelor of Consumer Science in Hospitality Management",
        "degree", "business", _DEG_LANG, 4, "98005-HSP", CAES),

    # ══ EXPANDED ENTRIES ════════════════════════════════════════════════════

    # College of Science, Engineering & Technology — additional BSc combinations
    _pc("Bachelor of Science (Applied Mathematics and Physics)",
        "degree", "science", _SCI_DEG, 4, "98801-AMP", CSET),

    _pc("Bachelor of Science (Applied Mathematics and Statistics)",
        "degree", "science", _SCI_DEG, 4, "98801-AMS", CSET),

    _pc("Bachelor of Science (Chemistry and Applied Mathematics)",
        "degree", "science", _SCI_DEG, 4, "98801-CAM", CSET),

    _pc("Bachelor of Science (Chemistry and Computer Science)",
        "degree", "science", _SCI_DEG, 4, "98801-CCS", CSET),

    _pc("Bachelor of Science (Chemistry and Information Systems)",
        "degree", "science", _SCI_DEG, 4, "98801-CIS", CSET),

    _pc("Bachelor of Science (Chemistry and Statistics)",
        "degree", "science", _SCI_DEG, 4, "98801-CAS", CSET),

    _pc("Bachelor of Science (Mathematics and Applied Mathematics)",
        "degree", "science", _SCI_DEG, 4, "98801-MAM", CSET),

    _pc("Bachelor of Science (Mathematics and Chemistry)",
        "degree", "science", _SCI_DEG, 4, "98801-MAC", CSET),

    _pc("Bachelor of Science (Mathematics and Information Systems)",
        "degree", "technology", _SCI_DEG, 4, "98801-MIS", CSET),

    _pc("Bachelor of Science (Statistics and Physics)",
        "degree", "science", _SCI_DEG, 4, "98801-STP", CSET),

    _pc("Bachelor of Science General",
        "degree", "science", _SCI_DEG, 4, "98801-GEN", CSET),

    _pc("Advanced Diploma in Engineering Technology in Civil Engineering",
        "advanced_diploma", "engineering", _ENG_DIP, 2, "90142", CSET),

    _pc("Advanced Diploma in Information Resource Management",
        "advanced_diploma", "technology", _DIP_LANG, 2, "90007", CSET),

    _pc("Diploma in Pulp and Paper Technology",
        "diploma", "engineering", _ENG_DIP, 3, "90141", CSET),

    # College of Human Sciences — additional programmes
    _pc("Higher Certificate in Archives and Records Management",
        "higher_certificate", "arts", [_E3], 1, "98577", CHSC),

    _pc("Higher Certificate in Supervisory Management",
        "higher_certificate", "business", [_E3], 1, "90015", CHSC),

    _pc("Diploma in Public Relations",
        "diploma", "arts", _DIP_LANG, 3, "90077", CHSC),

    _pc("Bachelor of Arts in Government, Administration and Development",
        "degree", "social_sciences", _DEG_LANG, 4, "99301", CHSC),

    _pc("Bachelor of Arts in Environmental Management",
        "degree", "social_sciences", _DEG_LANG, 4, "98055", CHSC),

    _pc("Bachelor of Arts in Policy Studies",
        "degree", "social_sciences", _DEG_LANG, 4, "99303", CHSC),

    _pc("Bachelor of Arts in Political Leadership and Citizenship",
        "degree", "social_sciences", _DEG_LANG, 4, "99304", CHSC),

    _pc("Bachelor of Arts in Visual Multimedia Arts",
        "degree", "arts", _DEG_LANG, 4, "90091", CHSC),

    _pc("Bachelor of Arts (African Languages and Linguistics)",
        "degree", "arts", _DEG_LANG, 4, "99311-ALL", CHSC),

    _pc("Bachelor of Arts (African Languages and Psychology)",
        "degree", "social_sciences", _DEG_LANG, 4, "99311-ALP", CHSC),

    _pc("Bachelor of Arts (Communication Studies and Public Administration)",
        "degree", "social_sciences", _DEG_LANG, 4, "99311-CSA", CHSC),

    _pc("Bachelor of Arts (Development Studies and Public Administration)",
        "degree", "social_sciences", _DEG_LANG, 4, "99311-DPA", CHSC),

    _pc("Bachelor of Arts (General)",
        "degree", "arts", _DEG_LANG, 4, "99311-GEN", CHSC),

    # College of Agriculture & Environmental Sciences — additional programmes
    _pc("Advanced Diploma in Animal Health",
        "advanced_diploma", "science", [_E4, _L3], 2, "90112", CAES),

    _pc("Advanced Diploma in Ornamental and Landscape Horticulture",
        "advanced_diploma", "science", _DIP_LANG, 2, "90094", CAES),

    _pc("Diploma in Ornamental Horticulture",
        "diploma", "science", [_E4, _M4, _P4], 3, "98025-HOR", CAES),

    _pc("Bachelor of Science in Agricultural Science (Agricultural Business and Management)",
        "degree", "science", _AGR_DEG, 4, "90082-ABM", CAES),

    _pc("Bachelor of Science in Life Sciences (Biochemistry and Botany)",
        "degree", "science", _AGR_DEG, 4, "98053-BAB", CAES),

    _pc("Bachelor of Science in Life Sciences (Genetics and Zoology)",
        "degree", "science", _AGR_DEG, 4, "98053-GZB", CAES),

    _pc("Bachelor of Science in Life Sciences (Botany and Zoology)",
        "degree", "science", _AGR_DEG, 4, "98053-BZG", CAES),

    _pc("Bachelor of Science in Environmental Management (Botany)",
        "degree", "science", _AGR_DEG, 4, "98052-EBO", CAES),

    _pc("Bachelor of Science in Environmental Management (Chemistry)",
        "degree", "science", _AGR_DEG, 4, "98052-ECH", CAES),

    _pc("Bachelor of Science in Environmental Management (Zoology)",
        "degree", "science", _AGR_DEG, 4, "98052-EZO", CAES),

    _pc("Bachelor of Consumer Science in Food and Clothing",
        "degree", "business", _DEG_LANG, 4, "98005-FCL", CAES),

    _pc("Bachelor of Consumer Science in Fashion Retail Management",
        "degree", "business", _DEG_LANG, 4, "98005-FAR", CAES),

    _pc("Bachelor of Consumer Science in Food Service Management",
        "degree", "business", _DEG_LANG, 4, "98005-FSM", CAES),

    _pc("Bachelor of Consumer Science in Fashion Small-Business Management",
        "degree", "business", _DEG_LANG, 4, "98005-FSB", CAES),

    # College of Economic & Management Sciences — additional programmes
    _pc("Higher Certificate in Banking",
        "higher_certificate", "business", [_E3], 1, "98225", CEMS),

    _pc("Higher Certificate in Retailing",
        "higher_certificate", "business", [_E3], 1, "90014", CEMS),

    _pc("Diploma in Administrative Management",
        "diploma", "business", _DIP_LANG, 3, "98216", CEMS),

    _pc("Diploma in Explosives Management",
        "diploma", "business", _DIP_LANG, 3, "98222", CEMS),

    _pc("Diploma in Local Government Finance",
        "diploma", "business", [_E4, _M3], 3, "90083", CEMS),

    _pc("Diploma in Operations Management",
        "diploma", "business", _DIP_LANG, 3, "90183", CEMS),

    _pc("Diploma in Small Business Management",
        "diploma", "business", _DIP_LANG, 3, "90073", CEMS),

    _pc("Advanced Diploma in Explosives Management",
        "advanced_diploma", "business", _DIP_LANG, 2, "90124", CEMS),

    _pc("Advanced Diploma in Safety Management",
        "advanced_diploma", "business", _DIP_LANG, 2, "90181", CEMS),

    _pc("Advanced Diploma in Tourism Management",
        "advanced_diploma", "business", _DIP_LANG, 2, "90118", CEMS),

    _pc("Bachelor of Administration in Human Settlements Management",
        "degree", "business", _DEG_LANG, 4, "90016-HSM", CEMS),

    # College of Law — additional programmes
    _pc("Diploma in Security Management",
        "diploma", "law", _DIP_LANG, 3, "98221", CLAW),

    _pc("Advanced Diploma in Security Management",
        "advanced_diploma", "law", _DIP_LANG, 2, "98235", CLAW),

    _pc("Bachelor of Arts in Police Science",
        "degree", "law", _DEG_LANG, 4, "98683", CLAW),

    _pc("Bachelor of Arts in Forensic Science and Technology",
        "degree", "law", [_E4, _M4], 4, "90002", CLAW),

    # College of Education — additional programmes
    _pc("Advanced Diploma in Education in Intermediate Phase Mathematics Teaching",
        "advanced_diploma", "education", [_E4, _M4], 2, "90113", CEDU),
]


# ---------------------------------------------------------------------------
def parse_unisa() -> List[ParsedCourse]:
    seen: set = set()
    out: List[ParsedCourse] = []
    for pc in SEED:
        key = (pc.name.lower(), pc.level, pc.campus)
        if key not in seen:
            seen.add(key)
            out.append(pc)
    return out


def parse_unisa_url(url: str, institution_short_name: str = "UNISA") -> List[ParsedCourse]:
    return parse_unisa()
