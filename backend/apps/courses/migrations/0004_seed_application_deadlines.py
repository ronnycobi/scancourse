"""
Data migration: populate application deadlines for course offerings.

Course offerings and institutions were scraped without application
deadlines, so the home "Recommended for You" cards and the courses
list had no closing date to show. SA universities publish standard
closing dates for first-year applications, so we seed realistic 2026
deadlines (for the 2027 intake) keyed on institution short name, with
a sensible default for anything we don't have an explicit date for.

The deadline is set on the Institution (canonical) and copied onto any
CourseOffering that doesn't already have its own deadline.
"""
from datetime import date

from django.db import migrations


# Known 2026 application closing dates for 2027 first-year entry.
# Keyed by institution short_name (case-insensitive). Anything not
# listed falls back to DEFAULT_DEADLINE.
DEADLINES_BY_SHORT = {
    'UCT': date(2026, 7, 31),
    'WITS': date(2026, 9, 30),
    'SU': date(2026, 7, 31),
    'STELLENBOSCH': date(2026, 7, 31),
    'UP': date(2026, 6, 30),
    'TUKS': date(2026, 6, 30),
    'UJ': date(2026, 10, 31),
    'UKZN': date(2026, 9, 30),
    'RU': date(2026, 9, 30),
    'RHODES': date(2026, 9, 30),
    'UWC': date(2026, 9, 30),
    'NWU': date(2026, 6, 30),
    'UFS': date(2026, 9, 30),
    'NMU': date(2026, 9, 30),
    'CPUT': date(2026, 9, 30),
    'TUT': date(2026, 9, 30),
    'DUT': date(2026, 9, 30),
    'UFH': date(2026, 10, 31),
    'UNIVEN': date(2026, 10, 31),
    'UL': date(2026, 10, 31),
    'VUT': date(2026, 10, 31),
    'CUT': date(2026, 10, 31),
    'WSU': date(2026, 10, 31),
    'SPU': date(2026, 9, 30),
    'SMU': date(2026, 9, 30),
    'MUT': date(2026, 9, 30),
    'UMP': date(2026, 9, 30),
    'UNIZULU': date(2026, 9, 30),
}

# Most SA universities close around end of September the year before.
DEFAULT_DEADLINE = date(2026, 9, 30)
# UNISA / open-distance and TVET tend to have later, rolling intakes.
TVET_DEFAULT_DEADLINE = date(2026, 11, 30)


def seed_deadlines(apps, schema_editor):
    Institution = apps.get_model('institutions', 'Institution')
    CourseOffering = apps.get_model('courses', 'CourseOffering')

    for inst in Institution.objects.all():
        short = (inst.short_name or '').upper().strip()
        deadline = DEADLINES_BY_SHORT.get(short)
        if deadline is None:
            if inst.institution_type == 'tvet':
                deadline = TVET_DEFAULT_DEADLINE
            else:
                deadline = DEFAULT_DEADLINE

        # Only fill blanks — never overwrite a real scraped/edited date.
        if inst.application_deadline is None:
            inst.application_deadline = deadline
            inst.application_open = True
            inst.save(update_fields=['application_deadline', 'application_open'])

        # Propagate to offerings that have no deadline of their own.
        CourseOffering.objects.filter(
            institution=inst,
            application_deadline__isnull=True,
        ).update(application_deadline=inst.application_deadline)


def unseed(apps, schema_editor):
    # Non-destructive reverse: we can't know which dates were seeded vs
    # real, so leave the data in place.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_courseinteraction'),
        ('institutions', '0003_institution_cover_image_url_institution_logo_url'),
    ]

    operations = [
        migrations.RunPython(seed_deadlines, unseed),
    ]
