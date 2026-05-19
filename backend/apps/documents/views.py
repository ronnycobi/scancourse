import logging
from io import BytesIO
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django.utils import timezone
from .models import Document, DocumentAccessLog
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .encryption import encrypt_bytes, decrypt_bytes

logger = logging.getLogger(__name__)


def log_access(document, request, action):
    DocumentAccessLog.objects.create(
        document=document,
        user=request.user if request.user.is_authenticated else None,
        action=action,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
    )


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        qs = Document.objects.filter(user=self.request.user)
        doc_type = self.request.query_params.get('type')
        if doc_type:
            qs = qs.filter(document_type=doc_type)
        return qs


class DocumentUploadView(generics.CreateAPIView):
    serializer_class = DocumentUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        original_name = uploaded_file.name
        size = uploaded_file.size
        mime = getattr(uploaded_file, 'content_type', '') or ''

        # Encrypt before saving
        try:
            raw_bytes = uploaded_file.read()
            encrypted = encrypt_bytes(raw_bytes)
        except Exception as e:
            logger.exception(f'Encryption failed: {e}')
            return Response({'detail': 'Encryption failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Replace file content with encrypted version
        from django.core.files.uploadedfile import InMemoryUploadedFile
        encrypted_file = InMemoryUploadedFile(
            file=BytesIO(encrypted),
            field_name='file',
            name=original_name + '.enc',
            content_type='application/octet-stream',
            size=len(encrypted),
            charset=None,
        )

        document = Document.objects.create(
            user=request.user,
            document_type=serializer.validated_data['document_type'],
            title=serializer.validated_data['title'],
            file=encrypted_file,
            original_filename=original_name,
            file_size=size,
            mime_type=mime,
            expires_at=serializer.validated_data.get('expires_at'),
            notes=serializer.validated_data.get('notes', ''),
            is_encrypted=True,
        )

        return Response(
            DocumentSerializer(document, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        log_access(instance, self.request, 'delete')
        instance.delete_file()
        instance.delete()


class DocumentDownloadView(APIView):
    def get(self, request, pk):
        try:
            doc = Document.objects.get(pk=pk, user=request.user)
        except Document.DoesNotExist:
            raise Http404

        try:
            with doc.file.open('rb') as f:
                encrypted = f.read()
            decrypted = decrypt_bytes(encrypted) if doc.is_encrypted else encrypted
        except Exception as e:
            logger.exception(f'Decryption failed for doc {pk}: {e}')
            return Response({'detail': 'Could not retrieve document.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        log_access(doc, request, 'download')
        doc.last_used_at = timezone.now()
        doc.save(update_fields=['last_used_at'])

        response = FileResponse(
            BytesIO(decrypted),
            as_attachment=True,
            filename=doc.original_filename,
            content_type=doc.mime_type or 'application/octet-stream',
        )
        return response


class DocumentTypesView(APIView):
    """Helper endpoint — returns the catalogue of document types for UI dropdowns."""

    def get(self, request):
        return Response([
            {'value': value, 'label': label}
            for value, label in Document.DOCUMENT_TYPES
        ])
