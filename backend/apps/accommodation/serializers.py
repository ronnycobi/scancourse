from rest_framework import serializers
from .models import Accommodation, AccommodationImage


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ('id', 'image', 'is_primary', 'order')


class AccommodationSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)
    nearby_institution_name = serializers.CharField(source='nearby_institution.name', read_only=True)

    class Meta:
        model = Accommodation
        fields = '__all__'
