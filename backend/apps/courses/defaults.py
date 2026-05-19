"""
Sensible default NSC subject requirements per field + level.

When a scraper can't extract the exact subject prerequisites from the source,
we fall back to these realistic SA-wide defaults. Students can use the data
for course matching, and the admin can fine-tune per offering.

NSC Levels:
  7 = 80%+    6 = 70-79%   5 = 60-69%   4 = 50-59%
  3 = 40-49%  2 = 30-39%   1 = 0-29%

These reflect typical undergraduate admission standards across SA universities.
"""

DEFAULT_SUBJECT_REQUIREMENTS: dict[tuple[str, str], list[dict]] = {
    # ── Engineering & Built Environment ──
    ('engineering', 'degree'): [
        {'subject': 'English', 'min_level': 5},
        {'subject': 'Mathematics', 'min_level': 6},
        {'subject': 'Physical Sciences', 'min_level': 5},
    ],
    ('engineering', 'diploma'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 4},
    ],
    ('built_environment', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 4},
    ],
    ('built_environment', 'diploma'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 4},
    ],

    # ── Health Sciences ──
    ('health', 'degree'): [
        {'subject': 'English', 'min_level': 5},
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 5},
        {'subject': 'Life Sciences', 'min_level': 5},
    ],
    ('health', 'diploma'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 4},
        {'subject': 'Life Sciences', 'min_level': 4},
    ],

    # ── Science (BSc) ──
    ('science', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 5},
        {'subject': 'Physical Sciences', 'min_level': 4},
    ],
    ('science', 'diploma'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 4},
    ],

    # ── Business / Commerce (BCom) ──
    ('business', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 4},
    ],
    ('business', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
        {'subject': 'Mathematics', 'min_level': 3},
    ],

    # ── ICT / Computing ──
    ('ict', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 5},
    ],
    ('ict', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
        {'subject': 'Mathematics', 'min_level': 4},
    ],

    # ── Law (LLB) ──
    ('law', 'degree'): [
        {'subject': 'English', 'min_level': 5},
        {'subject': 'Mathematics', 'min_level': 3},  # OR Math Lit
    ],

    # ── Humanities ──
    ('humanities', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 3},
    ],
    ('humanities', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
    ],

    # ── Education ──
    ('education', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 3},
    ],
    ('education', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
        {'subject': 'Mathematics', 'min_level': 3},
    ],

    # ── Arts & Design ──
    ('arts', 'degree'): [
        {'subject': 'English', 'min_level': 4},
    ],
    ('arts', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
    ],
    ('arts', 'certificate'): [
        {'subject': 'English', 'min_level': 3},
    ],

    # ── Agriculture ──
    ('agriculture', 'degree'): [
        {'subject': 'English', 'min_level': 4},
        {'subject': 'Mathematics', 'min_level': 4},
        {'subject': 'Life Sciences', 'min_level': 4},
    ],
    ('agriculture', 'diploma'): [
        {'subject': 'English', 'min_level': 3},
        {'subject': 'Mathematics', 'min_level': 3},
    ],
}

# Generic baselines used when no specific (field, level) match exists.
GENERIC_DEFAULTS: dict[str, list[dict]] = {
    'degree':            [{'subject': 'English', 'min_level': 4}, {'subject': 'Mathematics', 'min_level': 4}],
    'honours':           [{'subject': 'English', 'min_level': 4}, {'subject': 'Mathematics', 'min_level': 4}],
    'masters':           [{'subject': 'English', 'min_level': 4}],
    'phd':               [{'subject': 'English', 'min_level': 4}],
    'diploma':           [{'subject': 'English', 'min_level': 3}, {'subject': 'Mathematics', 'min_level': 3}],
    'advanced_diploma':  [{'subject': 'English', 'min_level': 4}, {'subject': 'Mathematics', 'min_level': 3}],
    'certificate':       [{'subject': 'English', 'min_level': 3}],
    'n1_n6':             [{'subject': 'English', 'min_level': 2}, {'subject': 'Mathematics', 'min_level': 2}],
    'nc_v':              [{'subject': 'English', 'min_level': 2}],
}


def default_subjects_for(field: str, level: str) -> list[dict]:
    """Return a sensible default list of subject requirements for a (field, level) combination."""
    key = (field or 'other', level or 'degree')
    if key in DEFAULT_SUBJECT_REQUIREMENTS:
        return [r.copy() for r in DEFAULT_SUBJECT_REQUIREMENTS[key]]
    # Fallback to generic by level only
    return [r.copy() for r in GENERIC_DEFAULTS.get(level or 'degree', GENERIC_DEFAULTS['degree'])]
