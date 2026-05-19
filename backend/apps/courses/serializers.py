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
    min_aps = serializers.SerializerMethodField()
    duration_years = serializers.FloatField(read_only=True)
    fees_per_year = serializers.FloatField(read_only=True)

    class Meta:
        model = Course
        fields = (
            'id', 'name', 'field', 'level', 'duration_years',
            'fees_per_year', 'salary_min', 'salary_max', 'min_aps',
        )

    def get_min_aps(self, obj):
        offering = obj.offerings.filter(is_active=True).order_by('min_aps').first()
        return offering.min_aps if offering else None


class CourseDetailSerializer(serializers.ModelSerializer):
    offerings = CourseOfferingSerializer(many=True, read_only=True)
    duration_years = serializers.FloatField(read_only=True)
    fees_per_year = serializers.FloatField(read_only=True)

    class Meta:
        model = Course
        fields = '__all__'


