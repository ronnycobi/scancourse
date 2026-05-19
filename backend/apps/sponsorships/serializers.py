from rest_framework import serializers
from .models import Sponsor, SponsorshipPlan, Sponsorship, SponsorshipImpression, SponsorshipClick


class SponsorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sponsor
        fields = '__all__'


class SponsorshipPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorshipPlan
        fields = '__all__'


class SponsorshipSerializer(serializers.ModelSerializer):
    sponsor_name = serializers.CharField(source='sponsor.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    bursary_name = serializers.CharField(source='bursary.name', read_only=True)
    is_currently_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Sponsorship
        fields = '__all__'


class TrackEventSerializer(serializers.Serializer):
    sponsorship_id = serializers.IntegerField()
    placement = serializers.CharField(max_length=50, required=False, default='unknown')


class TrackClickSerializer(serializers.Serializer):
    sponsorship_id = serializers.IntegerField()
    action = serializers.ChoiceField(choices=['view', 'apply', 'save'], default='view')
    referrer = serializers.CharField(max_length=100, required=False, allow_blank=True)
