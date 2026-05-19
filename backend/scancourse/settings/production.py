"""
Production settings for DigitalOcean App Platform / similar hosts.

Reads everything from environment variables — set these in the App Platform
"Environment Variables" section of your service:

REQUIRED:
    SECRET_KEY              long random string
    ALLOWED_HOSTS           your-app.ondigitalocean.app,scancourse.co.za
    DATABASE_URL            postgres:// — DO provides this automatically when
                            you attach a managed Postgres add-on
    GEMINI_API_KEY          for OCR + AI features

OPTIONAL:
    REDIS_URL               for Celery (otherwise tasks run inline)
    GOOGLE_CLOUD_API_KEY    extra OCR path (Gemini works without this)
    EMAIL_HOST/USER/PASS    for sending real emails
    SENTRY_DSN              for error tracking
    AWS_*                   for S3 media storage (optional)
"""
from .base import *

DEBUG = False

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Whitenoise for static files (no nginx needed)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + [m for m in MIDDLEWARE if m != 'django.middleware.security.SecurityMiddleware']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email — falls back to console if SMTP isn't configured (so password reset
# still works in dev mode, prints to logs).
if env('EMAIL_HOST', default=''):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@scancourse.co.za')

# Sentry — opt-in only.
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), CeleryIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    except ImportError:
        pass

# S3 media storage — opt-in. Without it, uploads go to local disk on the
# container (ephemeral — fine for first launch, replace before scaling).
if env('AWS_STORAGE_BUCKET_NAME', default=''):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='af-south-1')
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# Celery — fall back to running tasks synchronously if Redis isn't configured.
# That's fine for the bursary-refresh weekly cron (we can run it manually
# until a Redis add-on is attached).
if not env('REDIS_URL', default=''):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
