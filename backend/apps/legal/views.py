"""
POPIA-compliant data rights endpoints + public legal pages.
"""
import json
import logging
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ConsentRecord, DataExportRequest, AccountDeletionRequest
from .policies import (
    PRIVACY_POLICY, TERMS_OF_SERVICE, COOKIE_POLICY,
    ACCEPTABLE_USE, ABOUT, DISCLAIMER, CONTACT, ALL_DOCS,
)


# ════════════════════════════════════════════════════════════════
# Public legal *pages* (HTML, for humans on the website)
# These render the same markdown content as the API endpoints, but
# styled like the landing page. Lives at /legal/privacy/ etc.
# ════════════════════════════════════════════════════════════════

def _legal_page(request, slug):
    """Renders any of the 7 legal docs as a styled HTML page."""
    import markdown as md  # lazy import
    if slug not in ALL_DOCS:
        from django.http import Http404
        raise Http404(f'Unknown legal doc: {slug}')
    title, doc = ALL_DOCS[slug]
    html = md.markdown(
        doc['content'],
        extensions=['extra', 'tables', 'sane_lists', 'nl2br'],
    )
    return render(request, 'legal_page.html', {
        'title': title,
        'version': doc['version'],
        'effective_date': doc['effective_date'],
        'html_content': html,
    })


def delete_data_page(request):
    """Public page where any user can request account deletion.

    Required by Google Play's data safety section — Play wants a public
    URL that a user (or Google's reviewer) can hit without installing
    the app. GET renders the form, POST verifies credentials, soft-
    disables the account, and schedules deletion 30 days out (matching
    the in-app flow via RequestAccountDeletionView).
    """
    from django.contrib.auth import authenticate
    from datetime import timedelta as _td
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()[:200]
        password = request.POST.get('password') or ''
        confirm = request.POST.get('confirm') == 'on'
        errors = []
        if not email or '@' not in email:
            errors.append('Please enter the email you signed up with.')
        if not password:
            errors.append('Please enter your password.')
        if not confirm:
            errors.append('Please tick the confirmation box.')
        if errors:
            return render(request, 'delete_data_page.html', {
                'errors': errors,
                'form': {'email': email},
            })
        # Match by email — authenticate uses USERNAME_FIELD which is email here.
        user = authenticate(request, username=email, password=password)
        if user is None:
            return render(request, 'delete_data_page.html', {
                'errors': ['Email or password is incorrect.'],
                'form': {'email': email},
            })
        # Don't double-schedule if a pending request already exists.
        existing = AccountDeletionRequest.objects.filter(
            user=user, status='pending').first()
        if existing:
            return render(request, 'delete_data_page.html', {
                'already_scheduled': True,
                'scheduled_for': existing.scheduled_for,
            })
        scheduled = timezone.now() + _td(days=30)
        AccountDeletionRequest.objects.create(
            user=user,
            reason=(request.POST.get('reason') or '')[:500],
            scheduled_for=scheduled,
        )
        user.is_active = False
        user.save(update_fields=['is_active'])
        return render(request, 'delete_data_page.html', {
            'scheduled': True,
            'scheduled_for': scheduled,
        })
    return render(request, 'delete_data_page.html', {})


def privacy_page(request):       return _legal_page(request, 'privacy')
def terms_page(request):         return _legal_page(request, 'terms')
def cookies_page(request):       return _legal_page(request, 'cookies')
def acceptable_use_page(request): return _legal_page(request, 'acceptable-use')
def about_page(request):         return _legal_page(request, 'about')
def disclaimer_page(request):    return _legal_page(request, 'disclaimer')
def contact_page(request):
    """Contact page with a built-in form that POSTs to the same URL."""
    from django.contrib import messages
    from django.shortcuts import redirect
    from django.core.mail import send_mail
    from django.conf import settings as dj_settings
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()[:120]
        email = (request.POST.get('email') or '').strip()[:200]
        subject = (request.POST.get('subject') or '').strip()[:200] or 'New contact form'
        message_text = (request.POST.get('message') or '').strip()[:5000]
        # Simple validation — anything more sophisticated belongs in a form class.
        errors = []
        if not name:
            errors.append('Please enter your name.')
        if not email or '@' not in email or '.' not in email:
            errors.append('Please enter a valid email.')
        if not message_text:
            errors.append('Please write a message.')
        if errors:
            return render(request, 'contact_page.html', {
                'errors': errors,
                'form': {'name': name, 'email': email,
                         'subject': subject, 'message': message_text},
            })
        try:
            send_mail(
                subject=f'[Scancourse contact] {subject}',
                message=(
                    f'From: {name} <{email}>\n\n'
                    f'Subject: {subject}\n\n'
                    f'{message_text}\n'
                ),
                from_email=getattr(
                    dj_settings, 'DEFAULT_FROM_EMAIL', 'info@scancourse.co.za'),
                recipient_list=['info@scancourse.co.za'],
                fail_silently=False,
            )
            return render(request, 'contact_page.html', {'sent': True})
        except Exception as e:
            logger.warning('Contact form send failed: %s', e)
            return render(request, 'contact_page.html', {
                'errors': ['Sorry, something went wrong on our side. '
                           'Please email info@scancourse.co.za directly.'],
                'form': {'name': name, 'email': email,
                         'subject': subject, 'message': message_text},
            })
    return render(request, 'contact_page.html', {})


class ContactMessageAPIView(APIView):
    """POST /api/v1/legal/contact/  body: {name, email, subject, message}

    Public endpoint (anyone can reach out, no auth needed). Throttled to
    prevent abuse. Emails the submission to info@scancourse.co.za.
    """
    permission_classes = (permissions.AllowAny,)
    throttle_scope = 'password_reset'  # reuse the 5/hour bucket

    def post(self, request):
        name = (request.data.get('name') or '').strip()[:120]
        email = (request.data.get('email') or '').strip()[:200]
        subject = (request.data.get('subject') or '').strip()[:200] or 'New contact form'
        message_text = (request.data.get('message') or '').strip()[:5000]
        errors = {}
        if not name:
            errors['name'] = 'Please enter your name.'
        if not email or '@' not in email or '.' not in email:
            errors['email'] = 'Please enter a valid email address.'
        if not message_text:
            errors['message'] = 'Please write a message.'
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            from django.core.mail import send_mail
            from django.conf import settings as dj_settings
            send_mail(
                subject=f'[Scancourse contact] {subject}',
                message=(
                    f'From: {name} <{email}>\n\n'
                    f'Subject: {subject}\n\n'
                    f'{message_text}\n'
                ),
                from_email=getattr(
                    dj_settings, 'DEFAULT_FROM_EMAIL', 'info@scancourse.co.za'),
                recipient_list=['info@scancourse.co.za'],
                fail_silently=False,
            )
            return Response({'detail': 'Message sent. We\'ll reply within 2 business days.'})
        except Exception as e:
            logger.warning('Contact form (API) send failed: %s', e)
            return Response(
                {'detail': 'Sorry, we couldn\'t send your message right now. '
                           'Please email info@scancourse.co.za directly.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

logger = logging.getLogger(__name__)
User = get_user_model()


# ════════════════════════════════════════════════════════════════
# Public legal pages (no auth)
# ════════════════════════════════════════════════════════════════

class PrivacyPolicyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({
            'version': PRIVACY_POLICY['version'],
            'effective_date': PRIVACY_POLICY['effective_date'],
            'content': PRIVACY_POLICY['content'],
        })


class TermsOfServiceView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({
            'version': TERMS_OF_SERVICE['version'],
            'effective_date': TERMS_OF_SERVICE['effective_date'],
            'content': TERMS_OF_SERVICE['content'],
        })


class CookiePolicyView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        return Response({
            'version': COOKIE_POLICY['version'],
            'effective_date': COOKIE_POLICY['effective_date'],
            'content': COOKIE_POLICY['content'],
        })


# ════════════════════════════════════════════════════════════════
# POPIA: Consent management
# ════════════════════════════════════════════════════════════════

class RecordConsentView(APIView):
    def post(self, request):
        consent_type = request.data.get('consent_type')
        granted = bool(request.data.get('granted', False))
        version = request.data.get('version', '')

        valid_types = [c[0] for c in ConsentRecord.CONSENT_TYPES]
        if consent_type not in valid_types:
            return Response({'detail': 'Invalid consent type.'}, status=status.HTTP_400_BAD_REQUEST)

        ConsentRecord.objects.create(
            user=request.user,
            consent_type=consent_type,
            granted=granted,
            version=version,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        )
        return Response({'detail': 'Consent recorded.'})


class MyConsentsView(APIView):
    def get(self, request):
        # Latest record per consent_type
        records = {}
        for r in ConsentRecord.objects.filter(user=request.user).order_by('-timestamp'):
            if r.consent_type not in records:
                records[r.consent_type] = {
                    'consent_type': r.consent_type,
                    'granted': r.granted,
                    'version': r.version,
                    'timestamp': r.timestamp.isoformat(),
                }
        return Response(list(records.values()))


# ════════════════════════════════════════════════════════════════
# POPIA: Right of access (data export)
# ════════════════════════════════════════════════════════════════

class RequestDataExportView(APIView):
    """Initiate a data export — POPIA gives users the right to all their data."""

    def post(self, request):
        # Rate limit: max 1 export per 24h
        recent = DataExportRequest.objects.filter(
            user=request.user,
            requested_at__gte=timezone.now() - timedelta(hours=24),
        ).exists()
        if recent:
            return Response({'detail': 'You already requested an export recently. Please wait 24 hours.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)

        export_req = DataExportRequest.objects.create(user=request.user, status='processing')

        # Synchronously generate the export payload (could be Celery for big users)
        try:
            payload = build_user_data_export(request.user)
            # In production: write to S3, set download_url. For dev: return inline.
            export_req.status = 'ready'
            export_req.completed_at = timezone.now()
            export_req.expires_at = timezone.now() + timedelta(days=7)
            export_req.save()
            return Response({
                'request_id': export_req.id,
                'status': 'ready',
                'data': payload,
                'expires_at': export_req.expires_at.isoformat(),
            })
        except Exception as e:
            logger.exception(f'Data export failed for {request.user.id}: {e}')
            export_req.status = 'failed'
            export_req.error = str(e)
            export_req.save()
            return Response({'detail': 'Export failed. Please try again.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def build_user_data_export(user) -> dict:
    """Collect all user data into a single JSON-serialisable dict."""
    from apps.ocr.models import APSResult, Report
    from apps.applications.models import Application
    from apps.documents.models import Document
    from apps.users.models import SavedItem
    from apps.ai_assistant.models import ChatSession

    return {
        'profile': {
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'grade': user.grade,
            'province': user.province,
            'preferred_field': user.preferred_field,
            'dream_career': user.dream_career,
            'phone_number': user.phone_number,
            'created_at': user.created_at.isoformat() if user.created_at else None,
        },
        'aps_results': [
            {'total_aps': r.total_aps, 'subjects': r.subjects_data, 'created_at': r.created_at.isoformat()}
            for r in APSResult.objects.filter(user=user)
        ],
        'reports': [
            {'id': r.id, 'status': r.status, 'school_name': r.school_name, 'created_at': r.created_at.isoformat()}
            for r in Report.objects.filter(user=user)
        ],
        'applications': [
            {
                'institution': a.institution.name,
                'course': a.course.name if a.course else None,
                'status': a.status,
                'deadline': a.deadline.isoformat() if a.deadline else None,
                'submitted_at': a.submitted_at.isoformat() if a.submitted_at else None,
            }
            for a in Application.objects.filter(user=user).select_related('institution', 'course')
        ],
        'documents': [
            {
                'title': d.title,
                'document_type': d.document_type,
                'file_size': d.file_size,
                'created_at': d.created_at.isoformat(),
            }
            for d in Document.objects.filter(user=user)
        ],
        'saved_items': [
            {'item_type': s.item_type, 'item_id': s.item_id, 'saved_at': s.saved_at.isoformat()}
            for s in SavedItem.objects.filter(user=user)
        ],
        'chat_sessions': [
            {
                'title': c.title,
                'created_at': c.created_at.isoformat(),
                'messages': [
                    {'role': m.role, 'content': m.content, 'created_at': m.created_at.isoformat()}
                    for m in c.messages.all()
                ],
            }
            for c in ChatSession.objects.filter(user=user).prefetch_related('messages')
        ],
        'consents': [
            {
                'consent_type': c.consent_type, 'granted': c.granted,
                'version': c.version, 'timestamp': c.timestamp.isoformat(),
            }
            for c in ConsentRecord.objects.filter(user=user)
        ],
        'export_meta': {
            'generated_at': timezone.now().isoformat(),
            'data_controller': 'Scancourse (Pty) Ltd',
            'contact': 'info@scancourse.co.za',
        },
    }


# ════════════════════════════════════════════════════════════════
# POPIA: Right to erasure (account deletion)
# ════════════════════════════════════════════════════════════════

class RequestAccountDeletionView(APIView):
    def post(self, request):
        # 30-day grace period — user can cancel during this time
        existing = AccountDeletionRequest.objects.filter(user=request.user, status='pending').first()
        if existing:
            return Response({
                'detail': 'A deletion request is already pending.',
                'scheduled_for': existing.scheduled_for.isoformat(),
                'request_id': existing.id,
            }, status=status.HTTP_400_BAD_REQUEST)

        scheduled = timezone.now() + timedelta(days=30)
        req = AccountDeletionRequest.objects.create(
            user=request.user,
            reason=request.data.get('reason', ''),
            scheduled_for=scheduled,
        )
        # Soft-disable account
        request.user.is_active = False
        request.user.save(update_fields=['is_active'])

        return Response({
            'request_id': req.id,
            'scheduled_for': scheduled.isoformat(),
            'detail': 'Your account has been scheduled for deletion. You have 30 days to cancel by signing in again.',
        })


class CancelAccountDeletionView(APIView):
    permission_classes = (permissions.AllowAny,)  # User may not be active

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                raise User.DoesNotExist
        except User.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        req = AccountDeletionRequest.objects.filter(user=user, status='pending').first()
        if not req:
            return Response({'detail': 'No pending deletion request.'}, status=status.HTTP_404_NOT_FOUND)

        req.status = 'cancelled'
        req.save()
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'detail': 'Deletion cancelled. Welcome back!'})
