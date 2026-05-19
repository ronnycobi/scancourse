from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Institution
from .serializers import InstitutionListSerializer, InstitutionDetailSerializer


class InstitutionListView(generics.ListAPIView):
    serializer_class = InstitutionListSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Institution.objects.filter(is_active=True)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ('institution_type', 'province', 'nsfas_accredited', 'application_open')
    search_fields = ('name', 'short_name', 'city')
    ordering_fields = ('name', 'min_aps', 'application_deadline')


class InstitutionDetailView(generics.RetrieveAPIView):
    serializer_class = InstitutionDetailSerializer
    permission_classes = (permissions.AllowAny,)
    queryset = Institution.objects.filter(is_active=True)
    lookup_field = 'slug'
