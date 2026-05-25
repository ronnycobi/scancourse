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
from .policies import PRIVACY_POLICY, TERMS_OF_SERVICE, COOKIE_POLICY


# ════════════════════════════════════════════════════════════════
# Public legal *pages* (HTML, for humans on the website)
# These render the same markdown content as the API endpoints, but
# styled like the landing page. Lives at /legal/privacy/ etc.
# ════════════════════════════════════════════════════════════════

_PAGE_TITLES = {
    'privacy': 'Privacy Policy',
    'terms': 'Terms of Service',
    'cookies': 'Cookie Policy',
}

_PAGE_DOCS = {
    'privacy': PRIVACY_POLICY,
    'terms': TERMS_OF_SERVICE,
    'cookies': COOKIE_POLICY,
}


def _legal_page(request, slug):
    import markdown as md  # lazy import — only the public legal pages need it
    doc = _PAGE_DOCS[slug]
    html = md.markdown(
        doc['content'],
        extensions=['extra', 'tables', 'sane_lists', 'nl2br'],
    )
    return render(request, 'legal_page.html', {
        'title': _PAGE_TITLES[slug],
        'version': doc['version'],
        'effective_date': doc['effective_date'],
        'html_content': html,
    })


def privacy_page(request):
    return _legal_page(request, 'privacy')


def terms_page(request):
    return _legal_page(request, 'terms')


def cookies_page(request):
    return _legal_page(request, 'cookies')

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
