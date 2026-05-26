from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from apps.legal import views as legal_views
from . import admin_dashboard

# Admin branding + custom dashboard
admin.site.site_header = 'Scancourse Admin'
admin.site.site_title = 'Scancourse'
admin.site.index_title = 'Dashboard'
admin_dashboard.install()

api_v1 = [
    path('auth/', include('apps.users.urls')),
    path('institutions/', include('apps.institutions.urls')),
    path('courses/', include('apps.courses.urls')),
    path('bursaries/', include('apps.bursaries.urls')),
    path('accommodation/', include('apps.accommodation.urls')),
    path('deadlines/', include('apps.deadlines.urls')),
    path('ocr/', include('apps.ocr.urls')),
    path('ai/', include('apps.ai_assistant.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('applications/', include('apps.applications.urls')),
    path('documents/', include('apps.documents.urls')),
    path('roommates/', include('apps.roommates.urls')),
    path('legal/', include('apps.legal.urls')),
    path('search/', include('apps.search.urls')),
    path('sponsorships/', include('apps.sponsorships.urls')),
    path('outcomes/', include('apps.outcomes.urls')),
]

urlpatterns = [
    # Public landing page — what humans see at https://scancourse.co.za
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    # Public HTML legal pages (humans). The /api/v1/legal/* versions still
    # return JSON for the mobile app.
    path('legal/privacy/', legal_views.privacy_page, name='legal-privacy-page'),
    path('legal/terms/', legal_views.terms_page, name='legal-terms-page'),
    path('legal/cookies/', legal_views.cookies_page, name='legal-cookies-page'),
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('social-auth/', include('social_django.urls', namespace='social')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
