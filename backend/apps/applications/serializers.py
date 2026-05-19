from rest_framework import serializers
from apps.institutions.serializers import InstitutionListSerializer
from .models import Application, ApplicationDocument, ApplicationEvent


class ApplicationDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)

    class Meta:
        model = ApplicationDocument
        fields = ('id', 'document_type', 'document_type_display', 'is_required', 'is_uploaded', 'document', 'notes')


class ApplicationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationEvent
        fields = ('id', 'title', 'description', 'event_date')


class ApplicationListSerializer(serializers.ModelSerializer):
    institution = InstitutionListSerializer(read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents_required = serializers.SerializerMethodField()
    documents_uploaded = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = (
            'id', 'institution', 'course_name', 'status', 'status_display',
            'application_reference', 'deadline', 'days_until_deadline',
            'progress_percent', 'is_priority', 'documents_required', 'documents_uploaded',
            'submitted_at', 'updated_at',
        )

    def get_documents_required(self, obj):
        return obj.required_documents.filter(is_required=True).count()

    def get_documents_uploaded(self, obj):
        return obj.required_documents.filter(is_uploaded=True).count()


class ApplicationDetailSerializer(serializers.ModelSerializer):
    institution = InstitutionListSerializer(read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    required_documents = ApplicationDocumentSerializer(many=True, read_only=True)
    events = ApplicationEventSerializer(many=True, read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = '__all__'


class ApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ('institution', 'course', 'deadline', 'application_url', 'notes', 'is_priority')


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES)
    note = serializers.CharField(required=False, allow_blank=True, max_length=500)
