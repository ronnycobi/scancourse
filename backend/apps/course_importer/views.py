"""
Django views for the Course Importer.

URL flow:
    GET  /tools/import/                     → home (upload form)
    POST /tools/import/url/                 → parse from URL, redirect to review
    POST /tools/import/pdf/                 → parse from PDF, redirect to review
    POST /tools/import/text/                → parse from pasted text, redirect to review
    GET  /tools/import/<id>/                → review extracted courses
    POST /tools/import/<id>/save/           → save selected to DB
    GET  /tools/import/history/             → past jobs
"""
import json
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from apps.courses.models import Course, CourseOffering
from apps.institutions.models import Institution
from .models import ImportJob
from . import parser

logger = logging.getLogger(__name__)


SUPPORTED_INSTITUTIONS = [
    ('', '— Optional —'),
    ('UCT', 'UCT'),
    ('Wits', 'Wits'),
    ('UP', 'UP'),
    ('SU', 'Stellenbosch'),
    ('UJ', 'UJ'),
    ('UKZN', 'UKZN'),
    ('NMU', 'NMU'),
    ('TUT', 'TUT'),
    ('CPUT', 'CPUT'),
]


# ════════════════════════════════════════════════════════════════
# Upload form / home
# ════════════════════════════════════════════════════════════════

@staff_member_required
def home(request):
    recent_jobs = ImportJob.objects.all()[:10]
    return render(request, 'course_importer/home.html', {
        'institutions': SUPPORTED_INSTITUTIONS,
        'recent_jobs': recent_jobs,
    })


# ════════════════════════════════════════════════════════════════
# Trigger parse from each source
# ════════════════════════════════════════════════════════════════

@staff_member_required
@require_POST
def parse_url(request):
    url = request.POST.get('url', '').strip()
    institution = request.POST.get('institution', '').strip()
    if not url:
        messages.error(request, 'Please provide a URL.')
        return redirect('importer:home')

    job = ImportJob.objects.create(
        user=request.user,
        source_type='url',
        source_url=url,
        institution_short_name=institution,
        status='parsing',
    )

    try:
        parsed = parser.parse_url(url, institution)
        job.parsed_courses = [c.to_dict() for c in parsed]
        # Auto-fill institution if parser detected one
        if parsed and parsed[0].institution_short_name and not job.institution_short_name:
            job.institution_short_name = parsed[0].institution_short_name
        job.status = 'ready'
        job.save()
        messages.success(request, f'Parsed {len(parsed)} programmes from {url}.')
    except Exception as e:
        logger.exception(f'URL parse failed: {e}')
        job.status = 'failed'
        job.error_message = str(e)[:1000]
        job.save()
        messages.error(request, f'Parse failed: {e}')

    return redirect('importer:review', job_id=job.id)


@staff_member_required
@require_POST
def parse_pdf(request):
    if 'pdf' not in request.FILES:
        messages.error(request, 'Please upload a PDF.')
        return redirect('importer:home')

    pdf_file = request.FILES['pdf']
    institution = request.POST.get('institution', '').strip()

    if not pdf_file.name.lower().endswith('.pdf'):
        messages.error(request, 'Only PDF files supported.')
        return redirect('importer:home')

    if pdf_file.size > 50 * 1024 * 1024:
        messages.error(request, 'PDF too large (max 50MB).')
        return redirect('importer:home')

    job = ImportJob.objects.create(
        user=request.user,
        source_type='pdf',
        source_filename=pdf_file.name,
        source_pdf=pdf_file,
        institution_short_name=institution,
        status='parsing',
    )

    try:
        # Re-read the file from the saved field
        with job.source_pdf.open('rb') as f:
            pdf_bytes = f.read()
        parsed = parser.parse_pdf_bytes(pdf_bytes, institution)
        job.parsed_courses = [c.to_dict() for c in parsed]
        job.status = 'ready'
        job.save()
        messages.success(request, f'Parsed {len(parsed)} programmes from {pdf_file.name}.')
    except Exception as e:
        logger.exception(f'PDF parse failed: {e}')
        job.status = 'failed'
        job.error_message = str(e)[:1000]
        job.save()
        messages.error(request, f'Parse failed: {e}')

    return redirect('importer:review', job_id=job.id)


@staff_member_required
@require_POST
def parse_text(request):
    text = request.POST.get('text', '').strip()
    institution = request.POST.get('institution', '').strip()
    if not text:
        messages.error(request, 'Please paste some text.')
        return redirect('importer:home')

    job = ImportJob.objects.create(
        user=request.user,
        source_type='text',
        institution_short_name=institution,
        status='parsing',
    )

    try:
        parsed = parser.parse_text(text, institution)
        job.parsed_courses = [c.to_dict() for c in parsed]
        job.status = 'ready'
        job.save()
        messages.success(request, f'Parsed {len(parsed)} programmes.')
    except Exception as e:
        logger.exception(f'Text parse failed: {e}')
        job.status = 'failed'
        job.error_message = str(e)[:1000]
        job.save()
        messages.error(request, f'Parse failed: {e}')

    return redirect('importer:review', job_id=job.id)


# ════════════════════════════════════════════════════════════════
# Review & save
# ════════════════════════════════════════════════════════════════

@staff_member_required
def review(request, job_id):
    job = get_object_or_404(ImportJob, id=job_id)
    return render(request, 'course_importer/review.html', {
        'job': job,
        'institutions': SUPPORTED_INSTITUTIONS,
    })


@staff_member_required
@require_POST
def save_courses(request, job_id):
    job = get_object_or_404(ImportJob, id=job_id)

    # The form posts an edited courses_json field — use that, fall back to job.parsed_courses
    raw = request.POST.get('courses_json')
    try:
        courses = json.loads(raw) if raw else job.parsed_courses
    except json.JSONDecodeError:
        return HttpResponseBadRequest('Invalid courses JSON')

    valid_fields = {c[0] for c in Course._meta.get_field('field').choices}
    valid_levels = {c[0] for c in Course._meta.get_field('level').choices}

    saved_ids = []
    skipped = 0
    errors = []

    for c in courses:
        name = (c.get('name') or '').strip()
        if len(name) < 5:
            skipped += 1
            continue

        field_val = c.get('field') or 'other'
        if field_val not in valid_fields:
            field_val = 'other'

        level_val = c.get('level') or 'degree'
        if level_val not in valid_levels:
            level_val = 'degree'

        try:
            course, created = Course.objects.get_or_create(
                name=name,
                defaults={
                    'field': field_val,
                    'level': level_val,
                    'duration_years': c.get('duration_years'),
                    'fees_per_year': c.get('fees_per_year'),
                    'description': (c.get('description') or '')[:5000],
                    'career_opportunities': (c.get('career_opportunities') or '')[:2000],
                    'is_active': True,
                },
            )
            saved_ids.append(course.id)

            # Optionally create CourseOffering (one per campus if specified)
            inst_short = (c.get('institution_short_name') or '').strip()
            if inst_short:
                try:
                    inst = Institution.objects.get(short_name=inst_short)
                    deadline = c.get('application_deadline') or None
                    campus_field = (c.get('campus') or '').strip()
                    # If multiple campuses comma-separated, create one offering per campus
                    campuses = [cmp.strip() for cmp in campus_field.split(',')] if campus_field else ['']
                    for camp in campuses:
                        CourseOffering.objects.get_or_create(
                            course=course, institution=inst, campus=camp,
                            defaults={
                                'min_aps': int(c.get('min_aps') or inst.min_aps),
                                'campus': camp,
                                'programme_code': (c.get('programme_code') or '')[:20],
                                'application_deadline': deadline if deadline else None,
                                'subject_requirements': c.get('subject_requirements') or [],
                                'is_active': True,
                            },
                        )
                except Institution.DoesNotExist:
                    errors.append(f'Institution "{inst_short}" not found for {name}')
        except Exception as e:
            logger.exception(f'Save failed for {name}: {e}')
            errors.append(f'{name}: {e}')

    job.saved_course_ids = saved_ids
    job.status = 'saved'
    if errors:
        job.error_message = '\n'.join(errors[:20])
    job.save()

    messages.success(request, f'Saved {len(saved_ids)} courses ({skipped} skipped, {len(errors)} errors).')
    return redirect('importer:review', job_id=job.id)


# ════════════════════════════════════════════════════════════════
# History
# ════════════════════════════════════════════════════════════════

@staff_member_required
def history(request):
    jobs = ImportJob.objects.all()[:50]
    return render(request, 'course_importer/history.html', {'jobs': jobs})
