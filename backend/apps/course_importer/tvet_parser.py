"""TVET college programme definitions — nationally standardised, 2025/2026.

All 50 public TVET colleges offer the same core NCV and NATED programmes
set by DHET/Umalusi. No APS gate applies; entry is by prior qualification level.

NCV (National Certificate Vocational) — NQF Levels 2, 3, 4:
  Entry: Grade 9 pass (Level 2), then progression through 3 & 4.
  Duration: 3 years to complete all three levels.

NATED / Report 191 Engineering (N1–N3):
  Entry: Grade 9 pass or Grade 12.
  Duration: 18 months (3 semesters of 6 months each).

NATED / Report 191 Business Studies (N4–N6):
  Entry: Grade 12 or N3 certificate.
  Duration: 18 months (3 semesters of 6 months each).
  Leads to: National Diploma (N6 + 18 months practical experience).
"""
from __future__ import annotations
from typing import List
from .parser import ParsedCourse


def _prog(
    name: str,
    level: str,
    field: str,
    duration_years: float,
    description: str,
) -> dict:
    """Return a programme definition dict (not ParsedCourse — applied per college)."""
    return dict(
        name=name,
        level=level,
        field=field,
        duration_years=duration_years,
        description=description,
        min_aps=0,
        subject_requirements=[],
    )


# ---------------------------------------------------------------------------
# Nationally standardised TVET programmes
# ---------------------------------------------------------------------------

NCV_PROGRAMMES = [
    _prog(
        "NCV: Engineering and Related Design",
        "nc_v", "engineering", 3,
        "National Certificate Vocational in Engineering and Related Design (NQF Levels 2–4). "
        "Covers fitting and turning, electrical, mechanical drawing, and construction trade skills. "
        "Entry requires a Grade 9 pass. Prepares students for trade apprenticeships and artisan careers.",
    ),
    _prog(
        "NCV: Business, Commerce and Management Studies",
        "nc_v", "business", 3,
        "National Certificate Vocational in Business, Commerce and Management Studies (NQF Levels 2–4). "
        "Covers entrepreneurship, business operations, marketing, and management practice. "
        "Entry requires a Grade 9 pass. Prepares students for SME management and commerce careers.",
    ),
    _prog(
        "NCV: Finance, Economics and Accounting",
        "nc_v", "business", 3,
        "National Certificate Vocational in Finance, Economics and Accounting (NQF Levels 2–4). "
        "Covers financial literacy, bookkeeping, accounting principles, and economics. "
        "Entry requires a Grade 9 pass. Prepares students for finance and accounting support roles.",
    ),
    _prog(
        "NCV: Hospitality",
        "nc_v", "business", 3,
        "National Certificate Vocational in Hospitality (NQF Levels 2–4). "
        "Covers food preparation, accommodation services, front office operations, and food and beverages. "
        "Entry requires a Grade 9 pass. Prepares students for the hotel and catering industry.",
    ),
    _prog(
        "NCV: Information Technology and Computer Science",
        "nc_v", "technology", 3,
        "National Certificate Vocational in Information Technology and Computer Science (NQF Levels 2–4). "
        "Covers computer hardware, networking, programming fundamentals, and IT support. "
        "Entry requires a Grade 9 pass. Prepares students for entry-level IT and technical support roles.",
    ),
    _prog(
        "NCV: Office Administration",
        "nc_v", "business", 3,
        "National Certificate Vocational in Office Administration (NQF Levels 2–4). "
        "Covers office practice, communication, record keeping, and business writing. "
        "Entry requires a Grade 9 pass. Prepares students for administrative and clerical roles.",
    ),
    _prog(
        "NCV: Primary Agriculture",
        "nc_v", "science", 3,
        "National Certificate Vocational in Primary Agriculture (NQF Levels 2–4). "
        "Covers plant and animal production, soil science, and agricultural practice. "
        "Entry requires a Grade 9 pass. Prepares students for farming and agribusiness support roles.",
    ),
    _prog(
        "NCV: Tourism",
        "nc_v", "business", 3,
        "National Certificate Vocational in Tourism (NQF Levels 2–4). "
        "Covers tourism operations, travel services, guiding, and customer care. "
        "Entry requires a Grade 9 pass. Prepares students for the tourism and travel industry.",
    ),
]

NATED_N1_N3 = [
    _prog(
        "NATED N1–N3: Electrical Engineering",
        "n1_n6", "engineering", 2,
        "NATED Engineering Studies in Electrical Engineering (N1–N3, Report 191). "
        "Covers electrical theory, electronics, industrial electronics, and mathematics. "
        "Entry requires a Grade 9 pass or Grade 12. "
        "N3 qualifies for trade test entry and further N4–N6 study.",
    ),
    _prog(
        "NATED N1–N3: Mechanical Engineering",
        "n1_n6", "engineering", 2,
        "NATED Engineering Studies in Mechanical Engineering (N1–N3, Report 191). "
        "Covers mechanotechnology, engineering science, fitting and machining, and mathematics. "
        "Entry requires a Grade 9 pass or Grade 12. "
        "N3 qualifies for trade test entry and artisan apprenticeship.",
    ),
    _prog(
        "NATED N1–N3: Civil Engineering",
        "n1_n6", "engineering", 2,
        "NATED Engineering Studies in Civil Engineering (N1–N3, Report 191). "
        "Covers building and structural surveys, building science, and mathematics. "
        "Entry requires a Grade 9 pass or Grade 12. "
        "N3 qualifies students for construction industry entry and N4–N6 study.",
    ),
    _prog(
        "NATED N1–N3: Motor Vehicle Theory",
        "n1_n6", "engineering", 2,
        "NATED Engineering Studies in Motor Vehicle Theory (N1–N3, Report 191). "
        "Covers motor vehicle science, vehicle systems, and trade-related mathematics. "
        "Entry requires a Grade 9 pass or Grade 12. "
        "N3 qualifies for motor mechanic trade test entry.",
    ),
]

NATED_N4_N6 = [
    _prog(
        "NATED N4–N6: Business Management",
        "diploma", "business", 2,
        "NATED Business Studies in Business Management (N4–N6, Report 191). "
        "Covers entrepreneurship, business law, economics, and management principles. "
        "Entry requires a Grade 12 or N3 certificate. "
        "N6 plus 18 months practical experience leads to a National Diploma.",
    ),
    _prog(
        "NATED N4–N6: Financial Management",
        "diploma", "business", 2,
        "NATED Business Studies in Financial Management (N4–N6, Report 191). "
        "Covers financial accounting, cost and management accounting, and taxation. "
        "Entry requires a Grade 12 or N3 certificate. "
        "N6 plus 18 months practical experience leads to a National Diploma.",
    ),
    _prog(
        "NATED N4–N6: Human Resource Management",
        "diploma", "business", 2,
        "NATED Business Studies in Human Resource Management (N4–N6, Report 191). "
        "Covers labour relations, personnel management, and organisational behaviour. "
        "Entry requires a Grade 12 or N3 certificate. "
        "N6 plus 18 months practical experience leads to a National Diploma.",
    ),
    _prog(
        "NATED N4–N6: Marketing Management",
        "diploma", "business", 2,
        "NATED Business Studies in Marketing Management (N4–N6, Report 191). "
        "Covers marketing principles, sales management, advertising, and consumer behaviour. "
        "Entry requires a Grade 12 or N3 certificate. "
        "N6 plus 18 months practical experience leads to a National Diploma.",
    ),
    _prog(
        "NATED N4–N6: Public Management",
        "diploma", "business", 2,
        "NATED Business Studies in Public Management (N4–N6, Report 191). "
        "Covers public administration, municipal governance, and public finance. "
        "Entry requires a Grade 12 or N3 certificate. "
        "N6 plus 18 months practical experience leads to a National Diploma.",
    ),
]

ALL_TVET_PROGRAMMES = NCV_PROGRAMMES + NATED_N1_N3 + NATED_N4_N6


def get_tvet_programmes() -> List[dict]:
    """Return all standardised TVET programme definitions."""
    return ALL_TVET_PROGRAMMES
