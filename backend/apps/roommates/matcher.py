"""
Compatibility scoring algorithm for roommate matching.
Returns a score 0.0–1.0 based on weighted attribute matches.
"""
from .models import RoommateProfile

# Weights for each compatibility dimension (must sum to 1.0)
WEIGHTS = {
    'institution': 0.20,
    'budget': 0.18,
    'lifestyle': 0.25,    # combined sleep, clean, social, study
    'hard_filters': 0.15,  # smoking, pets, age, gender
    'languages': 0.10,
    'move_in': 0.07,
    'city': 0.05,
}


def _score_institution(a: RoommateProfile, b: RoommateProfile) -> float:
    if a.institution_id and a.institution_id == b.institution_id:
        return 1.0
    return 0.2  # different institutions still possible


def _score_budget(a: RoommateProfile, b: RoommateProfile) -> float:
    if not (a.budget_max and b.budget_max):
        return 0.5
    a_min, a_max = a.budget_min or 0, a.budget_max
    b_min, b_max = b.budget_min or 0, b.budget_max
    overlap_lo = max(a_min, b_min)
    overlap_hi = min(a_max, b_max)
    if overlap_hi < overlap_lo:
        return 0.0
    overlap = overlap_hi - overlap_lo
    range_size = max(a_max - a_min, b_max - b_min, 1)
    return min(1.0, overlap / range_size)


def _score_lifestyle(a: RoommateProfile, b: RoommateProfile) -> float:
    matches = 0
    total = 0
    for field in ['sleep_schedule', 'cleanliness', 'social_level', 'study_habits']:
        a_val, b_val = getattr(a, field), getattr(b, field)
        if a_val and b_val:
            total += 1
            if a_val == b_val:
                matches += 1
    return matches / total if total > 0 else 0.5


def _score_hard_filters(a: RoommateProfile, b: RoommateProfile) -> float:
    """Returns 0 if any hard filter is violated, else 1."""
    if a.prefers_non_smoker and b.smokes:
        return 0.0
    if b.prefers_non_smoker and a.smokes:
        return 0.0
    if a.prefers_no_pets and b.has_pets:
        return 0.0
    if b.prefers_no_pets and a.has_pets:
        return 0.0
    if a.prefers_same_gender and a.gender and b.gender and a.gender != b.gender:
        return 0.0
    if b.prefers_same_gender and a.gender and b.gender and a.gender != b.gender:
        return 0.0
    if b.age and not (a.age_range_min <= b.age <= a.age_range_max):
        return 0.0
    if a.age and not (b.age_range_min <= a.age <= b.age_range_max):
        return 0.0
    return 1.0


def _score_languages(a: RoommateProfile, b: RoommateProfile) -> float:
    if not (a.languages and b.languages):
        return 0.5
    set_a, set_b = set(a.languages), set(b.languages)
    common = len(set_a & set_b)
    total = len(set_a | set_b)
    return common / total if total else 0.5


def _score_move_in(a: RoommateProfile, b: RoommateProfile) -> float:
    if not (a.move_in_month and b.move_in_month):
        return 0.5
    delta_days = abs((a.move_in_month - b.move_in_month).days)
    if delta_days <= 30:
        return 1.0
    if delta_days <= 90:
        return 0.6
    return 0.2


def _score_city(a: RoommateProfile, b: RoommateProfile) -> float:
    if a.target_city and b.target_city and a.target_city.lower() == b.target_city.lower():
        return 1.0
    return 0.3


def compatibility_score(a: RoommateProfile, b: RoommateProfile) -> float:
    """Returns a single 0.0–1.0 score for two profiles."""
    if a.user_id == b.user_id:
        return 0.0

    hard_score = _score_hard_filters(a, b)
    if hard_score == 0.0:
        return 0.0  # short-circuit on hard filter violation

    score = 0.0
    score += WEIGHTS['institution'] * _score_institution(a, b)
    score += WEIGHTS['budget'] * _score_budget(a, b)
    score += WEIGHTS['lifestyle'] * _score_lifestyle(a, b)
    score += WEIGHTS['hard_filters'] * hard_score
    score += WEIGHTS['languages'] * _score_languages(a, b)
    score += WEIGHTS['move_in'] * _score_move_in(a, b)
    score += WEIGHTS['city'] * _score_city(a, b)
    return round(score, 3)


def find_matches(profile: RoommateProfile, limit: int = 20) -> list[tuple[RoommateProfile, float]]:
    """Find the top-N roommate candidates for the given profile."""
    candidates = RoommateProfile.objects.filter(is_active=True).exclude(user_id=profile.user_id)
    if profile.target_city:
        candidates = candidates.filter(target_city__iexact=profile.target_city) | candidates.filter(institution=profile.institution)
    candidates = candidates.distinct().select_related('user', 'institution')[:200]

    scored = [(c, compatibility_score(profile, c)) for c in candidates]
    scored = [(c, s) for c, s in scored if s > 0.3]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]
