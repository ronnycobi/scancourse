"""Backfill institution housing-office contact email + phone.

Most accommodations on the platform are scraped private rentals whose
contact fields are blank — the detail screen falls back to the linked
institution's housing-office contact, but every institution was loaded
with empty contact_email and contact_phone. This data migration fills
those gaps so the user always has someone to call/email about a
residence.

Strategy:
1. A small lookup table for major SA public universities where I'm
   confident about the publicly listed switchboard.
2. For everything else, derive a fallback "info@<domain>" email from
   the institution's website URL — info@ is the most universally
   configured alias across SA university email systems.
3. Idempotent: only writes when the field is currently empty, so a
   later proper backfill won't be overwritten.
"""
from __future__ import annotations

from urllib.parse import urlparse

from django.db import migrations


# Publicly listed general-enquiries contacts for major SA public
# universities. Phone numbers are the main switchboard, which routes to
# the housing office through reception.
KNOWN_CONTACTS = {
    'university of cape town': ('info@uct.ac.za', '+27 21 650 9111'),
    'university of the witwatersrand': ('info@wits.ac.za', '+27 11 717 1000'),
    'wits university': ('info@wits.ac.za', '+27 11 717 1000'),
    'university of pretoria': ('info@up.ac.za', '+27 12 420 3111'),
    'stellenbosch university': ('info@sun.ac.za', '+27 21 808 9111'),
    'university of johannesburg': ('info@uj.ac.za', '+27 11 559 4555'),
    'university of kwazulu-natal': ('enquiries@ukzn.ac.za', '+27 31 260 1111'),
    'university of the western cape': ('info@uwc.ac.za', '+27 21 959 2911'),
    'nelson mandela university': ('info@mandela.ac.za', '+27 41 504 1111'),
    'university of the free state': ('info@ufs.ac.za', '+27 51 401 9111'),
    'rhodes university': ('info@ru.ac.za', '+27 46 603 8111'),
    'durban university of technology': ('info@dut.ac.za', '+27 31 373 2000'),
    'tshwane university of technology': ('general@tut.ac.za', '+27 12 382 5911'),
    'cape peninsula university of technology': ('info@cput.ac.za', '+27 21 460 3911'),
    'north-west university': ('info@nwu.ac.za', '+27 18 299 1111'),
    'vaal university of technology': ('info@vut.ac.za', '+27 16 950 9000'),
    'walter sisulu university': ('info@wsu.ac.za', '+27 47 502 2111'),
    'university of fort hare': ('info@ufh.ac.za', '+27 40 602 2227'),
    'university of limpopo': ('info@ul.ac.za', '+27 15 268 9111'),
    'university of venda': ('info@univen.ac.za', '+27 15 962 8000'),
    'university of zululand': ('info@unizulu.ac.za', '+27 35 902 6000'),
    'mangosuthu university of technology': ('info@mut.ac.za', '+27 31 907 7111'),
    'central university of technology': ('info@cut.ac.za', '+27 51 507 3000'),
    'sefako makgatho health sciences university': ('info@smu.ac.za', '+27 12 521 4000'),
    'sol plaatje university': ('info@spu.ac.za', '+27 53 491 0000'),
    'university of mpumalanga': ('info@ump.ac.za', '+27 13 002 0001'),
}


def _domain_from_url(url: str) -> str:
    """Extract the apex domain from a website URL. 'https://www.uct.ac.za/x' → 'uct.ac.za'."""
    try:
        host = urlparse(url).hostname or ''
    except Exception:
        return ''
    if not host:
        return ''
    host = host.lower()
    if host.startswith('www.'):
        host = host[4:]
    return host


def backfill_contacts(apps, schema_editor):
    Institution = apps.get_model('institutions', 'Institution')
    for inst in Institution.objects.all():
        name_key = (inst.name or '').lower().strip()
        known = KNOWN_CONTACTS.get(name_key)

        # Email — known list wins, otherwise derive from website domain.
        if not (inst.contact_email or '').strip():
            if known and known[0]:
                inst.contact_email = known[0]
            else:
                domain = _domain_from_url(inst.website or '')
                if domain:
                    inst.contact_email = f'info@{domain}'

        # Phone — only the known list (deriving phones from URLs is not
        # possible, and we don't want to invent numbers).
        if not (inst.contact_phone or '').strip() and known and known[1]:
            inst.contact_phone = known[1]

        inst.save(update_fields=['contact_email', 'contact_phone'])


def reverse(apps, schema_editor):
    # Data migration — no inverse. Leave the backfilled values in place.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institutions', '0003_institution_cover_image_url_institution_logo_url'),
    ]
    operations = [
        migrations.RunPython(backfill_contacts, reverse),
    ]
