"""
Bursary matching engine.

Computes a `match` status for each bursary against a student's profile
(APS, average mark, preferred field, province). Statuses:

    'qualified'      — student meets all stated criteria
    'check_details'  — bursary has eligibility text we can't auto-verify
                       (e.g. household income, citizenship clauses)
    'grade_gap'      — student's average is below min_grade_average
    'field_mismatch' — bursary is field-restricted to something else
    'closed'         — application deadline has passed

Note: we can only check criteria encoded as structured fields
(min_grade_average, max_household_income, field, province). Bursaries
that depend on race/income/disability still show as 'check_details'
because we don't have those signals.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .models import Bursary


def _avg_from_aps_subjects(subjects: list[dict]) -> Optional[float]:
    """Estimate the student's overall percentage average from APSResult.subjects_data."""
    if not subjects:
        return None
    marks = [s.get('mark') for s in subjects if not s.get('is_life_orientation')]
    marks = [m for m in marks if isinstance(m, (int, float))]
    if not marks:
        return None
    return sum(marks) / len(marks)


def evaluate_bursary(
    bursary: Bursary,
    *,
    user_aps: int | None = None,
    user_avg: float | None = None,
    user_field: str | None = None,
    user_fields: list[str] | None = None,
    user_province: str | None = None,
    today: date | None = None,
) -> dict:
    """Return a match dict for a single bursary."""
    today = today or date.today()
    deadline = bursary.application_deadline

    # Merge singular + plural preferred fields (onboarding is multi-select).
    fields = set(user_fields or [])
    if user_field:
        fields.add(user_field)

    # 1. Closed?
    if deadline and deadline < today:
        return {
            'status': 'closed',
            'reason': f'Application closed on {deadline.isoformat()}',
            'days_until_deadline': (deadline - today).days,
        }

    days_left = (deadline - today).days if deadline else None

    # 2. Field constraint — only a mismatch if NONE of the student's chosen
    # fields match the bursary's restricted field.
    if bursary.field != 'any' and fields and bursary.field not in fields:
        return {
            'status': 'field_mismatch',
            'reason': f'Bursary is restricted to {bursary.field}; '
                      f'not in your preferred fields',
            'days_until_deadline': days_left,
        }

    # 3. Province constraint (some provincial bursaries are residents-only)
    if bursary.province not in ('ALL', '') and user_province and user_province != bursary.province:
        return {
            'status': 'province_mismatch',
            'reason': f'Bursary is for residents of {bursary.province} only',
            'days_until_deadline': days_left,
        }

    # 4. Grade requirement
    if bursary.min_grade_average and user_avg is not None:
        if user_avg < bursary.min_grade_average:
            return {
                'status': 'grade_gap',
                'reason': (
                    f'Requires {bursary.min_grade_average}% average; '
                    f'your average is {user_avg:.0f}%'
                ),
                'grade_gap': int(bursary.min_grade_average - user_avg),
                'days_until_deadline': days_left,
            }

    # 5. If we have a structured requirement and the student meets it,
    # AND there's no household-income clause to verify, mark as qualified.
    if bursary.max_household_income:
        return {
            'status': 'check_details',
            'reason': (
                f'Household income cap: R{bursary.max_household_income:,}. '
                'Check eligibility on the official application.'
            ),
            'days_until_deadline': days_left,
        }

    # No blockers we can detect from structured fields.
    return {
        'status': 'qualified',
        'reason': 'You meet the published criteria — verify full T&Cs on the official site.',
        'days_until_deadline': days_left,
    }


def match_bursaries(
    bursaries,
    *,
    user_aps: int | None = None,
    user_avg: float | None = None,
    user_field: str | None = None,
    user_fields: list[str] | None = None,
    user_province: str | None = None,
    today: date | None = None,
) -> list[dict]:
    """Evaluate every bursary; return list ordered by qualify status + deadline."""
    today = today or date.today()
    out = []
    for b in bursaries:
        match = evaluate_bursary(
            b,
            user_aps=user_aps,
            user_avg=user_avg,
            user_field=user_field,
            user_fields=user_fields,
            user_province=user_province,
            today=today,
        )
        out.append({'bursary': b, 'match': match})

    out.sort(key=lambda r: (
        STATUS_ORDER.get(r['match']['status'], 99),
        r['bursary'].application_deadline or date.max,
    ))
    return out


# Ordering of match statuses — best/most-actionable first.
STATUS_ORDER = {
    'qualified': 0,
    'check_details': 1,
    'grade_gap': 2,
    'field_mismatch': 3,
    'province_mismatch': 4,
    'closed': 5,
}


def summary(matched: list[dict]) -> dict:
    counts = {'qualified': 0, 'check_details': 0, 'grade_gap': 0,
              'field_mismatch': 0, 'province_mismatch': 0, 'closed': 0}
    for r in matched:
        counts[r['match']['status']] = counts.get(r['match']['status'], 0) + 1
    return counts
