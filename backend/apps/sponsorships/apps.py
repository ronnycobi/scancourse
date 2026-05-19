from django.apps import AppConfig


class SponsorshipsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.sponsorships'

    def ready(self):
        from . import signals  # noqa
