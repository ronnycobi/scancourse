"""Install the weekly bursary-refresh schedule into django-celery-beat."""
from django.core.management.base import BaseCommand
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = 'Install / refresh the weekly bursary refresh Celery beat schedule.'

    def handle(self, *args, **opts):
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='0',          # 03:00 every Monday SAST
            hour='3',
            day_of_week='1',
            day_of_month='*',
            month_of_year='*',
            timezone='Africa/Johannesburg',
        )
        task, created = PeriodicTask.objects.update_or_create(
            name='Weekly bursary catalogue refresh',
            defaults={
                'crontab': schedule,
                'task': 'apps.bursaries.tasks.refresh_bursaries_task',
                'enabled': True,
                'description': 'Re-applies bursary seed data and scans for new listings every Monday at 03:00 SAST.',
            },
        )
        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(
            f'{action}: "{task.name}" (Mondays 03:00 SAST)'
        ))
