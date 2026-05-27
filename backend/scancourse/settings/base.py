import os
from datetime import timedelta
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])

DJANGO_APPS = [
    # MUST be before 'django.contrib.admin' — Jazzmin replaces admin templates.
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    # Lets LogoutView actually invalidate refresh tokens (it already calls
    # token.blacklist(); without this app it silently no-ops).
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    'drf_spectacular',
    'social_django',
]

LOCAL_APPS = [
    'apps.users',
    'apps.institutions',
    'apps.courses',
    'apps.bursaries',
    'apps.accommodation',
    'apps.deadlines',
    'apps.ocr',
    'apps.ai_assistant',
    'apps.notifications',
    'apps.applications',
    'apps.documents',
    'apps.roommates',
    'apps.legal',
    'apps.search',
    'apps.sponsorships',
    'apps.outcomes',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'apps.users.middleware.UserLanguageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
]

ROOT_URLCONF = 'scancourse.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'scancourse.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='postgresql://scancourse:scancourse@localhost:5432/scancourse')
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    # Custom: require at least one letter and one digit
    {'NAME': 'apps.users.password_validators.LetterDigitValidator'},
]

# Global cap on incoming request body size (defaults are 2.5MB, way too small
# for OCR uploads; per-view validators still enforce a stricter 20MB for files).
DATA_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # 25 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 25 * 1024 * 1024  # 25 MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported South African languages
LANGUAGES = [
    ('en', 'English'),
    ('zu', 'isiZulu'),
    ('xh', 'isiXhosa'),
    ('af', 'Afrikaans'),
    ('st', 'Sesotho'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # NOTE: Throttling temporarily disabled. DRF throttles need a working
    # cache backend; the production environment's default LocMemCache was
    # 500-ing under multi-worker gunicorn. Re-enable once REDIS_URL is set
    # and CACHES is wired to django_redis (see TODO in production.py).
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://localhost:8080',
])
CORS_ALLOW_CREDENTIALS = True

REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
    }
}

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Africa/Johannesburg'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# ── Push-notification cadence ────────────────────────────────────────
# Static schedule used when Celery Beat is running. Each task has its
# own per-user throttle (see apps/notifications/tasks.py) so it won't
# spam anyone — these intervals are just how OFTEN we even check.
from celery.schedules import crontab  # noqa: E402
CELERY_BEAT_SCHEDULE = {
    'bursary-deadline-reminders': {
        'task': 'apps.notifications.tasks.send_bursary_deadline_reminders',
        # Every weekday at 09:00 SAST
        'schedule': crontab(hour=9, minute=0, day_of_week='mon-fri'),
    },
    'course-deadline-reminders': {
        'task': 'apps.notifications.tasks.send_course_deadline_reminders',
        'schedule': crontab(hour=9, minute=5, day_of_week='mon-fri'),
    },
    'new-course-matches': {
        'task': 'apps.notifications.tasks.send_new_course_matches',
        # Wednesdays at 17:00 — when learners are home from school
        'schedule': crontab(hour=17, minute=0, day_of_week='wed'),
    },
    'aps-improvement-nudge': {
        'task': 'apps.notifications.tasks.send_aps_improvement_nudge',
        # Saturdays at 11:00
        'schedule': crontab(hour=11, minute=0, day_of_week='sat'),
    },
    'weekly-digest': {
        'task': 'apps.notifications.tasks.send_weekly_digest',
        # Sundays at 19:00 — when learners plan their week (FCM push)
        'schedule': crontab(hour=19, minute=0, day_of_week='sun'),
    },
    'weekly-digest-email': {
        'task': 'apps.notifications.tasks.send_weekly_digest_emails',
        # Sundays at 19:05 — five minutes after the push so they don't
        # arrive at the same instant
        'schedule': crontab(hour=19, minute=5, day_of_week='sun'),
    },
}

GEMINI_API_KEY = env('GEMINI_API_KEY', default='')
GEMINI_MODEL = env('GEMINI_MODEL', default='gemini-2.5-flash')

# Google Cloud Vision API — better OCR for report cards.
# Set ONE of these in your .env / shell:
#   GOOGLE_CLOUD_API_KEY=...   (simplest — Google Cloud API key)
#   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json  (production)
GOOGLE_CLOUD_API_KEY = env('GOOGLE_CLOUD_API_KEY', default='')
GOOGLE_APPLICATION_CREDENTIALS = env(
    'GOOGLE_APPLICATION_CREDENTIALS', default='',
)

# Meilisearch
MEILISEARCH_URL = env('MEILISEARCH_URL', default='http://meilisearch:7700')
MEILISEARCH_MASTER_KEY = env('MEILISEARCH_MASTER_KEY', default='dev-master-key-change-in-prod')

TESSERACT_CMD = env('TESSERACT_CMD', default='/usr/bin/tesseract')

FIREBASE_CREDENTIALS_PATH = env('FIREBASE_CREDENTIALS_PATH', default='')

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default='scancourse-media')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='af-south-1')

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = env('GOOGLE_CLIENT_ID', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = env('GOOGLE_CLIENT_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']

SPECTACULAR_SETTINGS = {
    'TITLE': 'Scancourse API',
    'DESCRIPTION': 'South African student guidance platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'apps': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}

# ── Jazzmin admin theme ──────────────────────────────────────────────
# Modern dark/light sidebar admin layout. All custom config lives here.
JAZZMIN_SETTINGS = {
    'site_title': 'Scancourse Admin',
    'site_header': 'Scancourse',
    'site_brand': 'Scancourse',
    'site_logo': 'landing/scancourse-logo.png',
    'login_logo': 'landing/scancourse-logo.png',
    'site_logo_classes': 'img-circle',
    'site_icon': 'landing/scancourse-logo.png',
    'welcome_sign': 'Welcome to the Scancourse Admin',
    'copyright': 'Scancourse · scancourse.co.za',
    'search_model': ['users.User', 'courses.Course', 'bursaries.Bursary'],

    # Top menu — links shown in the navbar
    'topmenu_links': [
        {'name': 'Dashboard', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'Website', 'url': 'https://scancourse.co.za', 'new_window': True},
        {'app': 'users'},
    ],

    # Side menu ordering — most useful sections at top
    'order_with_respect_to': [
        'users.User',
        'ocr.Report',
        'ocr.APSResult',
        'courses.Course',
        'courses.CourseOffering',
        'institutions.Institution',
        'bursaries.Bursary',
        'accommodation',
        'applications',
        'legal',
        'auth',
    ],

    # Nice icons per model
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.user': 'fas fa-user',
        'auth.Group': 'fas fa-users',
        'users.User': 'fas fa-user-graduate',
        'users.SavedItem': 'fas fa-bookmark',
        'ocr.Report': 'fas fa-file-image',
        'ocr.APSResult': 'fas fa-calculator',
        'ocr.Subject': 'fas fa-book',
        'courses.Course': 'fas fa-graduation-cap',
        'courses.CourseOffering': 'fas fa-university',
        'courses.CourseInteraction': 'fas fa-eye',
        'institutions.Institution': 'fas fa-school',
        'bursaries.Bursary': 'fas fa-hand-holding-usd',
        'accommodation.Accommodation': 'fas fa-home',
        'applications.Application': 'fas fa-file-signature',
        'legal.ConsentRecord': 'fas fa-file-contract',
        'legal.DataExportRequest': 'fas fa-file-export',
        'legal.AccountDeletionRequest': 'fas fa-user-times',
        'notifications': 'fas fa-bell',
        'ai_assistant.ChatSession': 'fas fa-robot',
        'token_blacklist': 'fas fa-key',
    },
    'default_icon_parents': 'fas fa-folder',
    'default_icon_children': 'fas fa-circle',

    # UI behaviour
    'related_modal_active': True,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,

    # Custom links in the user dropdown (top right)
    'usermenu_links': [
        {'name': 'View website', 'url': 'https://scancourse.co.za', 'new_window': True},
        {'model': 'auth.user'},
    ],

    # Custom CSS additions
    'custom_css': None,
    'custom_js': None,
}

JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': True,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': 'navbar-primary',
    'accent': 'accent-primary',
    'navbar': 'navbar-primary navbar-dark',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': True,
    'sidebar_nav_compact_style': True,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}
