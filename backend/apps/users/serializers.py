from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, SavedItem


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password_confirm')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled.')
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'profile_picture', 'grade', 'province',
            'preferred_field', 'preferred_study_province', 'dream_career',
            'preferred_language', 'onboarding_completed', 'created_at',
        )
        read_only_fields = ('id', 'email', 'created_at')


class OnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('grade', 'province', 'preferred_field', 'preferred_study_province', 'dream_career')
        # All optional so users can Skip without selecting everything.
        extra_kwargs = {f: {'required': False, 'allow_null': True} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.onboarding_completed = True
        instance.save()
        return instance

    def to_representation(self, instance):
        # Return the full user so the Flutter app can update auth state
        # (otherwise isOnboarded stays false and the router redirects back here).
        return UserProfileSerializer(instance).data


class SavedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedItem
        fields = ('id', 'item_type', 'item_id', 'saved_at')
        read_only_fields = ('id', 'saved_at')


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserProfileSerializer()

    @staticmethod
    def get_tokens(user):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        }


class FCMTokenSerializer(serializers.Serializer):
    fcm_token = serializers.CharField()
