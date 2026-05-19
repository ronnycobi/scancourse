from django.urls import path
from . import views

app_name = 'importer'

urlpatterns = [
    path('', views.home, name='home'),
    path('url/', views.parse_url, name='parse-url'),
    path('pdf/', views.parse_pdf, name='parse-pdf'),
    path('text/', views.parse_text, name='parse-text'),
    path('history/', views.history, name='history'),
    path('<int:job_id>/', views.review, name='review'),
    path('<int:job_id>/save/', views.save_courses, name='save'),
]
