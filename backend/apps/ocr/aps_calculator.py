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
}

LIFE_ORIENTATION_SUBJECTS = {'life orientation', 'lo'}


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


def calculate_aps(subjects: list[dict]) -> dict:
    """
    subjects: list of {'name': str, 'mark': int}
    Returns: {'total_aps': int, 'subjects': list with aps points, 'eligible_subjects_count': int}
    """
    processed = []
    for subj in subjects:
        name = subj.get('name', '')
        mark = int(subj.get('mark', 0))
        normalized = normalize_subject(name)
        aps_points = mark_to_aps(mark)
        is_lo = is_life_orientation(name)

        processed.append({
            'name': name,
            'normalized_name': normalized,
            'mark': mark,
            'aps_points': aps_points,
            'is_life_orientation': is_lo,
        })

    # APS excludes Life Orientation from the total
    total_aps = sum(
        s['aps_points'] for s in processed if not s['is_life_orientation']
    )

    eligible_count = len([s for s in processed if not s['is_life_orientation']])

    return {
        'total_aps': total_aps,
        'subjects': processed,
        'eligible_subjects_count': eligible_count,
    }
