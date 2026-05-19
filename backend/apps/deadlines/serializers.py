from rest_framework import serializers
from .models import Deadline


class DeadlineSerializer(serializers.ModelSerializer):
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Deadline
        fields = '__all__'

    def get_days_remaining(self, obj):
        from django.utils import timezone
        delta = obj.deadline_date - timezone.now().date()
        return delta.days
