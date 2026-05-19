"""URL config for local-dev mode (excludes whatsapp, search)."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path('outcomes/', include('apps.outcomes.urls')),
    path('sponsorships/', include('apps.sponsorships.urls')),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tools/import/', include('apps.course_importer.urls')),
    path('api/v1/', include(api_v1)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
