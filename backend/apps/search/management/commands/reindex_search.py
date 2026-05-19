from django.core.management.base import BaseCommand
from apps.search.tasks import reindex_all


class Command(BaseCommand):
    help = 'Re-index all courses, institutions, and bursaries into Meilisearch.'

    def handle(self, *args, **options):
        self.stdout.write('Starting full reindex...')
        result = reindex_all.apply()  # synchronous
        self.stdout.write(self.style.SUCCESS('Done.'))
