from django.db.models import Case, IntegerField, Value, When, F
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Accommodation
from .serializers import AccommodationSerializer


class AccommodationListView(generics.ListAPIView):
    serializer_class = AccommodationSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ('province', 'city', 'room_type', 'nsfas_accredited', 'nearby_institution')
    search_fields = ('name', 'description', 'address', 'city')
    ordering_fields = ('price_per_month', 'distance_km', 'name')

    def get_queryset(self):
        qs = (
            Accommodation.objects.filter(is_active=True)
            .select_related('nearby_institution')
        )
        max_price = self.request.query_params.get('max_price')
        min_price = self.request.query_params.get('min_price')
        if max_price:
            qs = qs.filter(price_per_month__lte=max_price)
        if min_price:
            qs = qs.filter(price_per_month__gte=min_price)

        # Smart default ranking (when the client isn't asking for an explicit
        # ?ordering=): the places a student is most likely to want first —
        #   1. in their home / preferred-study province (close by)
        #   2. NSFAS-accredited (most students rely on it)
        #   3. closest to campus
        #   4. cheapest
        # An explicit ?ordering= still wins (applied by OrderingFilter after).
        provinces: set[str] = set()
        user = self.request.user
        if user.is_authenticated:
            if getattr(user, 'province', None):
                provinces.add(user.province)
            provinces.update(getattr(user, 'preferred_study_provinces', None) or [])

        if provinces:
            qs = qs.annotate(_near=Case(
                When(province__in=provinces, then=Value(0)),
                default=Value(1), output_field=IntegerField(),
            ))
        else:
            qs = qs.annotate(_near=Value(1, output_field=IntegerField()))

        qs = qs.annotate(_nsfas=Case(
            When(nsfas_accredited=True, then=Value(0)),
            default=Value(1), output_field=IntegerField(),
        ))

        return qs.order_by(
            '_near',
            '_nsfas',
            F('distance_km').asc(nulls_last=True),
            'price_per_month',
            'name',
        )


class AccommodationDetailView(generics.RetrieveAPIView):
    serializer_class = AccommodationSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Accommodation.objects.filter(is_active=True)
