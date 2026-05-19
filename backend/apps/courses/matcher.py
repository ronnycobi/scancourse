"""
Course matching engine.

Scores each active CourseOffering against a student's APS, subjects, and
profile preferences (dream career, preferred field). Returns offerings
bucketed by qualification (eligible / subject_gap / aps_gap / not_qualified)
and ranked by a relevance score within each bucket.

Subject requirements live in CourseOffering.subject_requirements (JSONField):
    [{"subject": "Mathematics", "min_level": 5}, ...]

Student subjects come from APSResult.subjects_data:
    [{"normalized_name": "mathematics", "aps_points": 6, ...}, ...]
"""
from __future__ import annotations

import re

from .models import CourseOffering


# ── Subject name normalisation ────────────────────────────────────────────────

_AFRICAN_LANGS = {
    'zulu', 'isizulu',
    'xhosa', 'isixhosa',
    'sotho', 'sesotho', 'northern sotho', 'sepedi',
    'tswana', 'setswana',
    'venda', 'tshivenda',
    'tsonga', 'xitsonga',
    'swati', 'siswati',
    'ndebele', 'isindebele',
    'afrikaans',
}

# Requirement subject name → set of normalised student subject names that satisfy it.
REQUIREMENT_TO_STUDENT: dict[str, set[str]] = {
    'english': {
        'english', 'english home language', 'english first additional language',
        'english second additional language', 'english sal', 'english fal',
        'english hl', 'eng hl', 'eng fal', 'eng sal',
    },
    'mathematics': {'mathematics', 'maths', 'math', 'pure mathematics'},
    'mathematical literacy': {
        'mathematical literacy', 'mathematics literacy', 'maths lit', 'math lit',
        'maths literacy',
    },
    'physical sciences': {
        'physical sciences', 'physical science', 'physics',
    },
    'life sciences': {'life sciences', 'life science', 'biology', 'bio'},
    'accounting': {'accounting', 'acc'},
    'business studies': {'business studies', 'business', 'business study'},
    'economics': {'economics', 'econ'},
    'geography': {'geography', 'geog'},
    'history': {'history', 'hist'},
    'information technology': {'information technology', 'it'},
    'computer applications technology': {
        'computer applications technology', 'cat', 'ca',
    },
    'tourism': {'tourism'},
    'dramatic arts': {'dramatic arts', 'drama'},
    'music': {'music'},
    'visual arts': {'visual arts', 'art'},
    'design': {'design'},
    'agricultural sciences': {
        'agricultural sciences', 'agriculture', 'agricultural science',
    },
    'consumer studies': {'consumer studies', 'consumer'},
    'african language': _AFRICAN_LANGS,
}

_MATHS_LIT_NAMES = REQUIREMENT_TO_STUDENT['mathematical literacy']


def _norm(name: str) -> str:
    return name.lower().strip()


def _strip_language_suffix(name: str) -> str:
    """Strip 'home language', 'first additional language', 'hl', 'fal', etc."""
    n = name
    for suffix in (
        'second additional language', 'first additional language',
        'home language', 'additional language', 'language',
        'hl', 'fal', 'sal',
    ):
        n = re.sub(rf'\b{suffix}\b', '', n).strip()
    return re.sub(r'\s+', ' ', n).strip()


def _student_has_language(student_subjects: list[dict], lang_set: set[str]) -> bool:
    for s in student_subjects:
        s_norm = _norm(s.get('normalized_name') or s.get('name', ''))
        if s_norm in lang_set or _strip_language_suffix(s_norm) in lang_set:
            return True
    return False


def _student_level(student_subjects: list[dict], requirement_name: str) -> int | None:
    """Return the student's APS level for a given requirement name, or None."""
    req_norm = _norm(requirement_name)
    accepted = REQUIREMENT_TO_STUDENT.get(req_norm)

    for subj in student_subjects:
        s_norm = _norm(subj.get('normalized_name') or subj.get('name', ''))
        s_stripped = _strip_language_suffix(s_norm)

        if accepted:
            if s_norm in accepted or s_stripped in accepted:
                return subj.get('aps_points', 0)
        else:
            # Fallback: direct normalised name match
            target = req_norm.replace(' ', '')
            if (
                s_norm == req_norm
                or s_norm.replace(' ', '') == target
                or s_stripped == req_norm
            ):
                return subj.get('aps_points', 0)
    return None


def _has_maths_literacy(student_subjects: list[dict]) -> bool:
    return any(
        _norm(s.get('normalized_name') or s.get('name', '')) in _MATHS_LIT_NAMES
        for s in student_subjects
    )


def _has_pure_maths(student_subjects: list[dict]) -> bool:
    pure = REQUIREMENT_TO_STUDENT['mathematics']
    return any(
        _norm(s.get('normalized_name') or s.get('name', '')) in pure
        for s in student_subjects
    )


# ── Dream career → field keyword map ─────────────────────────────────────────

DREAM_CAREER_KEYWORDS: dict[str, list[str]] = {
    'business': ['account', 'finance', 'business', 'econom', 'bank', 'commerce',
                 'audit', 'tax', 'market', 'entrepreneur', 'manage', 'invest'],
    'health':   ['doctor', 'nurse', 'pharm', 'medic', 'dentist', 'surgeon',
                 'health', 'physio', 'radiograph', 'optom', 'paramedic'],
    'engineering': ['engineer', 'mechanic', 'electric', 'civil', 'chemical',
                    'mining', 'aerospace', 'industrial'],
    'education': ['teach', 'educat', 'lecturer', 'tutor', 'professor'],
    'law': ['law', 'attorney', 'advocate', 'legal', 'judge', 'paralegal'],
    'arts': ['artist', 'design', 'graphic', 'fashion', 'film', 'music',
             'photograph', 'animat', 'creative'],
    'agriculture': ['farm', 'agricultur', 'vet', 'crop'],
    'ict': ['program', 'develop', 'software', 'computer', 'cyber', 'data scien',
            'it ', 'network', 'web', 'mobile dev', 'devops'],
    'science': ['scientist', 'biolog', 'chemist', 'physics', 'research',
                'geolog', 'astron', 'environ'],
    'built_environment': ['architect', 'plann', 'survey', 'construct', 'propert',
                          'urban'],
    'humanities': ['journalist', 'writer', 'psycholog', 'social work',
                   'communic', 'translat'],
}


def _career_keywords(career: str | None) -> list[str]:
    if not career:
        return []
    c = career.lower()
    return [kw for kws in DREAM_CAREER_KEYWORDS.values() for kw in kws if kw in c] + [c]


def _field_for_career(career: str | None) -> str | None:
    if not career:
        return None
    c = career.lower()
    for field, kws in DREAM_CAREER_KEYWORDS.items():
        if any(kw in c for kw in kws):
            return field
    return None


# ── Subject → field affinity ──────────────────────────────────────────────────
# Which field each subject naturally points to and how strongly.

SUBJECT_FIELD_AFFINITY: dict[str, dict[str, int]] = {
    'mathematics':         {'engineering': 3, 'science': 3, 'business': 2, 'ict': 3, 'built_environment': 2},
    'physical sciences':   {'engineering': 3, 'health': 3, 'science': 3, 'built_environment': 2},
    'life sciences':       {'health': 3, 'science': 3, 'agriculture': 2, 'education': 1},
    'accounting':          {'business': 3, 'law': 1},
    'business studies':    {'business': 3},
    'economics':           {'business': 3, 'humanities': 1, 'law': 1},
    'geography':           {'science': 2, 'built_environment': 2, 'agriculture': 1, 'humanities': 1},
    'history':             {'humanities': 3, 'law': 2, 'education': 1},
    'information technology': {'ict': 4, 'engineering': 2, 'science': 1},
    'computer applications technology': {'ict': 3, 'business': 1},
    'agricultural sciences': {'agriculture': 3, 'science': 1},
    'visual arts':         {'arts': 3, 'built_environment': 1},
    'dramatic arts':       {'arts': 3, 'humanities': 1, 'education': 1},
    'music':               {'arts': 3, 'humanities': 1},
    'design':              {'arts': 3, 'built_environment': 1, 'ict': 1},
    'consumer studies':    {'business': 1, 'health': 1, 'agriculture': 1},
    'tourism':             {'business': 2, 'humanities': 1},
    'mathematical literacy': {'humanities': 1, 'arts': 1, 'agriculture': 1, 'education': 1},
}


def _subject_field_scores(student_subjects: list[dict]) -> dict[str, float]:
    """
    Aggregate per-field strength based on subjects taken AND how well the
    student did. Score = sum(affinity_weight × (aps_points / 7)).
    Returns field → score.
    """
    out: dict[str, float] = {}
    for s in student_subjects:
        if s.get('is_life_orientation'):
            continue
        name = _norm(s.get('normalized_name') or s.get('name', ''))
        name = _strip_language_suffix(name).strip() or name
        # Try exact match first; then fall back to the requirement map.
        affinities = SUBJECT_FIELD_AFFINITY.get(name)
        if not affinities:
            for req_name, alts in REQUIREMENT_TO_STUDENT.items():
                if name in alts:
                    affinities = SUBJECT_FIELD_AFFINITY.get(req_name)
                    if affinities:
                        break
        if not affinities:
            continue
        pts = (s.get('aps_points') or 0) / 7.0  # 0..1
        for field, weight in affinities.items():
            out[field] = out.get(field, 0.0) + weight * pts
    return out


def _top_subject_fields(student_subjects: list[dict], n: int = 3) -> set[str]:
    scores = _subject_field_scores(student_subjects)
    return {f for f, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:n] if scores[f] > 0}


def _personalization_bonus(
    offering: CourseOffering,
    preferred_field: str | None,
    career: str | None,
    subject_fields: set[str] | None = None,
    career_subject_aligned: bool = True,
) -> int:
    """Score bonus reflecting how well this offering matches the student.

    Subject strengths are treated as the primary signal — a student with
    strong sciences gets a boost on science/engineering/health programmes
    even if their stated dream career doesn't line up. Career and preferred
    field still contribute, but only when the subject profile supports it.
    """
    bonus = 0
    course = offering.course
    field = course.field
    subject_fields = subject_fields or set()

    # Subject-driven affinity — biggest signal: 0-25
    if field in subject_fields:
        bonus += 20

    # Preferred field match — only meaningful if subjects support it
    if preferred_field and field == preferred_field:
        if not subject_fields or field in subject_fields:
            bonus += 12
        else:
            bonus += 4   # weak signal: pref doesn't match subjects

    # Dream career → field match — gated by subject alignment
    career_field = _field_for_career(career)
    if career_field and field == career_field:
        if career_subject_aligned:
            bonus += 10
        else:
            bonus += 3   # career doesn't match subject strengths

    # Keyword overlap with course name / description / career_opportunities
    if career and career_subject_aligned:
        haystack = ' '.join(filter(None, [
            course.name or '',
            course.description or '',
            course.career_opportunities or '',
        ])).lower()
        career_lc = career.lower()
        if career_lc in haystack:
            bonus += 12
        else:
            tokens = [t for t in re.split(r'[^a-z]+', career_lc) if len(t) > 3]
            if any(t in haystack for t in tokens):
                bonus += 4
    return bonus


# ── Per-offering match evaluation ─────────────────────────────────────────────

def _evaluate_offering(
    offering: CourseOffering,
    user_aps: int,
    student_subjects: list[dict],
    has_maths_lit: bool,
    preferred_field: str | None,
    career: str | None,
    subject_fields: set[str] | None = None,
    career_subject_aligned: bool = True,
) -> dict:
    requirements: list[dict] = offering.subject_requirements or []
    institution_type = offering.institution.institution_type
    has_data = bool(requirements) or offering.min_aps > 0

    # TVET: run the full scoring path so college programmes rank by
    # subject fit and APS surplus too — NC(V) Civil Engineering should
    # rank above NC(V) Office Admin for a maths-strong student.
    if institution_type == 'tvet':
        # NC(V) and N1-N3 have no real APS gate → score from subjects/field.
        # N4-N6 carries min_aps and we honour it like a uni programme.
        aps_surplus = user_aps - offering.min_aps if offering.min_aps else 0
        missing: list[dict] = []
        low: list[dict] = []
        for req in requirements:
            req_name = req.get('subject', '')
            req_level = int(req.get('min_level', 4))
            student_lvl = _student_level(student_subjects, req_name)
            if student_lvl is None:
                missing.append({'subject': req_name, 'required_level': req_level,
                                'student_level': None, 'reason': 'subject_not_taken'})
            elif student_lvl < req_level:
                low.append({'subject': req_name, 'required_level': req_level,
                            'student_level': student_lvl, 'gap': req_level - student_lvl})

        aps_ok = offering.min_aps == 0 or aps_surplus >= 0
        subjects_ok = not missing and not low
        # TVETs default to eligible; only flag a gap if both APS and subjects fail.
        if aps_ok and subjects_ok:
            category = 'eligible'
        elif aps_ok:
            category = 'subject_gap'
        elif subjects_ok:
            category = 'aps_gap'
        else:
            category = 'subject_gap'  # be friendly — TVET barriers are usually flexible

        if offering.min_aps == 0:
            aps_score = 30.0  # base score for open-enrolment TVETs (NC(V) L2)
        else:
            aps_score = min(max(aps_surplus + 20, 0), 40) * 1.5
        subject_penalty = (len(missing) * 12) + sum(g['gap'] * 4 for g in low)
        subject_score = max(40 - subject_penalty, 0)
        base = int(aps_score + subject_score) + _level_priority(offering.course.level)
        bonus = _personalization_bonus(offering, preferred_field, career,
                                       subject_fields, career_subject_aligned)
        return {
            'category': category,
            'aps_surplus': aps_surplus,
            'missing_subjects': missing,
            'low_subjects': low,
            'maths_lit_blocked': False,
            'score': base + bonus,
            'tvet': True,
            'placeholder': False,
        }

    # Placeholder data: no requirements AND no APS set.
    # Treat as eligible but heavily downweight so real matches surface first.
    if not has_data:
        bonus = _personalization_bonus(offering, preferred_field, career, subject_fields, career_subject_aligned)
        return {
            'category': 'eligible',
            'aps_surplus': 0,
            'missing_subjects': [],
            'low_subjects': [],
            'maths_lit_blocked': False,
            'score': 10 + bonus,   # base 10 only — real matches always rank higher
            'tvet': False,
            'placeholder': True,
        }

    aps_surplus = user_aps - offering.min_aps
    missing: list[dict] = []
    low: list[dict] = []
    maths_lit_blocked = False

    for req in requirements:
        req_name = req.get('subject', '')
        req_level = int(req.get('min_level', 4))

        if _norm(req_name) == 'mathematics' and has_maths_lit and not _has_pure_maths(student_subjects):
            maths_lit_blocked = True
            missing.append({
                'subject': req_name,
                'required_level': req_level,
                'student_level': None,
                'reason': 'mathematical_literacy_not_accepted',
            })
            continue

        student_lvl = _student_level(student_subjects, req_name)
        if student_lvl is None:
            missing.append({
                'subject': req_name,
                'required_level': req_level,
                'student_level': None,
                'reason': 'subject_not_taken',
            })
        elif student_lvl < req_level:
            low.append({
                'subject': req_name,
                'required_level': req_level,
                'student_level': student_lvl,
                'gap': req_level - student_lvl,
            })

    aps_ok = aps_surplus >= 0
    subjects_ok = not missing and not low

    if aps_ok and subjects_ok:
        category = 'eligible'
    elif aps_ok:
        category = 'subject_gap'
    elif subjects_ok:
        category = 'aps_gap'
    else:
        category = 'not_qualified'

    # Score 0-100 plus personalization bonus (0-30) plus level priority (0-15)
    if offering.min_aps == 0:
        # Open-enrolment / no published APS floor (UNISA distance, some TVETs,
        # placeholder data). De-rate heavily so they don't dominate over real
        # programmes with honest cutoffs the student comfortably clears.
        aps_score = 10.0
    else:
        aps_score = min(max(aps_surplus + 20, 0), 40) * 1.5      # 0-60
    subject_penalty = (len(missing) * 15) + sum(g['gap'] * 5 for g in low)
    subject_score = max(40 - subject_penalty, 0)                  # 0-40
    base = int(aps_score + subject_score) + _level_priority(offering.course.level)
    bonus = _personalization_bonus(offering, preferred_field, career, subject_fields, career_subject_aligned)

    return {
        'category': category,
        'aps_surplus': aps_surplus,
        'missing_subjects': missing,
        'low_subjects': low,
        'maths_lit_blocked': maths_lit_blocked,
        'score': base + bonus,
        'tvet': False,
        'placeholder': False,
    }


# ── Public API ────────────────────────────────────────────────────────────────

CATEGORY_ORDER = {'eligible': 0, 'subject_gap': 1, 'aps_gap': 2, 'not_qualified': 3}

# Higher = preferred. Degrees outrank diplomas, both outrank certificates.
LEVEL_PRIORITY = {
    'phd':              18,
    'masters':          16,
    'honours':          14,
    'degree':           12,
    'advanced_diploma':  6,
    'diploma':           5,
    'nc_v':              3,
    'n1_n6':             3,
    'certificate':       2,
}


def _level_priority(level: str) -> int:
    return LEVEL_PRIORITY.get(level, 4)


def match_courses(
    user_aps: int,
    user_subjects: list[dict],
    province: str | None = None,
    field: str | None = None,
    institution_type: str | None = None,
    level: str | None = None,
    preferred_field: str | None = None,
    career: str | None = None,
    search: str | None = None,
    include_not_qualified: bool = False,
    include_placeholders: bool = False,
    limit: int = 200,
) -> list[dict]:
    """
    Match a student's profile against active CourseOfferings.

    `preferred_field` and `career` add a personalization bonus so that
    courses relevant to the student's interests rank higher.
    `include_placeholders=False` hides offerings that have no subject
    requirements AND min_aps=0 (likely incomplete scrape data) so they
    don't drown out real matches.
    """
    has_maths_lit = _has_maths_literacy(user_subjects)
    subject_fields = _top_subject_fields(user_subjects, n=4)
    career_field = _field_for_career(career)
    # If career is given but subjects don't support it, mark mis-aligned.
    # Empty subject_fields → no signal either way → assume aligned (cold start).
    career_subject_aligned = (
        not career or not career_field or not subject_fields or career_field in subject_fields
    )

    qs = (
        CourseOffering.objects
        .filter(is_active=True)
        .select_related('course', 'institution')
    )

    if province:
        qs = qs.filter(institution__province=province)
    if institution_type:
        qs = qs.filter(institution__institution_type=institution_type)
    if field:
        qs = qs.filter(course__field=field)
    if level:
        qs = qs.filter(course__level=level)
    if search:
        from django.db.models import Q
        qs = qs.filter(
            Q(course__name__icontains=search)
            | Q(course__description__icontains=search)
            | Q(course__career_opportunities__icontains=search)
            | Q(institution__name__icontains=search)
            | Q(institution__short_name__icontains=search)
        )

    results = []
    for offering in qs.iterator(chunk_size=500):
        match = _evaluate_offering(
            offering, user_aps, user_subjects, has_maths_lit,
            preferred_field, career,
            subject_fields=subject_fields,
            career_subject_aligned=career_subject_aligned,
        )

        if not include_not_qualified and match['category'] == 'not_qualified':
            continue
        if not include_placeholders and match.get('placeholder'):
            continue

        results.append({
            'offering_id':           offering.id,
            'course_id':             offering.course_id,
            'course_name':           offering.course.name,
            'course_field':          offering.course.field,
            'course_level':          offering.course.level,
            'course_duration_years': offering.course.duration_years,
            'course_description':    offering.course.description,
            'institution_id':        offering.institution_id,
            'institution_name':      offering.institution.name,
            'institution_short':     offering.institution.short_name,
            'institution_type':      offering.institution.institution_type,
            'institution_province':  offering.institution.province,
            'institution_city':      offering.institution.city,
            'institution_website':   offering.institution.website,
            'institution_logo_url':  offering.institution.logo_url,
            'institution_apply_url': offering.institution.application_url,
            'campus':                offering.campus,
            'min_aps':               offering.min_aps,
            'programme_code':        offering.programme_code,
            'subject_requirements':  offering.subject_requirements,
            'match':                 match,
        })

    results.sort(key=lambda r: (
        CATEGORY_ORDER.get(r['match']['category'], 9),
        -r['match']['score'],
    ))

    return results[:limit]


def match_summary(results: list[dict]) -> dict:
    counts = {'eligible': 0, 'subject_gap': 0, 'aps_gap': 0, 'not_qualified': 0}
    for r in results:
        counts[r['match']['category']] = counts.get(r['match']['category'], 0) + 1
    return counts
