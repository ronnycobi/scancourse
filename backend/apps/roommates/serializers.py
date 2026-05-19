from rest_framework import serializers
from .models import RoommateProfile, RoommateMatch, RoommateMessage


class RoommateProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    institution_name = serializers.CharField(source='institution.name', read_only=True)

    class Meta:
        model = RoommateProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def get_user_name(self, obj):
        return obj.user.first_name or obj.user.username

    def get_user_avatar(self, obj):
        if obj.user.profile_picture:
            return obj.user.profile_picture.url
        return None


class MatchCandidateSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    score = serializers.FloatField(read_only=True)

    class Meta:
        model = RoommateProfile
        fields = (
            'id', 'user_name', 'bio', 'age', 'gender', 'institution_name', 'target_city',
            'budget_min', 'budget_max', 'sleep_schedule', 'cleanliness', 'social_level',
            'study_habits', 'languages', 'score',
        )

    def get_user_name(self, obj):
        return obj.user.first_name or obj.user.username


class RoommateMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.user.first_name', read_only=True)

    class Meta:
        model = RoommateMessage
        fields = ('id', 'sender', 'sender_name', 'recipient', 'body', 'is_read', 'created_at')
        read_only_fields = ('id', 'sender', 'is_read', 'created_at')
