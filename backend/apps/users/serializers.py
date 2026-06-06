from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, SavedItem


import re


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password_confirm')

    # ── Field-level checks (run independently — DRF reports them under
    #    the field key so the Flutter client can show inline errors).
    def validate_first_name(self, value):
        v = (value or '').strip()
        if not v:
            raise serializers.ValidationError('Please enter your first name.')
        if not re.match(r"^[A-Za-zÀ-ɏ'\- ]+$", v):
            raise serializers.ValidationError(
                'First name can only contain letters, spaces, hyphens or apostrophes.')
        return v

    def validate_last_name(self, value):
        v = (value or '').strip()
        if not v:
            raise serializers.ValidationError('Please enter your last name.')
        if not re.match(r"^[A-Za-zÀ-ɏ'\- ]+$", v):
            raise serializers.ValidationError(
                'Last name can only contain letters, spaces, hyphens or apostrophes.')
        return v

    def validate_username(self, value):
        v = (value or '').strip()
        if len(v) < 3:
            raise serializers.ValidationError('Username must be at least 3 characters.')
        if not re.match(r'^[A-Za-z0-9_.]+$', v):
            raise serializers.ValidationError(
                'Username can only contain letters, numbers, dots and underscores.')
        return v

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Passwords do not match.'})
        # Run the FULL Django password validator chain — length, common,
        # numeric-only, similarity, AND our LetterDigitValidator. Without
        # this, weak passwords like '12345678' were sneaking through.
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password(
                data['password'],
                user=User(
                    email=data.get('email', ''),
                    username=data.get('username', ''),
                    first_name=data.get('first_name', ''),
                    last_name=data.get('last_name', ''),
                ),
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
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


def _sync_singular_from_plural(instance):
    """Helper — when the plural list is set, keep the singular field
    pointing at the first item so existing matcher/recommender code
    (which still reads the singular) keeps working."""
    if instance.preferred_fields:
        instance.preferred_field = instance.preferred_fields[0]
    if instance.preferred_study_provinces:
        instance.preferred_study_province = instance.preferred_study_provinces[0]
    if instance.dream_careers:
        instance.dream_career = instance.dream_careers[0]


class UserProfileSerializer(serializers.ModelSerializer):
    # Plural fields, exposed as plain JSON lists.
    preferred_fields = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False)
    preferred_study_provinces = serializers.ListField(
        child=serializers.CharField(max_length=3), required=False)
    dream_careers = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'profile_picture', 'grade', 'province',
            # Singular — still returned for old API clients
            'preferred_field', 'preferred_study_province', 'dream_career',
            # New plural — what the latest Flutter app reads/writes
            'preferred_fields', 'preferred_study_provinces', 'dream_careers',
            'preferred_language', 'onboarding_completed', 'created_at',
        )
        read_only_fields = ('id', 'email', 'created_at')

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        _sync_singular_from_plural(instance)
        instance.save(update_fields=[
            'preferred_field', 'preferred_study_province', 'dream_career',
        ])
        return instance


class OnboardingSerializer(serializers.ModelSerializer):
    preferred_fields = serializers.ListField(
        child=serializers.CharField(max_length=100), required=False)
    preferred_study_provinces = serializers.ListField(
        child=serializers.CharField(max_length=3), required=False)
    dream_careers = serializers.ListField(
        child=serializers.CharField(max_length=200), required=False)

    class Meta:
        model = User
        fields = (
            'grade', 'province',
            'preferred_field', 'preferred_study_province', 'dream_career',
            'preferred_fields', 'preferred_study_provinces', 'dream_careers',
        )
        # All optional so users can Skip without selecting everything.
        extra_kwargs = {f: {'required': False, 'allow_null': True} for f in fields}

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        _sync_singular_from_plural(instance)
        instance.onboarding_completed = True
        instance.save()
        return instance

    def to_representation(self, instance):
        # Return the full user so the Flutter app can update auth state
        # (otherwise isOnboarded stays false and the router redirects back here).
        return UserProfileSerializer(instance).data


class SavedItemSerializer(serializers.ModelSerializer):
    # Embed the underlying item's display data so the mobile "Saved" screen
    # can show real names (e.g. "BCom Accounting · UCT") instead of just
    # "Course #42".
    item_name = serializers.SerializerMethodField()
    item_subtitle = serializers.SerializerMethodField()
    # Light per-type metadata so the Saved screen can sort/section/sweep
    # without a second roundtrip — currently {deadline: ISO date} for
    # bursaries; empty for other types.
    meta = serializers.SerializerMethodField()

    class Meta:
        model = SavedItem
        fields = (
            'id', 'item_type', 'item_id', 'saved_at',
            'item_name', 'item_subtitle', 'meta',
        )
        read_only_fields = (
            'id', 'saved_at', 'item_name', 'item_subtitle', 'meta')

    def _lookup(self, obj):
        """Cached per-request lookup of the underlying object."""
        cache_key = f'_resolved_{obj.item_type}_{obj.item_id}'
        ctx = self.context.setdefault('_resolved', {})
        if cache_key in ctx:
            return ctx[cache_key]

        try:
            if obj.item_type == 'course':
                from apps.courses.models import Course
                row = Course.objects.filter(pk=obj.item_id).only(
                    'id', 'name', 'field').first()
                if row:
                    ctx[cache_key] = (row.name, row.field or '')
                    return ctx[cache_key]
            elif obj.item_type == 'bursary':
                from apps.bursaries.models import Bursary
                row = Bursary.objects.filter(pk=obj.item_id).only(
                    'id', 'name', 'provider', 'application_deadline').first()
                if row:
                    ctx[cache_key] = (row.name, row.provider or '')
                    # Cache the deadline alongside so get_meta is cheap.
                    self.context.setdefault('_meta', {})[
                        cache_key] = {
                        'deadline': row.application_deadline.isoformat()
                        if row.application_deadline else None,
                    }
                    return ctx[cache_key]
            elif obj.item_type == 'accommodation':
                from apps.accommodation.models import Accommodation
                row = Accommodation.objects.filter(pk=obj.item_id).only(
                    'id', 'name', 'city').first()
                if row:
                    ctx[cache_key] = (row.name, row.city or '')
                    return ctx[cache_key]
            elif obj.item_type == 'institution':
                from apps.institutions.models import Institution
                row = Institution.objects.filter(pk=obj.item_id).only(
                    'id', 'name', 'city').first()
                if row:
                    ctx[cache_key] = (row.name, row.city or '')
                    return ctx[cache_key]
        except Exception:
            pass
        ctx[cache_key] = (None, None)
        return ctx[cache_key]

    def get_item_name(self, obj):
        name, _ = self._lookup(obj)
        return name

    def get_item_subtitle(self, obj):
        _, subtitle = self._lookup(obj)
        return subtitle

    def get_meta(self, obj):
        # _lookup populates self.context['_meta'] for types that have any.
        self._lookup(obj)
        cache_key = f'_resolved_{obj.item_type}_{obj.item_id}'
        return self.context.get('_meta', {}).get(cache_key, {})


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
