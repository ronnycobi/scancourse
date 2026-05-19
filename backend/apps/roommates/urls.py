from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.MyProfileView.as_view(), name='roommate-profile'),
    path('matches/', views.MatchesView.as_view(), name='roommate-matches'),
    path('my-matches/', views.MyMatchesView.as_view(), name='roommate-my-matches'),
    path('<int:pk>/like/', views.LikeView.as_view(), name='roommate-like'),
    path('<int:pk>/pass/', views.PassView.as_view(), name='roommate-pass'),
    path('<int:pk>/messages/', views.MessageThreadView.as_view(), name='roommate-messages'),
]
