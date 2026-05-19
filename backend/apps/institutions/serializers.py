from rest_framework import serializers
from .models import Institution


class InstitutionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = (
            'id', 'name', 'short_name', 'slug', 'institution_type', 'province',
            'city', 'logo', 'logo_url', 'cover_image_url',
            'application_open', 'application_deadline', 'application_url',
            'website', 'nsfas_accredited', 'min_aps',
        )


class InstitutionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = '__all__'
