"""Send a test email through the configured SMTP backend and surface
any error verbatim. Used to debug SMTP wiring without touching the
production password-reset flow.

Usage (in DigitalOcean App Platform console):
    python manage.py test_email foconu.info@gmail.com
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Send a test email through the configured SMTP backend.'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Email address to send the test to')

    def handle(self, *args, **options):
        to = options['recipient']
        from_addr = getattr(
            settings, 'DEFAULT_FROM_EMAIL', 'info@scancourse.co.za')

        self.stdout.write('SMTP config:')
        self.stdout.write(f'  EMAIL_BACKEND = {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  EMAIL_HOST    = {getattr(settings, "EMAIL_HOST", "(unset)")}')
        self.stdout.write(f'  EMAIL_PORT    = {getattr(settings, "EMAIL_PORT", "(unset)")}')
        self.stdout.write(f'  EMAIL_USE_TLS = {getattr(settings, "EMAIL_USE_TLS", "(unset)")}')
        self.stdout.write(f'  EMAIL_HOST_USER = {getattr(settings, "EMAIL_HOST_USER", "(unset)")}')
        self.stdout.write(f'  EMAIL_HOST_PASSWORD = {"(set, hidden)" if getattr(settings, "EMAIL_HOST_PASSWORD", "") else "(unset)"}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL = {from_addr}')
        self.stdout.write(f'  Sending to: {to}')
        self.stdout.write('')

        try:
            send_mail(
                subject='Scancourse SMTP test',
                message=(
                    'This is a test email from Scancourse to verify that '
                    'the SMTP configuration on DigitalOcean is working. '
                    'If you received this, password reset emails will work too.'
                ),
                from_email=from_addr,
                recipient_list=[to],
                fail_silently=False,  # Surface real errors
            )
            self.stdout.write(self.style.SUCCESS('OK: send_mail returned without raising.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'FAILED: {type(e).__name__}: {e}'))
            raise
