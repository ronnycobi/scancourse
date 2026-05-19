from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

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
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_v1)),
    path('whatsapp/', include('apps.whatsapp.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('social-auth/', include('social_django.urls', namespace='social')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
