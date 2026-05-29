from django.db.models import Case, IntegerField, Value, When, F
from rest_framework import generics, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from scancourse.pagination import LargeResultsSetPagination
from .models import Accommodation
from .serializers import AccommodationSerializer


class AccommodationListView(generics.ListAPIView):
    serializer_class = AccommodationSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = LargeResultsSetPagination
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
        #   1. NEXT TO an institution where they SAVED a course (they want to
        #      study there, so accommodation there is the most relevant)
        #   2. in their home / preferred-study province (close by)
        #   3. NSFAS-accredited (most students rely on it)
        #   4. closest to campus
        #   5. cheapest
        # An explicit ?ordering= still wins (applied by OrderingFilter after).
        provinces: set[str] = set()
        saved_institution_ids: set[int] = set()
        user = self.request.user
        if user.is_authenticated:
            if getattr(user, 'province', None):
                provinces.add(user.province)
            provinces.update(getattr(user, 'preferred_study_provinces', None) or [])

            # Institutions (and their provinces) the user has shown interest
            # in by saving a course there.
            from apps.users.models import SavedItem
            from apps.courses.models import CourseOffering
            saved_course_ids = list(
                SavedItem.objects.filter(user=user, item_type='course')
                .values_list('item_id', flat=True)
            )
            if saved_course_ids:
                for inst_id, prov in (
                    CourseOffering.objects
                    .filter(course_id__in=saved_course_ids, is_active=True)
                    .values_list('institution_id', 'institution__province')
                    .distinct()
                ):
                    if inst_id:
                        saved_institution_ids.add(inst_id)
                    if prov:
                        provinces.add(prov)

        # 1. Next to a saved-course institution.
        if saved_institution_ids:
            qs = qs.annotate(_saved_inst=Case(
                When(nearby_institution_id__in=saved_institution_ids, then=Value(0)),
                default=Value(1), output_field=IntegerField(),
            ))
        else:
            qs = qs.annotate(_saved_inst=Value(1, output_field=IntegerField()))

        # 2. In a relevant province.
        if provinces:
            qs = qs.annotate(_near=Case(
                When(province__in=provinces, then=Value(0)),
                default=Value(1), output_field=IntegerField(),
            ))
        else:
            qs = qs.annotate(_near=Value(1, output_field=IntegerField()))

        # 3. NSFAS-accredited.
        qs = qs.annotate(_nsfas=Case(
            When(nsfas_accredited=True, then=Value(0)),
            default=Value(1), output_field=IntegerField(),
        ))

        return qs.order_by(
            '_saved_inst',
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
