from django.urls import path
from . import views

urlpatterns = [
    path('', views.SearchView.as_view(), name='search'),
    path('suggest/', views.SearchSuggestView.as_view(), name='search-suggest'),
]
