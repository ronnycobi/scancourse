from django.urls import path
from . import views

urlpatterns = [
    path('', views.AccommodationListView.as_view(), name='accommodation-list'),
    path('<int:pk>/', views.AccommodationDetailView.as_view(), name='accommodation-detail'),
]
