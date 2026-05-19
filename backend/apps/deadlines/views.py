from rest_framework import generics, permissions
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .models import Deadline
from .serializers import DeadlineSerializer


class DeadlineListView(generics.ListAPIView):
    serializer_class = DeadlineSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ('deadline_type', 'institution')
    ordering_fields = ('deadline_date',)

    def get_queryset(self):
        return Deadline.objects.filter(is_active=True, deadline_date__gte=timezone.now().date())
