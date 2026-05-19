from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Report, Subject, APSResult
from .serializers import (
    ReportUploadSerializer, ReportSerializer, SubjectUpdateSerializer,
    APSResultSerializer, ManualEntrySerializer,
)
from .tasks import process_report
from .aps_calculator import calculate_aps


class ReportUploadView(generics.CreateAPIView):
    serializer_class = ReportUploadSerializer
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        process_report.delay(report.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        report = Report.objects.get(id=serializer.instance.id)
        return Response(ReportSerializer(report).data, status=status.HTTP_202_ACCEPTED)


class ReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).prefetch_related('subjects', 'aps_result')


class ReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)


class SubjectVerifyView(APIView):
    def patch(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        subjects_data = request.data.get('subjects', [])
        for item in subjects_data:
            try:
                subj = report.subjects.get(id=item['id'])
                subj.name = item.get('name', subj.name)
                subj.mark = item.get('mark', subj.mark)
                subj.is_verified = True
                subj.save()
            except Subject.DoesNotExist:
                continue

        # Recalculate APS after verification
        all_subjects = [{'name': s.name, 'mark': s.mark} for s in report.subjects.all()]
        aps_data = calculate_aps(all_subjects)
        APSResult.objects.update_or_create(
            report=report,
            defaults={
                'user': request.user,
                'total_aps': aps_data['total_aps'],
                'subjects_data': aps_data['subjects'],
            }
        )

        report.status = 'verified'
        report.save(update_fields=['status'])

        return Response(ReportSerializer(report).data)


class ManualEntryView(APIView):
    def post(self, request):
        serializer = ManualEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subjects = serializer.validated_data['subjects']
        aps_data = calculate_aps(subjects)

        aps_result = APSResult.objects.create(
            user=request.user,
            total_aps=aps_data['total_aps'],
            subjects_data=aps_data['subjects'],
        )

        return Response(APSResultSerializer(aps_result).data, status=status.HTTP_201_CREATED)


class APSHistoryView(generics.ListAPIView):
    serializer_class = APSResultSerializer

    def get_queryset(self):
        return APSResult.objects.filter(user=self.request.user)


class LatestAPSView(APIView):
    """
    Returns the user's BEST-MARKS-ACROSS-ALL-REPORTS snapshot.

    SA universities calculate APS from the highest mark for each subject
    across every sitting (NSC + supp + upgrades). This endpoint does the
    same so the app always reflects the strongest possible profile.
    """
    def get(self, request):
        from .aggregator import best_aps_for_user
        merged = best_aps_for_user(request.user)
        return Response({
            'id': None,
            'total_aps': merged['total_aps'],
            'subjects_data': merged['subjects'],
            'report_count': merged['report_count'],
            'source_reports': merged['source_reports'],
            'is_merged': merged['report_count'] > 1,
            'created_at': None,
        })
