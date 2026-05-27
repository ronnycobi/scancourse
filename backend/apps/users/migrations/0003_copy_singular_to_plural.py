"""Backfill the new plural preference fields with whatever the user
already has in the singular ones."""
from django.db import migrations


def copy_forward(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for u in User.objects.iterator():
        changed = False
        if u.preferred_field and not u.preferred_fields:
            u.preferred_fields = [u.preferred_field]
            changed = True
        if u.preferred_study_province and not u.preferred_study_provinces:
            u.preferred_study_provinces = [u.preferred_study_province]
            changed = True
        if u.dream_career and not u.dream_careers:
            # dream_career was a free-text string. Treat it as a single item.
            u.dream_careers = [u.dream_career]
            changed = True
        if changed:
            u.save(update_fields=[
                'preferred_fields',
                'preferred_study_provinces',
                'dream_careers',
            ])


def copy_back(apps, schema_editor):
    # No-op reversal — we never delete the new fields' data
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_plural_preference_fields'),
    ]
    operations = [
        migrations.RunPython(copy_forward, copy_back),
    ]
