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
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime as _datetime
from .models import SavedItem

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)
    throttle_scope = 'register'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(TokenResponseSerializer.get_tokens(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_scope = 'login'

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
    throttle_scope = 'login'

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
    throttle_scope = 'password_reset'

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        if not email:
            return Response({'detail': 'Email is required.'}, status=400)
        user = User.objects.filter(email__iexact=email).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # Web URL hosts the reset form — works on any device without
            # the app installed. The token + uid stay hidden from the
            # user; they just tap the button in the email.
            base = getattr(
                settings, 'WEBSITE_BASE_URL', 'https://scancourse.co.za')
            reset_url = f'{base}/reset-password/?uid={uid}&token={token}'
            ctx = {
                'first_name': user.first_name or 'there',
                'reset_url': reset_url,
                'year': _datetime.now().year,
            }
            html_body = render_to_string('emails/password_reset.html', ctx)
            text_body = render_to_string('emails/password_reset.txt', ctx)
            msg = EmailMultiAlternatives(
                subject='Reset your Scancourse password',
                body=text_body,
                from_email=getattr(
                    settings, 'DEFAULT_FROM_EMAIL', 'info@scancourse.co.za'),
                to=[user.email],
            )
            msg.attach_alternative(html_body, 'text/html')
            # fail_silently=False so SMTP errors surface in logs — we
            # already validated the SMTP wiring works end-to-end.
            msg.send(fail_silently=False)
        # Always 200 — don't reveal existence of accounts.
        return Response({'detail': 'If that account exists, a reset link has been sent.'})


class PasswordResetConfirmView(APIView):
    """
    POST /auth/password-reset/confirm/  body: {uid, token, new_password}
    """
    permission_classes = (permissions.AllowAny,)
    throttle_scope = 'password_reset'

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


class ChangePasswordView(APIView):
    """
    POST /auth/change-password/  body: {current_password, new_password}

    Authenticated endpoint — the user must prove they know their current
    password before they can set a new one. This is the safer pattern for
    a signed-in user changing their password (vs the reset-by-email flow).
    """
    throttle_scope = 'password_reset'  # reuse the existing tight bucket

    def post(self, request):
        current = request.data.get('current_password') or ''
        new_password = request.data.get('new_password') or ''
        if not current or not new_password:
            return Response(
                {'detail': 'current_password and new_password are required.'},
                status=400,
            )
        user = request.user
        if not user.check_password(current):
            return Response(
                {'current_password': 'Current password is incorrect.'},
                status=400,
            )
        if current == new_password:
            return Response(
                {'new_password': 'New password must be different from the current one.'},
                status=400,
            )
        # Run the full Django password validator suite (length, common,
        # numeric, similarity, letter+digit) so the message matches what
        # registration enforces.
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError as DjangoValidationError
        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as e:
            return Response({'new_password': list(e.messages)}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed.'})
