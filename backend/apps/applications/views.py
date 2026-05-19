from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from .models import Application, ApplicationDocument, ApplicationEvent
from .serializers import (
    ApplicationListSerializer, ApplicationDetailSerializer,
    ApplicationCreateSerializer, StatusUpdateSerializer,
    ApplicationDocumentSerializer,
)

# Documents that most SA institutions require by default
DEFAULT_REQUIRED_DOCS = [
    'id_copy', 'matric_certificate', 'nsc_results',
    'proof_of_residence', 'parent_income',
]


class ApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationListSerializer

    def get_queryset(self):
        qs = Application.objects.filter(user=self.request.user).select_related(
            'institution', 'course'
        ).prefetch_related('required_documents')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationCreateSerializer

    def perform_create(self, serializer):
        application = serializer.save(user=self.request.user)
        # Auto-create default required document checklist
        for doc_type in DEFAULT_REQUIRED_DOCS:
            ApplicationDocument.objects.create(
                application=application,
                document_type=doc_type,
                is_required=True,
            )
        ApplicationEvent.objects.create(
            application=application,
            title='Application started',
            description=f'Created draft for {application.institution.name}',
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            ApplicationDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED,
        )


class ApplicationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationDetailSerializer

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).prefetch_related(
            'required_documents', 'events'
        )


class ApplicationStatusUpdateView(APIView):
    def post(self, request, pk):
        try:
            app = Application.objects.get(pk=pk, user=request.user)
        except Application.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = app.status
        new_status = serializer.validated_data['status']
        note = serializer.validated_data.get('note', '')

        app.status = new_status
        if new_status == 'submitted' and not app.submitted_at:
            app.submitted_at = timezone.now()
        app.save()

        ApplicationEvent.objects.create(
            application=app,
            title=f'Status: {old_status} → {new_status}',
            description=note,
        )

        return Response(ApplicationDetailSerializer(app).data)


class ApplicationDocumentUpdateView(APIView):
    def patch(self, request, pk, doc_id):
        try:
            doc = ApplicationDocument.objects.get(pk=doc_id, application__pk=pk, application__user=request.user)
        except ApplicationDocument.DoesNotExist:
            return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        document_id = request.data.get('document_id')
        if document_id:
            doc.document_id = document_id
        doc.save()

        return Response(ApplicationDocumentSerializer(doc).data)


class ApplicationStatsView(APIView):
    def get(self, request):
        qs = Application.objects.filter(user=request.user)
        stats = {
            'total': qs.count(),
            'in_progress': qs.filter(status__in=['draft', 'in_progress']).count(),
            'submitted': qs.filter(status__in=['submitted', 'under_review']).count(),
            'offers': qs.filter(status__in=['conditional_offer', 'firm_offer', 'accepted']).count(),
            'rejected': qs.filter(status='rejected').count(),
            'closing_soon': qs.filter(
                deadline__gte=timezone.now().date(),
                deadline__lte=timezone.now().date() + timezone.timedelta(days=14),
            ).exclude(status__in=['submitted', 'accepted', 'rejected', 'withdrawn']).count(),
        }
        return Response(stats)
