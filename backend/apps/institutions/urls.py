from django.urls import path
from . import views

urlpatterns = [
    path('', views.InstitutionListView.as_view(), name='institution-list'),
    path('<slug:slug>/', views.InstitutionDetailView.as_view(), name='institution-detail'),
]
