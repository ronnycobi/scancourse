from rest_framework import serializers
from .models import Report, Subject, APSResult


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'normalized_name', 'mark', 'level', 'is_verified', 'is_life_orientation')


class SubjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'mark')


class ReportUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ('id', 'file', 'file_type')
        # file_type is derived from the upload extension; clients don't send it.
        extra_kwargs = {'file_type': {'required': False, 'read_only': True}}

    def validate_file(self, value):
        ext = value.name.split('.')[-1].lower()
        if ext not in ('pdf', 'jpg', 'jpeg', 'png', 'heic'):
            raise serializers.ValidationError('Unsupported file type. Use PDF, JPG, PNG, or HEIC.')
        if value.size > 20 * 1024 * 1024:
            raise serializers.ValidationError('File too large. Maximum size is 20MB.')
        return value

    def validate(self, data):
        ext = data['file'].name.split('.')[-1].lower()
        data['file_type'] = 'pdf' if ext == 'pdf' else 'image'
        return data


class ReportSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    aps_result = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = (
            'id', 'file', 'file_type', 'status', 'grade', 'academic_year',
            'school_name', 'subjects', 'aps_result', 'created_at',
        )

    def get_aps_result(self, obj):
        if hasattr(obj, 'aps_result'):
            return APSResultSerializer(obj.aps_result).data
        return None


class APSResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = APSResult
        fields = ('id', 'total_aps', 'subjects_data', 'created_at')


class ManualEntrySerializer(serializers.Serializer):
    subjects = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        min_length=1,
        max_length=15,
    )

    def validate_subjects(self, value):
        for item in value:
            if 'name' not in item or 'mark' not in item:
                raise serializers.ValidationError('Each subject must have name and mark.')
            try:
                mark = int(item['mark'])
                if not (0 <= mark <= 100):
                    raise serializers.ValidationError(f'Mark must be 0-100, got {mark}.')
            except (ValueError, TypeError):
                raise serializers.ValidationError(f'Invalid mark: {item["mark"]}')
        return value
