from rest_framework import serializers
from apps.institutions.serializers import InstitutionListSerializer
from .models import Course, CourseOffering, SubjectRequirement


class SubjectRequirementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectRequirement
        fields = ('subject_name', 'min_level', 'is_mandatory')


class CourseOfferingSerializer(serializers.ModelSerializer):
    institution = InstitutionListSerializer(read_only=True)
    subject_reqs = SubjectRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = CourseOffering
        fields = (
            'id', 'institution', 'min_aps', 'application_deadline',
            'application_url', 'special_requirements', 'subject_reqs', 'available_spaces',
        )


class CourseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the /courses/ list endpoint. Includes the
    primary (lowest APS) offering's institution so cards can show
    "BCom Accounting · Wits" without making a second request.
    """
    min_aps = serializers.SerializerMethodField()
    duration_years = serializers.FloatField(read_only=True)
    fees_per_year = serializers.FloatField(read_only=True)
    institution_name = serializers.SerializerMethodField()
    institution_short = serializers.SerializerMethodField()
    institution_city = serializers.SerializerMethodField()
    institution_logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            'id', 'name', 'field', 'level', 'duration_years',
            'fees_per_year', 'salary_min', 'salary_max', 'min_aps',
            'institution_name', 'institution_short',
            'institution_city', 'institution_logo_url',
        )

    def _primary(self, obj):
        """Lowest-APS active offering — most accessible entry point.
        Cached on the instance to keep it to one query per row."""
        if not hasattr(obj, '_primary_offering_cache'):
            obj._primary_offering_cache = (
                obj.offerings.filter(is_active=True)
                .select_related('institution')
                .order_by('min_aps').first()
            )
        return obj._primary_offering_cache

    def get_min_aps(self, obj):
        o = self._primary(obj)
        return o.min_aps if o else None

    def get_institution_name(self, obj):
        o = self._primary(obj)
        return o.institution.name if (o and o.institution_id) else None

    def get_institution_short(self, obj):
        o = self._primary(obj)
        return o.institution.short_name if (o and o.institution_id) else None

    def get_institution_city(self, obj):
        o = self._primary(obj)
        return o.institution.city if (o and o.institution_id) else None

    def get_institution_logo_url(self, obj):
        o = self._primary(obj)
        return o.institution.logo_url if (o and o.institution_id) else None


class CourseDetailSerializer(serializers.ModelSerializer):
    offerings = CourseOfferingSerializer(many=True, read_only=True)
    duration_years = serializers.FloatField(read_only=True)
    fees_per_year = serializers.FloatField(read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


