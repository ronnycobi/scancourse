from rest_framework import serializers
from .models import Accommodation, AccommodationImage


class AccommodationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccommodationImage
        fields = ('id', 'image', 'is_primary', 'order')


class AccommodationSerializer(serializers.ModelSerializer):
    images = AccommodationImageSerializer(many=True, read_only=True)
    nearby_institution_name = serializers.CharField(
        source='nearby_institution.name', read_only=True)
    # Surface the linked institution's housing-office contact details so
    # the app can fall back to them when the residence itself has no
    # direct phone/email/website listed. Most scraped private rentals
    # have blank contact fields; without this fallback the user is
    # stranded on the detail screen.
    nearby_institution_phone = serializers.CharField(
        source='nearby_institution.contact_phone',
        read_only=True, allow_null=True, default='')
    nearby_institution_email = serializers.CharField(
        source='nearby_institution.contact_email',
        read_only=True, allow_null=True, default='')
    nearby_institution_website = serializers.CharField(
        source='nearby_institution.website',
        read_only=True, allow_null=True, default='')

    class Meta:
        model = Accommodation
        fields = '__all__'
