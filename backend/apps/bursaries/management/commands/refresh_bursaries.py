"""
Refresh the bursary catalogue.

Runs the canonical seed scripts (2026 + expanded), then optionally fetches
new headlines from zabursaries.co.za and logs them for manual review.

Usage:
    python manage.py refresh_bursaries           # seed + scrape headlines
    python manage.py refresh_bursaries --no-scrape   # seed only
"""
from __future__ import annotations

import logging
import re
import sys
import importlib.util
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings

from apps.bursaries.models import Bursary

log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Refresh the bursary catalogue from canonical seed scripts + scrape new headlines'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-scrape',
            action='store_true',
            help='Skip the web scrape — only re-apply seed scripts.',
        )

    def handle(self, *args, **opts):
        self._run_seed_scripts()
        if not opts['no_scrape']:
            self._scrape_zabursaries()

        active = Bursary.objects.filter(is_active=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'Done. Active bursaries: {active}'
        ))

    def _run_seed_scripts(self):
        """Re-execute the canonical seed scripts. They are idempotent."""
        scripts_dir = Path(settings.BASE_DIR) / 'scripts'
        for name in ('seed_bursaries_2026.py', 'seed_bursaries_2026_expanded.py'):
            path = scripts_dir / name
            if not path.exists():
                self.stdout.write(self.style.WARNING(f'Skip {name} (missing)'))
                continue
            self.stdout.write(f'Running {name}…')
            # `manage.py shell <script>` style — exec the file with module
            # globals so `from apps.x import …` works.
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

    def _scrape_zabursaries(self):
        """
        Fetch the latest listings from zabursaries.co.za and log any
        bursary names we don't already have. Does NOT auto-create — student-
        facing data needs human review.
        """
        try:
            resp = requests.get('https://www.zabursaries.co.za/', timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 ScanCourse bursary refresher',
            })
            resp.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Scrape failed: {e}'))
            return

        soup = BeautifulSoup(resp.text, 'html.parser')
        existing = {b.name.lower() for b in Bursary.objects.all()}
        new_titles: list[str] = []

        for h in soup.select('h2, h3'):
            text = h.get_text(' ', strip=True)
            if not text or len(text) < 8 or len(text) > 200:
                continue
            if not re.search(r'\bbursary|scholarship|funding\b', text, re.I):
                continue
            if any(text.lower() in e or e in text.lower() for e in existing):
                continue
            new_titles.append(text)

        if not new_titles:
            self.stdout.write('No new headlines found.')
            return

        self.stdout.write(self.style.WARNING(
            f'Found {len(new_titles)} bursary headlines NOT in catalogue '
            '— review and add manually if appropriate:'
        ))
        for t in new_titles[:30]:
            self.stdout.write(f'  • {t}')
