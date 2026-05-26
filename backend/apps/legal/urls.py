from django.urls import path
from . import views

urlpatterns = [
    # Public legal pages
    path('privacy/', views.PrivacyPolicyView.as_view(), name='privacy-policy'),
    path('terms/', views.TermsOfServiceView.as_view(), name='terms-of-service'),
    path('cookies/', views.CookiePolicyView.as_view(), name='cookie-policy'),
    path('contact/', views.ContactMessageAPIView.as_view(), name='contact-message'),

    # POPIA: consent
    path('consent/', views.RecordConsentView.as_view(), name='record-consent'),
    path('consents/', views.MyConsentsView.as_view(), name='my-consents'),

    # POPIA: data rights
    path('data-export/', views.RequestDataExportView.as_view(), name='data-export'),
    path('delete-account/', views.RequestAccountDeletionView.as_view(), name='delete-account'),
    path('cancel-deletion/', views.CancelAccountDeletionView.as_view(), name='cancel-deletion'),
]
