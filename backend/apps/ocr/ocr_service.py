"""
OCR extraction service using Tesseract and OpenCV preprocessing.
"""
import re
import os
import logging
import tempfile
from pathlib import Path

# Lazy imports — heavy OCR deps only loaded when actually OCRing
# (Allows the rest of the OCR app — manual entry, APS calculation — to work
#  without Tesseract/OpenCV installed.)
def _lazy_imports():
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    return cv2, np, pytesseract, Image, convert_from_path

logger = logging.getLogger(__name__)

SUBJECT_PATTERN = re.compile(
    r'([A-Za-z\s/\-&]+?)\s+(\d{1,3})\s*%?',
    re.IGNORECASE
)

MARK_BOUNDS = (0, 100)
MIN_SUBJECT_NAME_LEN = 3

KNOWN_NON_SUBJECTS = {
    'total', 'average', 'aggregate', 'result', 'grade', 'class',
    'promoted', 'failed', 'date', 'term', 'quarter', 'year',
    'name', 'surname', 'school', 'student', 'learner',
}


def preprocess_image(image, cv2, np):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    scaled = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    return scaled


def extract_text_from_image(image_path: str) -> str:
    cv2, np, pytesseract, Image, _ = _lazy_imports()
    img = cv2.imread(image_path)
    if img is None:
        pil_img = Image.open(image_path)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    processed = preprocess_image(img, cv2, np)
    config = '--oem 3 --psm 6'
    text = pytesseract.image_to_string(processed, config=config)
    return text


def extract_text_from_pdf(pdf_path: str) -> str:
    cv2, np, pytesseract, _, convert_from_path = _lazy_imports()
    with tempfile.TemporaryDirectory() as tmp_dir:
        pages = convert_from_path(pdf_path, dpi=300, output_folder=tmp_dir)
        texts = []
        for page in pages:
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            processed = preprocess_image(img, cv2, np)
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed, config=config)
            texts.append(text)
        return '\n'.join(texts)


def extract_text(file_path: str, file_type: str) -> str:
    """Extract raw text from a report-card image or PDF.

    Priority chain (best → fallback):
        1. Google Cloud Vision  — only if GOOGLE_CLOUD_API_KEY is set
        2. Gemini Vision        — if GEMINI_API_KEY is set (multimodal)
        3. Local Tesseract      — always available, last resort
    """
    ext = Path(file_path).suffix.lower()
    is_pdf = file_type == 'pdf' or ext == '.pdf'

    # 1. Google Cloud Vision (image only — PDF path uses Tesseract).
    try:
        from . import google_vision
        if google_vision.is_available() and not is_pdf:
            return google_vision.extract_text(file_path)
    except Exception as e:
        logger.warning('Google Vision OCR failed (%s); trying Gemini.', e)

    # 2. Gemini Vision (image only).
    try:
        from . import gemini_vision
        if gemini_vision.is_available() and not is_pdf:
            return gemini_vision.extract_text(file_path)
    except Exception as e:
        logger.warning('Gemini Vision OCR failed (%s); falling back to Tesseract.', e)

    # 3. Tesseract last-resort.
    if is_pdf:
        return extract_text_from_pdf(file_path)
    return extract_text_from_image(file_path)


def extract_subjects_directly(file_path: str, file_type: str) -> dict | None:
    """
    Use Gemini multimodal to extract structured subject+mark data in one
    pass. Returns None if Gemini isn't configured or the response wasn't
    valid JSON — callers should fall back to extract_text() + parse.
    """
    ext = Path(file_path).suffix.lower()
    if file_type == 'pdf' or ext == '.pdf':
        return None  # Image-only for now
    try:
        from . import gemini_vision
        if gemini_vision.is_available():
            return gemini_vision.extract_subjects(file_path)
    except Exception as e:
        logger.warning('Gemini structured extraction failed: %s', e)
    return None


def parse_subjects_from_text(text: str) -> list[dict]:
    subjects = []
    seen_names = set()

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        matches = SUBJECT_PATTERN.findall(line)
        for name_raw, mark_str in matches:
            name = name_raw.strip().rstrip(':').strip()
            if len(name) < MIN_SUBJECT_NAME_LEN:
                continue
            if name.lower() in KNOWN_NON_SUBJECTS:
                continue

            try:
                mark = int(mark_str)
            except ValueError:
                continue

            if not (MARK_BOUNDS[0] <= mark <= MARK_BOUNDS[1]):
                continue

            name_key = name.lower()
            if name_key in seen_names:
                continue

            seen_names.add(name_key)
            subjects.append({'name': name, 'mark': mark})

    return subjects


def extract_school_info(text: str) -> dict:
    info = {}
    lines = text.split('\n')[:15]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if any(kw in line.lower() for kw in ['school', 'high', 'academy', 'college']):
            info['school_name'] = line[:200]
        if re.search(r'(grade\s*1[0-2])', line, re.IGNORECASE):
            match = re.search(r'(grade\s*1[0-2])', line, re.IGNORECASE)
            if match:
                info['grade'] = match.group(1).title()
        if re.search(r'20\d{2}', line):
            match = re.search(r'20\d{2}', line)
            if match:
                info['academic_year'] = match.group(0)

    return info
