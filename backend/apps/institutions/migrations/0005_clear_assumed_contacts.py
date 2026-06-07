"""Reverse the assumption-based backfill from migration 0004.

0004 filled blank institution contact_email and contact_phone with a
mix of hand-curated and domain-derived "info@<domain>" addresses. The
user rejected the assumption-based ones — better to show a clear "no
email listed" state than to surface an address that might bounce.

This migration clears whatever 0004 set. Nothing existed before 0004
ran, so blanket-resetting these fields to '' is safe and lossless.
"""
from __future__ import annotations

from django.db import migrations


def clear_contacts(apps, schema_editor):
    Institution = apps.get_model('institutions', 'Institution')
    Institution.objects.update(contact_email='', contact_phone='')


def reverse(apps, schema_editor):
    # No-op — we don't want to put the assumptions back.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institutions', '0004_backfill_contact_info'),
    ]
    operations = [
        migrations.RunPython(clear_contacts, reverse),
    ]
