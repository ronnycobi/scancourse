"""
Collaborative-filtering + content-based course recommender.

Strategy:
  1. Look at the user's signals (CourseInteraction rows + SavedItem rows).
     Compute a weight per course they've engaged with.
  2. Item-item CF: find other users who interacted with those same courses,
     then score every OTHER course those neighbours also interacted with.
     Higher overlap with current user → stronger recommendation.
  3. Filter the candidate set to courses the user can qualify for (uses
     the matcher), then blend the CF score with the matcher's
     personalization score so cold-start users still get good results.

Falls back gracefully:
  - New user with zero interactions → pure matcher personalization.
  - Course pool empty → returns [].
"""
from __future__ import annotations

from collections import defaultdict

from django.db.models import Count

from apps.ocr.models import APSResult
from apps.users.models import SavedItem

from .matcher import (
    match_courses,
    _top_subject_fields,
    _field_for_career,
)
from .models import Course, CourseInteraction


INTERACTION_WEIGHTS = {'view': 1.0, 'save': 3.0, 'apply': 5.0}

# Tier bonuses: how strongly to favour each level for a student whose APS
# qualifies them for a bachelor's. Degrees lead — diplomas/certs are
# alternatives, not the main recommendation.
LEVEL_BONUS_BACHELOR_TIER = {
    'degree':            45,
    'advanced_diploma':  10,
    'diploma':            8,
    'nc_v':               0,
    'n1_n6':              0,
    'certificate':        0,
}

# For students whose APS falls in the diploma range — bias the other way.
LEVEL_BONUS_DIPLOMA_TIER = {
    'diploma':           30,
    'advanced_diploma':  25,
    'nc_v':              15,
    'n1_n6':             15,
    'certificate':       10,
    'degree':             5,  # still show 1-2 degrees they could stretch for
}


def _course_has_content(offering: dict) -> bool:
    """Skip offerings with empty/garbage course data."""
    name = (offering.get('course_name') or '').strip()
    if len(name) < 4:
        return False
    # Names that start with a preposition / fragment from bad scrapes.
    lower = name.lower()
    if lower.startswith(('in ', 'a ', 'the ', '- ', ': ')):
        return False
    return True


def _user_course_weights(user) -> dict[int, float]:
    """Aggregate the current user's signals into course_id → weight."""
    weights: dict[int, float] = defaultdict(float)

    for inter in CourseInteraction.objects.filter(user=user).values('course_id', 'kind'):
        weights[inter['course_id']] += INTERACTION_WEIGHTS.get(inter['kind'], 1.0)

    for s in SavedItem.objects.filter(user=user, item_type='course').values_list('item_id', flat=True):
        weights[s] += INTERACTION_WEIGHTS['save']

    return dict(weights)


def _collaborative_scores(user, seed_course_ids: set[int]) -> dict[int, float]:
    """
    Item-item CF score for every candidate course.

    For each seed (current user's course), find users who also interacted with it;
    every OTHER course those users touched gets +1 weighted by interaction kind.
    """
    if not seed_course_ids:
        return {}

    # Neighbours: users who interacted with at least one seed course.
    neighbour_ids = (
        CourseInteraction.objects
        .filter(course_id__in=seed_course_ids)
        .exclude(user=user)
        .values_list('user_id', flat=True)
        .distinct()
    )

    saved_neighbours = (
        SavedItem.objects
        .filter(item_type='course', item_id__in=seed_course_ids)
        .exclude(user=user)
        .values_list('user_id', flat=True)
        .distinct()
    )
    neighbours = set(neighbour_ids) | set(saved_neighbours)
    if not neighbours:
        return {}

    scores: dict[int, float] = defaultdict(float)

    for row in (
        CourseInteraction.objects
        .filter(user_id__in=neighbours)
        .exclude(course_id__in=seed_course_ids)
        .values('course_id', 'kind')
    ):
        scores[row['course_id']] += INTERACTION_WEIGHTS.get(row['kind'], 1.0)

    for s in (
        SavedItem.objects
        .filter(user_id__in=neighbours, item_type='course')
        .exclude(item_id__in=seed_course_ids)
        .values_list('item_id', flat=True)
    ):
        scores[s] += INTERACTION_WEIGHTS['save']

    return dict(scores)


def recommend_courses(user, limit: int = 20) -> list[dict]:
    """
    Return up to `limit` recommended offerings for the user.

    Output: same shape as matcher.match_courses results, with an extra
    `recommendation` field: {'cf_score': float, 'reason': str}.
    """
    # Use the BEST mark per subject across ALL the student's reports —
    # mirrors how SA universities compute APS from multiple sittings
    # (NSC + supplementary + subject upgrades).
    from apps.ocr.aggregator import best_aps_for_user
    merged = best_aps_for_user(user)
    user_aps = merged['total_aps']
    user_subjects = merged['subjects']

    # APS ≥ 26 is comfortably bachelor-degree territory at most SA universities.
    # Below that, diplomas are the realistic target.
    bachelor_tier = user_aps >= 26
    level_bonus_map = LEVEL_BONUS_BACHELOR_TIER if bachelor_tier else LEVEL_BONUS_DIPLOMA_TIER

    career = getattr(user, 'dream_career', None) or None
    matched = match_courses(
        user_aps=user_aps,
        user_subjects=user_subjects,
        preferred_field=getattr(user, 'preferred_field', None) or None,
        career=career,
        include_not_qualified=False,
        include_placeholders=False,
        limit=500,
    )
    if not matched:
        return []

    subject_fields = _top_subject_fields(user_subjects, n=4)
    career_field = _field_for_career(career)
    career_aligned = (
        not career or not career_field or not subject_fields or career_field in subject_fields
    )

    # Build a course_id → best (highest-scoring) offering map.
    # Skip thin/garbage course data.
    best_for_course: dict[int, dict] = {}
    for r in matched:
        if not _course_has_content(r):
            continue
        cid = r['course_id']
        if cid not in best_for_course or r['match']['score'] > best_for_course[cid]['match']['score']:
            best_for_course[cid] = r

    seed_weights = _user_course_weights(user)
    cf_scores = _collaborative_scores(user, set(seed_weights.keys()))

    # Popularity fallback (for brand-new platforms): most-saved/most-viewed.
    if not cf_scores:
        popular = (
            CourseInteraction.objects
            .values('course_id')
            .annotate(n=Count('id'))
            .order_by('-n')[:50]
        )
        for row in popular:
            cf_scores[row['course_id']] = float(row['n'])
        # Add saves
        for s in (
            SavedItem.objects.filter(item_type='course')
            .values('item_id').annotate(n=Count('id'))
        ):
            cf_scores[s['item_id']] = cf_scores.get(s['item_id'], 0) + s['n'] * 3.0

    # Don't recommend things the user has already engaged with.
    seen = set(seed_weights.keys())

    recs: list[dict] = []
    for course_id, offering_data in best_for_course.items():
        if course_id in seen:
            continue
        cf = cf_scores.get(course_id, 0.0)
        level = offering_data.get('course_level', '')
        course_field = offering_data['course_field']

        # Tier bonus: bachelor tier → degrees lead; diploma tier → diplomas lead.
        tier_bonus = level_bonus_map.get(level, 0)

        # Field-fit bonus: strong subject alignment AND career alignment → boost.
        field_fit_bonus = 0
        if course_field in subject_fields:
            field_fit_bonus += 15
        if career_field and course_field == career_field and career_aligned:
            field_fit_bonus += 15

        # Real-uni bonus: prefer institutions with honest APS cutoffs over
        # open-enrolment ones (UNISA, placeholder data) so the latter don't
        # dominate purely by having 144+ courses across every field.
        real_uni_bonus = 30 if (offering_data.get('min_aps') or 0) > 0 else 0

        # Final: matcher score + level tier + field fit + real-uni + CF
        final = (
            offering_data['match']['score']
            + tier_bonus
            + field_fit_bonus
            + real_uni_bonus
            + cf * 10.0
        )

        if cf > 0:
            reason = 'similar_students'
        elif course_field in subject_fields and career_field == course_field and career_aligned:
            reason = 'matches_your_subjects_and_career'
        elif course_field in subject_fields:
            reason = 'matches_your_subjects'
        elif career_field and course_field == career_field and career_aligned:
            reason = 'matches_your_career'
        elif offering_data['match']['score'] >= 100:
            reason = 'matches_your_profile'
        else:
            reason = 'matches_your_interests'

        item = dict(offering_data)
        item['recommendation'] = {
            'final_score': round(final, 1),
            'cf_score': round(cf, 2),
            'reason': reason,
        }
        recs.append(item)

    recs.sort(key=lambda r: -r['recommendation']['final_score'])

    # Diversity cap: avoid letting one open-enrolment institution (UNISA)
    # or any single institution flood the recommendations. Take at most
    # `per_institution_cap` offerings per institution while preserving order.
    per_institution_cap = 1
    diversified: list[dict] = []
    seen_counts: dict[int, int] = {}
    for r in recs:
        inst_id = r.get('institution_id')
        used = seen_counts.get(inst_id, 0)
        if used >= per_institution_cap:
            continue
        diversified.append(r)
        seen_counts[inst_id] = used + 1
        if len(diversified) >= limit:
            break

    # No backfill — better to return fewer items than to flood with one
    # institution's catalogue. If we couldn't find enough variety, that's
    # the honest answer.
    return diversified[:limit]
