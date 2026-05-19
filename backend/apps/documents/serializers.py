from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id', 'document_type', 'document_type_display', 'title',
            'original_filename', 'file_size', 'mime_type',
            'is_verified', 'is_encrypted', 'is_expired',
            'expires_at', 'notes', 'created_at', 'last_used_at', 'download_url',
        )
        read_only_fields = ('id', 'file_size', 'mime_type', 'is_verified', 'is_encrypted', 'created_at', 'last_used_at')

    def get_download_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/v1/documents/{obj.id}/download/')
        return f'/api/v1/documents/{obj.id}/download/'


class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = Document
        fields = ('document_type', 'title', 'file', 'expires_at', 'notes')

    def validate_file(self, value):
        if value.size > 15 * 1024 * 1024:
            raise serializers.ValidationError('File too large. Maximum 15MB.')

        ext = value.name.lower().split('.')[-1]
        allowed = {'pdf', 'jpg', 'jpeg', 'png', 'heic', 'webp'}
        if ext not in allowed:
            raise serializers.ValidationError(f'File type .{ext} not allowed. Use PDF, JPG, or PNG.')

        return value
