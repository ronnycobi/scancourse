from django.urls import path
from . import views

urlpatterns = [
    path('', views.CourseListView.as_view(), name='course-list'),
    path('match/', views.CourseMatchView.as_view(), name='course-match'),
    path('recommend/', views.CourseRecommendView.as_view(), name='course-recommend'),
    path('<int:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('<int:pk>/interact/', views.CourseInteractionView.as_view(), name='course-interact'),
    path('<int:pk>/explain-gap/', views.ExplainGapView.as_view(), name='course-explain-gap'),
]
