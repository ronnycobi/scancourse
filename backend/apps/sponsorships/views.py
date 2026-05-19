from datetime import timedelta
from django.db.models import Count
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Sponsor, SponsorshipPlan, Sponsorship, SponsorshipImpression, SponsorshipClick
from .serializers import (
    SponsorSerializer, SponsorshipPlanSerializer, SponsorshipSerializer,
    TrackEventSerializer, TrackClickSerializer,
)


# ════════════════════════════════════════════════════════════════
# Public — pricing tiers shown on the partner landing page
# ════════════════════════════════════════════════════════════════

class PlanListView(generics.ListAPIView):
    queryset = SponsorshipPlan.objects.all()
    serializer_class = SponsorshipPlanSerializer
    permission_classes = (permissions.AllowAny,)


# ════════════════════════════════════════════════════════════════
# Tracking — called from the app whenever a sponsored item is shown / clicked
# ════════════════════════════════════════════════════════════════

class TrackImpressionView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TrackEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sponsorship = Sponsorship.objects.get(id=serializer.validated_data['sponsorship_id'])
        except Sponsorship.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        SponsorshipImpression.objects.create(
            sponsorship=sponsorship,
            user=request.user if request.user.is_authenticated else None,
            placement=serializer.validated_data.get('placement', 'unknown'),
        )
        return Response({'detail': 'tracked'}, status=status.HTTP_201_CREATED)


class TrackClickView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TrackClickSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sponsorship = Sponsorship.objects.get(id=serializer.validated_data['sponsorship_id'])
        except Sponsorship.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        SponsorshipClick.objects.create(
            sponsorship=sponsorship,
            user=request.user if request.user.is_authenticated else None,
            action=serializer.validated_data.get('action', 'view'),
            referrer=serializer.validated_data.get('referrer', ''),
        )
        return Response({'detail': 'tracked'}, status=status.HTTP_201_CREATED)


# ════════════════════════════════════════════════════════════════
# Sponsor portal — analytics for paying partners
# ════════════════════════════════════════════════════════════════

class SponsorAnalyticsView(APIView):
    """
    Sponsors get a dashboard of impressions, clicks, and CTR for their sponsorships.
    Auth: sponsor must own this sponsorship (in production, link Sponsor to a User).
    """

    def get(self, request, sponsorship_id):
        try:
            sponsorship = Sponsorship.objects.get(id=sponsorship_id)
        except Sponsorship.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Restrict to staff for now — production: sponsor user roles
        if not request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        days = int(request.query_params.get('days', 30))
        since = timezone.now() - timedelta(days=days)

        impressions = SponsorshipImpression.objects.filter(sponsorship=sponsorship, timestamp__gte=since)
        clicks = SponsorshipClick.objects.filter(sponsorship=sponsorship, timestamp__gte=since)

        impression_count = impressions.count()
        click_count = clicks.count()
        apply_count = clicks.filter(action='apply').count()
        save_count = clicks.filter(action='save').count()

        ctr = (click_count / impression_count * 100) if impression_count else 0
        apply_rate = (apply_count / impression_count * 100) if impression_count else 0

        # Daily breakdown
        from django.db.models.functions import TruncDate
        daily_impressions = list(
            impressions.annotate(day=TruncDate('timestamp'))
            .values('day').annotate(count=Count('id')).order_by('day')
        )
        daily_clicks = list(
            clicks.annotate(day=TruncDate('timestamp'))
            .values('day').annotate(count=Count('id')).order_by('day')
        )

        return Response({
            'sponsorship': SponsorshipSerializer(sponsorship).data,
            'period_days': days,
            'totals': {
                'impressions': impression_count,
                'clicks': click_count,
                'applies': apply_count,
                'saves': save_count,
                'ctr_percent': round(ctr, 2),
                'apply_rate_percent': round(apply_rate, 2),
            },
            'daily': {
                'impressions': [{'day': str(d['day']), 'count': d['count']} for d in daily_impressions],
                'clicks': [{'day': str(d['day']), 'count': d['count']} for d in daily_clicks],
            },
        })
