from django.urls import path
from . import views

urlpatterns = [
    path('precheck/', views.ImagePrecheckView.as_view(), name='ocr-precheck'),
    path('improvement-plan/', views.ImprovementPlanView.as_view(), name='ocr-improvement-plan'),
    path('upload/', views.ReportUploadView.as_view(), name='report-upload'),
    path('reports/', views.ReportListView.as_view(), name='report-list'),
    path('reports/<int:pk>/', views.ReportDetailView.as_view(), name='report-detail'),
    path('reports/<int:report_id>/verify/', views.SubjectVerifyView.as_view(), name='subject-verify'),
    path('manual/', views.ManualEntryView.as_view(), name='manual-entry'),
    path('aps/', views.LatestAPSView.as_view(), name='aps-latest'),
    path('aps/history/', views.APSHistoryView.as_view(), name='aps-history'),
    path('aps/journey/', views.APSJourneyView.as_view(), name='aps-journey'),
]
