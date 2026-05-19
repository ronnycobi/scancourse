"""
Combine multiple APSResults into a single "best marks" snapshot.

Real-world flow: a student might:
  - Have a Grade 11 report
  - Then a Grade 12 NSC final
  - Then write a supplementary / re-mark
  - Then upgrade a subject through an online programme

SA universities calculate APS from the **highest mark per subject across
all sittings**. This module does the same — picks the best mark per
normalised subject name, then recomputes total APS.
"""
from __future__ import annotations

from typing import Iterable

from .aps_calculator import calculate_aps
from .models import APSResult


def merge_results(results: Iterable[APSResult]) -> dict:
    """
    Take an iterable of APSResults and return:
        {
            'total_aps':     int,
            'subjects':      [...best mark per subject...],
            'report_count':  int,
            'source_reports': [APSResult ids contributing the winning mark],
        }
    """
    best_by_subject: dict[str, dict] = {}
    contributing: set[int] = set()
    n_results = 0

    for ar in results:
        n_results += 1
        for s in (ar.subjects_data or []):
            key = (s.get('normalized_name') or s.get('name', '')).lower().strip()
            if not key:
                continue
            mark = s.get('mark')
            if not isinstance(mark, (int, float)):
                continue
            current = best_by_subject.get(key)
            if current is None or mark > current.get('mark', 0):
                # Snapshot this subject's row; remember which APSResult it came from.
                best_by_subject[key] = {**s, '_source_apsresult_id': ar.pk}

    # Re-run the canonical APS calculator so we use the same rules
    # (drop LO, take top 6, etc.) instead of summing manually.
    if best_by_subject:
        canonical = calculate_aps([
            {'name': v.get('name', k), 'mark': v['mark']}
            for k, v in best_by_subject.items()
        ])
        for src_id, s in [(v['_source_apsresult_id'], v) for v in best_by_subject.values()]:
            contributing.add(src_id)
        return {
            'total_aps': canonical['total_aps'],
            'subjects': canonical['subjects'],
            'report_count': n_results,
            'source_reports': sorted(contributing),
        }

    return {
        'total_aps': 0,
        'subjects': [],
        'report_count': n_results,
        'source_reports': [],
    }


def best_aps_for_user(user) -> dict:
    """
    Public helper: best-marks-across-all-reports snapshot for a user.
    Returns the same dict shape as merge_results().
    """
    qs = (
        APSResult.objects.filter(user=user)
        .exclude(total_aps=0)
        .order_by('-created_at')
    )
    return merge_results(qs)
