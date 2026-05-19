from django.urls import path
from . import views

urlpatterns = [
    path('', views.BursaryListView.as_view(), name='bursary-list'),
    path('stats/', views.BursaryStatsView.as_view(), name='bursary-stats'),
    path('recommend/', views.BursaryRecommendView.as_view(), name='bursary-recommend'),
    path('<int:pk>/', views.BursaryDetailView.as_view(), name='bursary-detail'),
]
