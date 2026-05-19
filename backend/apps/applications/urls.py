from django.urls import path
from . import views

urlpatterns = [
    path('', views.ApplicationListView.as_view(), name='application-list'),
    path('create/', views.ApplicationCreateView.as_view(), name='application-create'),
    path('stats/', views.ApplicationStatsView.as_view(), name='application-stats'),
    path('<int:pk>/', views.ApplicationDetailView.as_view(), name='application-detail'),
    path('<int:pk>/status/', views.ApplicationStatusUpdateView.as_view(), name='application-status'),
    path('<int:pk>/documents/<int:doc_id>/', views.ApplicationDocumentUpdateView.as_view(), name='application-document'),
]
