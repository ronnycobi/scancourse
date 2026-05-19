"""
AI-powered course extractor — uses Gemini to pull structured course data
from ANY university's URL or PDF.

Examples:
  # Extract from a URL
  python manage.py extract_courses --url https://www.uj.ac.za/study-at-uj/find-a-programme/
  python manage.py extract_courses --url https://www.wits.ac.za/undergraduate/

  # Extract from a downloaded prospectus PDF
  python manage.py extract_courses --pdf ~/Downloads/uct_prospectus_2025.pdf --institution UCT

  # Extract from raw text
  python manage.py extract_courses --text "BSc Computer Science: 3 years, APS 32..." --institution UJ

  # Dry run (preview without saving)
  python manage.py extract_courses --url https://... --dry-run

The command:
1. Fetches the URL (or reads the PDF/text)
2. Sends content to Gemini with a structured extraction prompt
3. Parses Gemini's JSON output
4. Reviews + saves Course + CourseOffering records
"""
import json
import logging
import re
import sys

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import google.generativeai as genai

from apps.courses.models import Course, CourseOffering
from apps.institutions.models import Institution

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """You are extracting structured course/programme data from South African university content.

For EACH programme/course you can identify, return a JSON object with these fields:

{
  "name": "Full course name (e.g. 'Bachelor of Commerce in Accounting')",
  "field": "ONE of: engineering, health, business, law, humanities, science, education, arts, agriculture, ict, built_environment, other",
  "level": "ONE of: certificate, diploma, advanced_diploma, degree, honours, masters, phd, n1_n6, nc_v",
  "duration_years": 3.0,           // number, null if unknown
  "min_aps": 28,                    // integer 0-50, 0 if unknown
  "description": "Short 1-2 sentence summary",
  "career_opportunities": "Comma-separated list of common job roles, or empty",
  "subject_requirements": [         // list of mandatory school subjects
    {"subject": "Mathematics", "min_level": 5},
    {"subject": "English", "min_level": 4}
  ],
  "application_deadline": "YYYY-MM-DD",  // null if not stated
  "fees_per_year": 65000,                // ZAR, null if unknown
  "source_excerpt": "..."                // 1-line quote from source for verification
}

Return a JSON ARRAY of these objects. If no programmes are found, return [].

Important:
- Only extract programmes/qualifications/courses students can apply to
- Skip generic department/faculty pages
- For "min_level" in subject_requirements, NSC level 1-7 (where 4 = 50-59%, 5 = 60-69%)
- Be conservative — null is better than wrong
- Output ONLY valid JSON, no markdown, no explanation
"""


class Command(BaseCommand):
    help = 'Extract course data from URLs / PDFs / text using Gemini AI'

    def add_arguments(self, parser):
        parser.add_argument('--url', help='URL to fetch and extract from')
        parser.add_argument('--pdf', help='Path to a PDF file')
        parser.add_argument('--text', help='Raw text to extract from')
        parser.add_argument('--institution', help='Institution short name (e.g. UJ, UCT)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving to DB')
        parser.add_argument('--max-chars', type=int, default=80000, help='Max chars to send to Gemini')

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY:
            raise CommandError('GEMINI_API_KEY environment variable is required')

        genai.configure(api_key=settings.GEMINI_API_KEY)

        # 1. Get content
        content = self._get_content(options)
        if not content:
            raise CommandError('No content to extract from')

        if len(content) > options['max_chars']:
            self.stdout.write(self.style.WARNING(
                f'Content is {len(content)} chars — truncating to {options["max_chars"]}'
            ))
            content = content[:options['max_chars']]

        # 2. Run Gemini extraction
        self.stdout.write(f'\n→ Sending {len(content)} chars to Gemini ({settings.GEMINI_MODEL})...')
        extracted = self._extract_with_gemini(content)
        if not extracted:
            raise CommandError('Gemini returned no programmes. Check the source content.')

        self.stdout.write(self.style.SUCCESS(f'✓ Extracted {len(extracted)} programmes'))

        # 3. Show preview
        for i, prog in enumerate(extracted[:10], 1):
            self.stdout.write(
                f'\n  {i}. {prog.get("name")}\n'
                f'     Field: {prog.get("field")} · Level: {prog.get("level")}\n'
                f'     APS: {prog.get("min_aps") or "?"} · Duration: {prog.get("duration_years") or "?"} years'
            )
        if len(extracted) > 10:
            self.stdout.write(f'\n  ... and {len(extracted) - 10} more')

        # 4. Save to DB unless dry-run
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n[dry-run] not saved'))
            return

        self._save(extracted, options.get('institution'))

    # ────────────────────────────────────────────────────────────
    def _get_content(self, options):
        if options.get('url'):
            return self._fetch_url(options['url'])
        if options.get('pdf'):
            return self._read_pdf(options['pdf'])
        if options.get('text'):
            return options['text']
        return None

    def _fetch_url(self, url: str) -> str:
        self.stdout.write(f'→ Fetching {url}')
        resp = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ScancourseBot/1.0)',
        })
        resp.raise_for_status()

        # Strip to text — minimal HTML cleanup so Gemini doesn't waste tokens on tags
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            return soup.get_text('\n', strip=True)
        except ImportError:
            return resp.text

    def _read_pdf(self, path: str) -> str:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise CommandError('Install PyPDF2 first: pip install PyPDF2')
        reader = PdfReader(path)
        return '\n'.join(p.extract_text() or '' for p in reader.pages)

    # ────────────────────────────────────────────────────────────
    def _extract_with_gemini(self, content: str) -> list[dict]:
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=EXTRACTION_PROMPT,
        )
        response = model.generate_content(
            content,
            generation_config={
                'temperature': 0.2,
                'max_output_tokens': 8192,
                'response_mime_type': 'application/json',
            },
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            self.stderr.write(f'JSON parse failed: {e}')
            self.stderr.write(f'Raw response: {response.text[:500]}')
            return []

    # ────────────────────────────────────────────────────────────
    def _save(self, programmes: list[dict], institution_short_name: str | None):
        institution = None
        if institution_short_name:
            try:
                institution = Institution.objects.get(short_name=institution_short_name)
                self.stdout.write(f'\n→ Linking offerings to {institution.name}')
            except Institution.DoesNotExist:
                self.stderr.write(self.style.ERROR(
                    f'Institution {institution_short_name!r} not found. Skipping offerings.'
                ))

        valid_fields = [c[0] for c in Course._meta.get_field('field').choices]
        valid_levels = [c[0] for c in Course._meta.get_field('level').choices]

        new_courses, new_offerings, skipped = 0, 0, 0
        for p in programmes:
            name = p.get('name', '').strip()
            if len(name) < 5:
                skipped += 1
                continue

            field = p.get('field', 'other')
            if field not in valid_fields:
                field = 'other'

            level = p.get('level', 'degree')
            if level not in valid_levels:
                level = 'degree'

            course, created = Course.objects.get_or_create(
                name=name,
                defaults={
                    'field': field,
                    'level': level,
                    'duration_years': p.get('duration_years'),
                    'description': p.get('description', '')[:5000],
                    'career_opportunities': p.get('career_opportunities', '')[:2000],
                    'fees_per_year': p.get('fees_per_year'),
                    'is_active': True,
                },
            )
            if created:
                new_courses += 1
                self.stdout.write(f'  + Course: {name}')

            if institution:
                offering, off_created = CourseOffering.objects.get_or_create(
                    course=course, institution=institution,
                    defaults={
                        'min_aps': p.get('min_aps') or institution.min_aps,
                        'subject_requirements': p.get('subject_requirements', []),
                        'application_deadline': p.get('application_deadline'),
                        'is_active': True,
                    },
                )
                if off_created:
                    new_offerings += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✓ Done: {new_courses} new courses, {new_offerings} new offerings, {skipped} skipped'
        ))
