from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan-list'),
    path('track/impression/', views.TrackImpressionView.as_view(), name='track-impression'),
    path('track/click/', views.TrackClickView.as_view(), name='track-click'),
    path('<int:sponsorship_id>/analytics/', views.SponsorAnalyticsView.as_view(), name='analytics'),
]
