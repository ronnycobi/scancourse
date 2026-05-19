from django.urls import path
from . import views

urlpatterns = [
    path('courses/<int:course_id>/', views.CourseOutcomeView.as_view(), name='course-outcomes'),
    path('aggregate/', views.FieldAggregateView.as_view(), name='outcome-aggregate'),
    path('compare/', views.CompareOutcomesView.as_view(), name='outcome-compare'),
    path('top-paying/', views.TopPayingCoursesView.as_view(), name='top-paying'),
    path('sectors/', views.SectorListView.as_view(), name='sector-list'),
    path('employers/', views.EmployerListView.as_view(), name='employer-list'),
    path('sources/', views.DataSourceListView.as_view(), name='source-list'),
    path('<int:pk>/', views.OutcomeDetailView.as_view(), name='outcome-detail'),
]
