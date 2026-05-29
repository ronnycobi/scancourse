"""
South African APS (Admission Point Score) Calculator.
Uses the standard NSC APS table.
"""

APS_TABLE = {
    (80, 100): 7,
    (70, 79): 6,
    (60, 69): 5,
    (50, 59): 4,
    (40, 49): 3,
    (30, 39): 2,
    (0, 29): 1,
}

SUBJECT_ALIASES = {
    'maths': 'mathematics',
    'math': 'mathematics',
    'mathematics literacy': 'mathematical literacy',
    'maths lit': 'mathematical literacy',
    'math lit': 'mathematical literacy',
    'afrikaans': 'afrikaans home language',
    'english': 'english home language',
    'eng hl': 'english home language',
    'eng fal': 'english first additional language',
    'life orientation': 'life orientation',
    'lo': 'life orientation',
    'physical science': 'physical sciences',
    'phys sci': 'physical sciences',
    'physics': 'physical sciences',
    'life science': 'life sciences',
    'biology': 'life sciences',
    'acc': 'accounting',
    'bus studies': 'business studies',
    'geog': 'geography',
    'hist': 'history',
    'ca': 'computer applications technology',
    'cat': 'computer applications technology',
    'it': 'information technology',
    'ems': 'economic and management sciences',
    # IEB Advanced Programme subjects — extra subjects sat in addition to
    # the 7 NSC subjects. They do NOT count toward standard APS.
    'ap maths': 'advanced programme mathematics',
    'ap mathematics': 'advanced programme mathematics',
    'advanced programme maths': 'advanced programme mathematics',
    'ap english': 'advanced programme english',
    'ap afrikaans': 'advanced programme afrikaans',
}

LIFE_ORIENTATION_SUBJECTS = {'life orientation', 'lo'}

# IEB Advanced Programme subjects. Like Life Orientation, these are
# excluded from the standard APS total (universities may award separate
# bonus points, but they aren't part of the 6-subject APS).
ADVANCED_PROGRAMME_SUBJECTS = {
    'advanced programme mathematics',
    'advanced programme english',
    'advanced programme afrikaans',
}


def mark_to_aps(mark: int) -> int:
    for (low, high), points in APS_TABLE.items():
        if low <= mark <= high:
            return points
    return 0


def normalize_subject(name: str) -> str:
    cleaned = name.lower().strip()
    return SUBJECT_ALIASES.get(cleaned, cleaned)


def is_life_orientation(name: str) -> bool:
    return normalize_subject(name) in LIFE_ORIENTATION_SUBJECTS


def is_advanced_programme(name: str) -> bool:
    return normalize_subject(name) in ADVANCED_PROGRAMME_SUBJECTS


def calculate_aps(subjects: list[dict]) -> dict:
    """
    subjects: list of {'name': str, 'mark': int}
    Returns: {'total_aps': int, 'subjects': list with aps points, 'eligible_subjects_count': int}

    Both Life Orientation and IEB Advanced Programme subjects are flagged
    and excluded from the APS total (they aren't part of the standard
    6-subject APS).
    """
    processed = []
    for subj in subjects:
        name = subj.get('name', '')
        mark = int(subj.get('mark', 0))
        normalized = normalize_subject(name)
        aps_points = mark_to_aps(mark)
        is_lo = is_life_orientation(name)
        is_ap = is_advanced_programme(name)

        processed.append({
            'name': name,
            'normalized_name': normalized,
            'mark': mark,
            'aps_points': aps_points,
            'is_life_orientation': is_lo,
            'is_advanced_programme': is_ap,
            # Eligible to count toward APS at all (i.e. not LO/AP).
            'counts_in_aps': not (is_lo or is_ap),
            # Set below: whether it actually made the best-6 used for APS.
            'counted_in_aps': False,
        })

    # SA universities compute APS from the student's BEST 6 subjects,
    # excluding Life Orientation and IEB Advanced Programme subjects.
    # Many learners (especially IEB) take 8-11 subjects, so we must pick
    # the top 6 by points rather than summing everything.
    eligible = [s for s in processed if s['counts_in_aps']]
    top6 = sorted(eligible, key=lambda s: s['aps_points'], reverse=True)[:6]
    for s in top6:
        s['counted_in_aps'] = True

    total_aps = sum(s['aps_points'] for s in top6)

    return {
        'total_aps': total_aps,
        'subjects': processed,
        'eligible_subjects_count': len(eligible),
        'counted_subjects_count': len(top6),
    }
