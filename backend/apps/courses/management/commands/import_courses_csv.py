"""
Bulk import courses from a CSV file.

Expected CSV columns (case-sensitive):
  course_name, field, level, duration_years, fees_per_year,
  description, career_opportunities, salary_min, salary_max,
  institution_short_name, min_aps, application_deadline

Usage:
  python manage.py import_courses_csv path/to/courses.csv
  python manage.py import_courses_csv path/to/courses.csv --dry-run
"""
import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from apps.courses.models import Course, CourseOffering
from apps.institutions.models import Institution

VALID_FIELDS = (
    'engineering', 'health', 'business', 'law', 'humanities',
    'science', 'education', 'arts', 'agriculture', 'ict',
    'built_environment', 'other',
)
VALID_LEVELS = (
    'certificate', 'diploma', 'advanced_diploma', 'degree',
    'honours', 'masters', 'phd', 'n1_n6', 'nc_v',
)


class Command(BaseCommand):
    help = 'Bulk import courses from CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_path')
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        path = options['csv_path']
        dry = options['dry_run']

        try:
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f'File not found: {path}')

        self.stdout.write(f'Reading {len(rows)} rows from {path}')

        courses_created, offerings_created, errors = 0, 0, 0

        for i, row in enumerate(rows, 1):
            name = (row.get('course_name') or '').strip()
            if len(name) < 5:
                self.stderr.write(f'Row {i}: skipped (no course name)')
                errors += 1
                continue

            field = (row.get('field') or 'other').strip()
            if field not in VALID_FIELDS:
                field = 'other'

            level = (row.get('level') or 'degree').strip()
            if level not in VALID_LEVELS:
                level = 'degree'

            def _to_decimal(v):
                try: return float(v) if v else None
                except (ValueError, TypeError): return None

            def _to_int(v):
                try: return int(v) if v else None
                except (ValueError, TypeError): return None

            def _to_date(v):
                if not v: return None
                v = v.strip()
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d %B %Y', '%d %b %Y'):
                    try: return datetime.strptime(v, fmt).date()
                    except ValueError: continue
                return None

            course_data = {
                'field': field,
                'level': level,
                'duration_years': _to_decimal(row.get('duration_years')),
                'fees_per_year': _to_decimal(row.get('fees_per_year')),
                'description': (row.get('description') or '')[:5000],
                'career_opportunities': (row.get('career_opportunities') or '')[:2000],
                'salary_min': _to_int(row.get('salary_min')),
                'salary_max': _to_int(row.get('salary_max')),
                'is_active': True,
            }

            if not dry:
                course, created = Course.objects.get_or_create(name=name, defaults=course_data)
                if created:
                    courses_created += 1
                else:
                    # Update existing
                    for k, v in course_data.items():
                        if v is not None:
                            setattr(course, k, v)
                    course.save()
            else:
                created = not Course.objects.filter(name=name).exists()
                course = None

            self.stdout.write(f'  Row {i}: {"+" if created else "·"} {name}')

            inst_short = (row.get('institution_short_name') or '').strip()
            if inst_short and course:
                try:
                    inst = Institution.objects.get(short_name=inst_short)
                    if not dry:
                        offering, off_created = CourseOffering.objects.get_or_create(
                            course=course, institution=inst,
                            defaults={
                                'min_aps': _to_int(row.get('min_aps')) or inst.min_aps,
                                'application_deadline': _to_date(row.get('application_deadline')),
                                'is_active': True,
                            },
                        )
                        if off_created:
                            offerings_created += 1
                except Institution.DoesNotExist:
                    self.stderr.write(f'    ! Institution {inst_short!r} not found')

        if dry:
            self.stdout.write(self.style.WARNING('\n[dry-run] no changes saved'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'✓ Done: {courses_created} new courses, {offerings_created} new offerings, {errors} errors'
            ))
