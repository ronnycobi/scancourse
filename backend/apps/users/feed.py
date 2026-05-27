"""
Home feed builder.

Pulls signals from across the codebase (saved items, deadlines, APS
status, profile completeness, etc.) and turns them into a ranked list
of cards for the mobile app's home screen.

Each card has a fixed shape:
    {
      "id": "stable id so the client can de-dupe / dismiss",
      "type": "deadline | match | improvement | tip | onboarding | celebration",
      "priority": 0-100,  # higher = closer to the top
      "icon": "deadline | bursary | course | trending_up | ...",  # client maps to Material icon
      "accent": "primary | accent | error | success | secondary",
      "title": "short bold",
      "body":  "one or two sentences",
      "cta":   "Apply now",  # optional button label
      "deep_link": "/bursaries/12",
      "expires_at": "2026-06-15T...",  # optional ISO
    }

The order is computed here, on the server, so the client just maps it
to widgets. Easy to A/B test the ranking later.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Iterable
from django.utils import timezone
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView


class HomeFeedView(APIView):
    """GET /api/v1/auth/feed/ — personalised feed cards."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        u = request.user
        today = timezone.now().date()
        items: list[dict] = []

        # ── 1. URGENT: saved bursaries closing in ≤ 14 days ─────────
        items.extend(self._bursary_deadlines(u, today))

        # ── 2. URGENT: saved course offerings closing in ≤ 14 days ──
        items.extend(self._course_deadlines(u, today))

        # NOTE: '_new_matches' generator removed — the count was
        # confusing ('1300 new courses match your APS' isn't actionable
        # and felt spammy). Recommended-for-You carousel on the home
        # screen does this job better with real course previews.

        # ── 4. Latest improvement plan summary ──────────────────────
        items.extend(self._improvement_nudge(u))

        # ── 5. Profile completeness ─────────────────────────────────
        items.extend(self._profile_nudge(u))

        # NOTE: _bursary_recommendation removed from the home feed.
        # 'Recommended Bursaries' carousel + 'Bursaries Closing Soon'
        # cover the same job with better visuals on the home screen,
        # so the For You card felt redundant.

        # ── 7. APS celebration ──────────────────────────────────────
        items.extend(self._aps_celebration(u))

        # ── 8. Tip card (always last, lowest priority) ──────────────
        items.append(self._daily_tip(u))

        # Sort by priority desc, cap to 12
        items.sort(key=lambda c: c.get('priority', 0), reverse=True)
        return Response({'items': items[:12]})

    # ── Generators ──────────────────────────────────────────────────

    def _bursary_deadlines(self, user, today):
        from apps.users.models import SavedItem
        from apps.bursaries.models import Bursary
        saved_ids = list(SavedItem.objects.filter(
            user=user, item_type='bursary'
        ).values_list('item_id', flat=True)[:50])
        if not saved_ids:
            return []
        closing = Bursary.objects.filter(
            id__in=saved_ids,
            application_deadline__gte=today,
            application_deadline__lte=today + timedelta(days=14),
        ).order_by('application_deadline')[:3]
        out = []
        for b in closing:
            days = (b.application_deadline - today).days
            urgent = days <= 3
            out.append({
                'id': f'bursary-deadline-{b.id}',
                'type': 'deadline',
                'priority': 100 - days,  # closest = highest
                'icon': 'bursary',
                'accent': 'error' if urgent else 'accent',
                'title': '{} closes in {} day{}'.format(
                    b.name[:60], days, '' if days == 1 else 's'),
                'body': 'Tap to view eligibility and apply now.',
                'cta': 'Apply',
                'deep_link': f'/bursaries/{b.id}',
                'expires_at': b.application_deadline.isoformat(),
            })
        return out

    def _course_deadlines(self, user, today):
        from apps.users.models import SavedItem
        from apps.courses.models import CourseOffering
        saved_ids = list(SavedItem.objects.filter(
            user=user, item_type='course'
        ).values_list('item_id', flat=True)[:50])
        if not saved_ids:
            return []
        closing = CourseOffering.objects.filter(
            course_id__in=saved_ids,
            application_deadline__gte=today,
            application_deadline__lte=today + timedelta(days=14),
        ).select_related('course', 'institution')[:3]
        out = []
        for o in closing:
            days = (o.application_deadline - today).days
            urgent = days <= 7
            inst = ''
            if o.institution_id:
                inst = o.institution.short_name or o.institution.name
            out.append({
                'id': f'course-deadline-{o.id}',
                'type': 'deadline',
                'priority': 90 - days,
                'icon': 'course',
                'accent': 'error' if urgent else 'accent',
                'title': f'{o.course.name[:60]} closes in {days}d',
                'body': inst,
                'cta': 'View course',
                'deep_link': f'/courses/{o.course_id}',
                'expires_at': o.application_deadline.isoformat(),
            })
        return out

    def _new_matches(self, user):
        from apps.ocr.models import APSResult
        from apps.courses.models import CourseOffering
        latest = APSResult.objects.filter(user=user).order_by('-created_at').first()
        if not latest:
            return []
        # New = added in the last 14 days the user qualifies for
        cutoff = timezone.now() - timedelta(days=14)
        try:
            count = CourseOffering.objects.filter(
                min_aps__lte=latest.total_aps,
                created_at__gte=cutoff,
            ).count() if hasattr(CourseOffering, 'created_at') else 0
        except Exception:
            count = 0
        if count < 1:
            return []
        return [{
            'id': 'new-matches',
            'type': 'match',
            'priority': 70,
            'icon': 'school',
            'accent': 'primary',
            'title': '{} new courses match your APS'.format(count),
            'body': 'Tap to see programmes you now qualify for.',
            'cta': 'See courses',
            'deep_link': '/courses',
        }]

    def _improvement_nudge(self, user):
        """
        Grade-aware "what to do with your APS" card.

        - Grade 10 / 11: mid-school, marks can still move. Push the
          improvement plan ("see how to lift your APS").
        - Grade 12 / gap year / other: NSC marks are already on file.
          No point telling them to study harder. Push *application*
          + course-discovery instead — that's what's next.
        - Grade not set: neutral wording so we don't insult anyone.
        """
        from apps.ocr.models import APSResult
        latest = APSResult.objects.filter(user=user).order_by(
            '-created_at').first()
        if not latest:
            return []

        grade = (user.grade or '').strip()
        can_still_improve = grade in ('grade_10', 'grade_11')
        marks_locked = grade in ('grade_12', 'gap_year', 'other')

        if can_still_improve:
            urgent = latest.total_aps < 30
            return [{
                'id': 'improvement-nudge',
                'type': 'improvement',
                'priority': 60 if not urgent else 80,
                'icon': 'trending_up',
                'accent': 'accent',
                'title': f'Your APS is {latest.total_aps}. Push it higher?',
                'body': 'Tap for 3 specific things you can do this term to lift your marks before finals.',
                'cta': 'See plan',
                'deep_link': '/improvement-plan',
            }]

        if marks_locked:
            # Different message — focus on apply NOW.
            return [{
                'id': 'apply-nudge',
                'type': 'match',
                'priority': 75,
                'icon': 'school',
                'accent': 'primary',
                'title': f'Your APS is {latest.total_aps}. Time to apply.',
                'body': 'See every course and bursary you qualify for, and start tracking your applications.',
                'cta': 'See matches',
                'deep_link': '/courses',
            }]

        # Grade unset — neutral wording, doesn't presume the user is
        # still studying or done.
        return [{
            'id': 'aps-info',
            'type': 'match',
            'priority': 55,
            'icon': 'school',
            'accent': 'primary',
            'title': f'Your APS is {latest.total_aps}',
            'body': 'See the courses and bursaries you qualify for.',
            'cta': 'Browse',
            'deep_link': '/courses',
        }]

    def _profile_nudge(self, user):
        """Nudge to fill in missing profile bits — improves matching."""
        gaps = []
        if not user.grade:
            gaps.append('grade')
        if not getattr(user, 'preferred_fields', None):
            gaps.append('interested fields')
        if not getattr(user, 'dream_careers', None):
            gaps.append('dream career')
        if not gaps:
            return []
        if len(gaps) == 1:
            body = f'Add your {gaps[0]} — takes 10 seconds and unlocks better matches.'
        else:
            body = 'Add your {} for better course matches.'.format(
                ', '.join(gaps))
        return [{
            'id': 'profile-nudge',
            'type': 'onboarding',
            'priority': 55,
            'icon': 'person',
            'accent': 'primary',
            'title': 'Make your profile work harder',
            'body': body,
            'cta': 'Update profile',
            'deep_link': '/edit-profile',
        }]

    def _bursary_recommendation(self, user):
        """One bursary the user hasn't saved yet that matches their field."""
        from apps.users.models import SavedItem
        from apps.bursaries.models import Bursary
        saved = set(SavedItem.objects.filter(
            user=user, item_type='bursary'
        ).values_list('item_id', flat=True))
        # Pick a recent bursary in the user's preferred field that they
        # haven't saved.
        fields = list(getattr(user, 'preferred_fields', None) or [])
        if user.preferred_field and not fields:
            fields = [user.preferred_field]
        qs = Bursary.objects.exclude(id__in=saved)
        if fields:
            qs = qs.filter(field__in=fields)
        cand = qs.order_by('-id').first()
        if not cand:
            return []
        return [{
            'id': f'bursary-rec-{cand.id}',
            'type': 'match',
            'priority': 50,
            'icon': 'bursary',
            'accent': 'secondary',
            'title': cand.name[:60],
            'body': 'Worth a look — fits your interests.',
            'cta': 'View bursary',
            'deep_link': f'/bursaries/{cand.id}',
        }]

    def _aps_celebration(self, user):
        """If their latest APS is higher than the one before, celebrate."""
        from apps.ocr.models import APSResult
        results = list(
            APSResult.objects.filter(user=user)
            .order_by('-created_at')[:2]
        )
        if len(results) < 2:
            return []
        latest, prev = results[0], results[1]
        delta = latest.total_aps - prev.total_aps
        if delta <= 0:
            return []
        return [{
            'id': f'aps-celebration-{latest.id}',
            'type': 'celebration',
            'priority': 65,
            'icon': 'celebration',
            'accent': 'success',
            'title': 'Your APS jumped +{} 🎉'.format(delta),
            'body': f'You\'re now at {latest.total_aps} — see your journey.',
            'cta': 'View journey',
            'deep_link': '/aps-journey',
        }]

    def _daily_tip(self, user):
        """Cycle through a small set of evergreen tips so the feed
        always has at least one card. Index changes daily by user."""
        tips = [
            {
                'title': 'Tip: scan a fresh report each term',
                'body': 'Your APS updates the moment we read new marks. '
                        'Stay on top of your improvement.',
                'cta': 'Scan now',
                'deep_link': '/scanner',
            },
            {
                'title': 'Need help with a motivation letter?',
                'body': 'Our AI helper writes a first draft you can edit.',
                'cta': 'Try it',
                'deep_link': '/motivation-letter',
            },
            {
                'title': 'Track every application',
                'body': 'Mark courses + bursaries you\'re applying to so deadlines never slip.',
                'cta': 'Open tracker',
                'deep_link': '/applications',
            },
            {
                'title': 'See your APS journey',
                'body': 'Track how your APS has improved over time and what it unlocks.',
                'cta': 'View journey',
                'deep_link': '/aps-journey',
            },
        ]
        today_index = timezone.now().toordinal() + (user.id or 0)
        tip = tips[today_index % len(tips)]
        return {
            'id': f'tip-{today_index}',
            'type': 'tip',
            'priority': 10,
            'icon': 'tip',
            'accent': 'primary',
            'title': tip['title'],
            'body': tip['body'],
            'cta': tip['cta'],
            'deep_link': tip['deep_link'],
        }
