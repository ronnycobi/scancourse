from collections import defaultdict
from datetime import date

from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ocr.models import APSResult
from apps.users.models import SavedItem

from scancourse.pagination import LargeResultsSetPagination
from .models import Bursary
from .matcher import evaluate_bursary, match_bursaries, summary, STATUS_ORDER
from .serializers import BursarySerializer


def _user_fields(user) -> list[str]:
    """All of the user's preferred fields (multi-select), with the legacy
    singular field merged in for backward compatibility."""
    fields = list(getattr(user, 'preferred_fields', None) or [])
    single = getattr(user, 'preferred_field', None)
    if single and single not in fields:
        fields.append(single)
    return fields


class BursaryListView(generics.ListAPIView):
    """
    GET /api/v1/bursaries/
        Public. Supports ?search=, ?field=, ?province=, ?funding_type=,
        ?status=open|closing_soon|closed, ?ordering=application_deadline.

    Returns the list paginated. When authenticated, each bursary also
    carries a `match` block with the user's qualify status.
    """
    serializer_class = BursarySerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = LargeResultsSetPagination
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ('field', 'province', 'funding_type')
    search_fields = ('name', 'provider', 'description', 'eligibility')
    ordering_fields = ('application_deadline', 'name', 'amount')

    def get_queryset(self):
        qs = Bursary.objects.filter(is_active=True)
        status = (self.request.query_params.get('status') or '').lower()
        search = (self.request.query_params.get('search') or '').strip()
        today = date.today()

        # When the user is searching, ignore the status filter — they want
        # to find anything that matches regardless of open/closed.
        if not search:
            if status == 'open':
                qs = qs.filter(Q(application_deadline__gte=today) | Q(application_deadline__isnull=True))
            elif status == 'closing_soon':
                qs = qs.filter(
                    application_deadline__gte=today,
                    application_deadline__lte=today.fromordinal(today.toordinal() + 30),
                )
            elif status == 'closed':
                qs = qs.filter(application_deadline__lt=today)
        return qs.order_by(
            '-is_sponsored', '-sponsor_priority',
            'application_deadline', 'name',
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Attach match info per item if user is authenticated and has APS.
        if not request.user.is_authenticated:
            return response

        from apps.ocr.aggregator import best_aps_for_user
        from .matcher import _avg_from_aps_subjects
        merged = best_aps_for_user(request.user)
        if merged['report_count'] == 0:
            return response

        user_aps = merged['total_aps']
        user_subjects = merged['subjects']
        user_avg = _avg_from_aps_subjects(user_subjects)
        user_fields = _user_fields(request.user)
        user_province = getattr(request.user, 'province', None) or None

        results = response.data.get('results') or response.data
        if isinstance(results, list):
            # One query for all bursaries on this page (avoid N+1).
            ids = [item['id'] for item in results if 'id' in item]
            by_id = {b.id: b for b in Bursary.objects.filter(pk__in=ids)}
            for item in results:
                bursary = by_id.get(item.get('id'))
                if not bursary:
                    continue
                item['match'] = evaluate_bursary(
                    bursary,
                    user_aps=user_aps,
                    user_avg=user_avg,
                    user_fields=user_fields,
                    user_province=user_province,
                )
            # Sort qualified-first within the current page, preserving
            # deadline order within each status bucket.
            results.sort(key=lambda x: (
                STATUS_ORDER.get((x.get('match') or {}).get('status'), 9),
                x.get('application_deadline') or '9999-12-31',
            ))
        return response


class BursaryDetailView(generics.RetrieveAPIView):
    serializer_class = BursarySerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Bursary.objects.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        if request.user.is_authenticated:
            from apps.ocr.aggregator import best_aps_for_user
            from .matcher import _avg_from_aps_subjects
            merged = best_aps_for_user(request.user)
            if merged['report_count'] > 0:
                bursary = self.get_object()
                response.data['match'] = evaluate_bursary(
                    bursary,
                    user_aps=merged['total_aps'],
                    user_avg=_avg_from_aps_subjects(merged['subjects']),
                    user_fields=_user_fields(request.user),
                    user_province=getattr(request.user, 'province', None) or None,
                )
        return response


class BursaryStatsView(APIView):
    """GET /api/v1/bursaries/stats/  — total + per-status counts for the current user."""
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        today = date.today()
        total = Bursary.objects.filter(is_active=True).count()
        open_count = Bursary.objects.filter(
            is_active=True,
        ).filter(Q(application_deadline__gte=today) | Q(application_deadline__isnull=True)).count()
        closed_count = Bursary.objects.filter(
            is_active=True, application_deadline__lt=today,
        ).count()
        closing_soon = Bursary.objects.filter(
            is_active=True,
            application_deadline__gte=today,
            application_deadline__lte=today.fromordinal(today.toordinal() + 30),
        ).count()

        out = {
            'total': total,
            'open': open_count,
            'closed': closed_count,
            'closing_soon': closing_soon,
        }

        if request.user.is_authenticated:
            from apps.ocr.aggregator import best_aps_for_user
            from .matcher import _avg_from_aps_subjects
            merged = best_aps_for_user(request.user)
            if merged['report_count'] > 0:
                matched = match_bursaries(
                    Bursary.objects.filter(is_active=True).filter(
                        Q(application_deadline__gte=today) | Q(application_deadline__isnull=True),
                    ),
                    user_aps=merged['total_aps'],
                    user_avg=_avg_from_aps_subjects(merged['subjects']),
                    user_fields=_user_fields(request.user),
                    user_province=getattr(request.user, 'province', None) or None,
                )
                out['match_summary'] = summary(matched)

        return Response(out)


class BursaryRecommendView(APIView):
    """
    GET /api/v1/bursaries/recommend/?limit=10
        Authenticated. Combines content-based matching (qualify status +
        field fit + provider relevance) with item-item collaborative
        filtering via the existing SavedItem signal.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            limit = min(int(request.query_params.get('limit', 10)), 50)
        except (TypeError, ValueError):
            limit = 10

        today = date.today()
        user = request.user

        from apps.ocr.aggregator import best_aps_for_user
        from .matcher import _avg_from_aps_subjects
        merged = best_aps_for_user(user)
        user_avg = _avg_from_aps_subjects(merged['subjects']) if merged['report_count'] else None
        user_aps = merged['total_aps'] if merged['report_count'] else None
        user_fields = _user_fields(user)
        user_province = getattr(user, 'province', None) or None

        bursaries = list(
            Bursary.objects.filter(is_active=True)
            .filter(Q(application_deadline__gte=today) | Q(application_deadline__isnull=True))
        )
        matched = match_bursaries(
            bursaries, user_aps=user_aps, user_avg=user_avg,
            user_fields=user_fields, user_province=user_province,
        )

        # Content score: qualified > check_details > grade_gap > field_mismatch
        content_weight = {
            'qualified': 100,
            'check_details': 70,
            'grade_gap': 40,
            'field_mismatch': 20,
            'closed': 0,
        }
        # CF: bursaries saved by users who also saved one of THIS user's saved bursaries.
        own_saved = set(
            SavedItem.objects.filter(user=user, item_type='bursary')
            .values_list('item_id', flat=True)
        )
        neighbours = (
            SavedItem.objects.filter(item_type='bursary', item_id__in=own_saved)
            .exclude(user=user)
            .values_list('user_id', flat=True)
            .distinct()
        )
        cf_scores: dict[int, float] = defaultdict(float)
        if neighbours:
            for row in SavedItem.objects.filter(
                user_id__in=neighbours, item_type='bursary',
            ).exclude(item_id__in=own_saved).values('item_id').annotate(n=Count('id')):
                cf_scores[row['item_id']] = row['n'] * 3.0
        else:
            # Cold-start: most-saved bursaries across the platform.
            for row in SavedItem.objects.filter(item_type='bursary').values('item_id').annotate(n=Count('id'))[:50]:
                cf_scores[row['item_id']] = row['n'] * 1.0

        ranked = []
        for r in matched:
            b = r['bursary']
            if b.id in own_saved:
                continue
            base = content_weight.get(r['match']['status'], 0)
            cf = cf_scores.get(b.id, 0.0)
            field_bonus = 15 if (user_fields and b.field in user_fields) else 0
            province_bonus = 10 if (user_province and b.province == user_province) else 0
            # Penalise distant deadlines slightly so soon-closing ones surface.
            days = r['match'].get('days_until_deadline') or 365
            urgency_bonus = max(0, 20 - days // 14)
            final = base + field_bonus + province_bonus + urgency_bonus + cf * 10.0
            ranked.append({
                'bursary': BursarySerializer(b).data,
                'match': r['match'],
                'final_score': round(final, 1),
            })

        ranked.sort(key=lambda x: -x['final_score'])
        return Response({'count': len(ranked), 'results': ranked[:limit]})
