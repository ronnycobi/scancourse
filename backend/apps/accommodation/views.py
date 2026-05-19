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
        qs = Accommodation.objects.filter(is_active=True)
        max_price = self.request.query_params.get('max_price')
        min_price = self.request.query_params.get('min_price')
        if max_price:
            qs = qs.filter(price_per_month__lte=max_price)
        if min_price:
            qs = qs.filter(price_per_month__gte=min_price)
        return qs


class AccommodationDetailView(generics.RetrieveAPIView):
    serializer_class = AccommodationSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Accommodation.objects.filter(is_active=True)
