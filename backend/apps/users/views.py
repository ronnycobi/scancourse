from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    OnboardingSerializer, SavedItemSerializer, TokenResponseSerializer,
    FCMTokenSerializer,
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from .models import SavedItem

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenResponseSerializer.get_tokens(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        return Response(TokenResponseSerializer.get_tokens(user))


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
        return Response({'detail': 'Successfully logged out.'})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class OnboardingView(generics.UpdateAPIView):
    serializer_class = OnboardingSerializer
    http_method_names = ['patch']

    def get_object(self):
        return self.request.user


class SavedItemListView(generics.ListCreateAPIView):
    serializer_class = SavedItemSerializer

    def get_queryset(self):
        return SavedItem.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SavedItemDeleteView(generics.DestroyAPIView):
    serializer_class = SavedItemSerializer

    def get_queryset(self):
        return SavedItem.objects.filter(user=self.request.user)


class FCMTokenView(APIView):
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.fcm_token = serializer.validated_data['fcm_token']
        request.user.save(update_fields=['fcm_token'])
        return Response({'detail': 'FCM token updated.'})


class SetLanguageView(APIView):
    def post(self, request):
        from django.conf import settings as django_settings
        lang = request.data.get('language')
        valid = [code for code, _ in django_settings.LANGUAGES]
        if lang not in valid:
            return Response(
                {'detail': f'Invalid language. Choose from: {valid}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        request.user.preferred_language = lang
        request.user.save(update_fields=['preferred_language'])
        return Response({'detail': 'Language updated.', 'language': lang})


class AvailableLanguagesView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        from django.conf import settings as django_settings
        return Response([
            {'code': code, 'name': name}
            for code, name in django_settings.LANGUAGES
        ])


class GoogleAuthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        from django.conf import settings

        token = request.data.get('id_token')
        if not token:
            return Response({'detail': 'id_token required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
            )
        except ValueError:
            return Response({'detail': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

        email = idinfo.get('email')
        if not email:
            return Response({'detail': 'Email not found in token.'}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
            }
        )
        return Response(TokenResponseSerializer.get_tokens(user))


class PasswordResetRequestView(APIView):
    """
    POST /auth/password-reset/  body: {email}

    Sends a password-reset email with a token+uid. Always returns 200 to
    avoid leaking which emails exist.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=400)
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f'scancourse://reset?uid={uid}&token={token}'
            send_mail(
                subject='Reset your Scancourse password',
                message=(
                    f'Hi {user.first_name or "there"},\n\n'
                    f'Use this link to reset your Scancourse password:\n\n{reset_url}\n\n'
                    f'Or open the app and use this code:\n\nUID: {uid}\nToken: {token}\n\n'
                    f'If you did not request this, ignore this email.'
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@scancourse.co.za'),
                recipient_list=[user.email],
                fail_silently=True,
            )
        # Always 200 — don't reveal existence of accounts.
        return Response({'detail': 'If that account exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    """
    POST /auth/password-reset/confirm/  body: {uid, token, new_password}
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        uid = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')
        if not (uid and token and new_password):
            return Response({'detail': 'uid, token and new_password are required.'}, status=400)
        if len(new_password) < 8:
            return Response({'detail': 'Password must be at least 8 characters.'}, status=400)
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({'detail': 'Invalid reset link.'}, status=400)
        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Reset link has expired.'}, status=400)
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password reset. You can log in now.'})
