from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('saved/', views.SavedItemListView.as_view(), name='saved-list'),
    path('saved/<int:pk>/', views.SavedItemDeleteView.as_view(), name='saved-delete'),
    path('fcm-token/', views.FCMTokenView.as_view(), name='fcm-token'),
    path('language/', views.SetLanguageView.as_view(), name='set-language'),
    path('languages/', views.AvailableLanguagesView.as_view(), name='available-languages'),
    path('google/', views.GoogleAuthView.as_view(), name='google-auth'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
