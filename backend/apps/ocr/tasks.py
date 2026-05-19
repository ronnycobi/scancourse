import logging
from celery import shared_task
from .models import Report, Subject, APSResult
from .ocr_service import (
    extract_text,
    parse_subjects_from_text,
    extract_school_info,
    extract_subjects_directly,
)
from .aps_calculator import calculate_aps, normalize_subject, is_life_orientation

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_report(self, report_id: int):
    try:
        report = Report.objects.get(id=report_id)
    except Report.DoesNotExist:
        logger.error(f'Report {report_id} not found')
        return

    report.status = 'processing'
    report.save(update_fields=['status'])

    try:
        # Preferred: ask Gemini multimodal for structured subjects directly.
        # Falls back to OCR-then-regex if Gemini isn't configured / fails.
        structured = extract_subjects_directly(report.file.path, report.file_type)

        if structured and structured.get('subjects'):
            raw_subjects = structured['subjects']
            report.school_name = structured.get('school') or ''
            report.grade = structured.get('grade') or ''
            report.academic_year = ''
            report.raw_text = ''  # No raw OCR text in the structured path
            logger.info('Used Gemini structured extraction (%d subjects)',
                        len(raw_subjects))
        else:
            text = extract_text(report.file.path, report.file_type)
            report.raw_text = text
            school_info = extract_school_info(text)
            report.school_name = school_info.get('school_name', '')
            report.grade = school_info.get('grade', '')
            report.academic_year = school_info.get('academic_year', '')
            raw_subjects = parse_subjects_from_text(text)

        Subject.objects.filter(report=report).delete()
        for subj in raw_subjects:
            Subject.objects.create(
                report=report,
                name=subj['name'],
                normalized_name=normalize_subject(subj['name']),
                mark=subj['mark'],
                is_life_orientation=is_life_orientation(subj['name']),
            )

        aps_data = calculate_aps(raw_subjects)

        APSResult.objects.update_or_create(
            report=report,
            defaults={
                'user': report.user,
                'total_aps': aps_data['total_aps'],
                'subjects_data': aps_data['subjects'],
            }
        )

        report.status = 'completed'
        report.save(update_fields=['status', 'raw_text', 'school_name', 'grade', 'academic_year'])

        logger.info(f'Report {report_id} processed. APS: {aps_data["total_aps"]}')

    except Exception as exc:
        logger.exception(f'Failed to process report {report_id}: {exc}')
        report.status = 'failed'
        report.error_message = str(exc)
        report.save(update_fields=['status', 'error_message'])
        self.retry(exc=exc)
