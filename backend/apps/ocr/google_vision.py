"""
Google Cloud Vision OCR — far more accurate on real report cards than
Tesseract. Activated automatically when GOOGLE_CLOUD_API_KEY is set in
the environment (or .env file).

Two integration paths:
  1. REST API with an API key  (simplest — set GOOGLE_CLOUD_API_KEY)
  2. Service-account JSON      (set GOOGLE_APPLICATION_CREDENTIALS path)

We try #1 first because that's what the user provides; #2 is automatic
if google-cloud-vision SDK is installed and credentials are available.
"""
from __future__ import annotations

import base64
import logging
from pathlib import Path

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VISION_API_URL = 'https://vision.googleapis.com/v1/images:annotate'
MAX_BYTES = 20 * 1024 * 1024  # Vision API caps at 20 MB per image


def is_available() -> bool:
    """Vision OCR is configured iff a key or service-account is present."""
    return bool(
        getattr(settings, 'GOOGLE_CLOUD_API_KEY', '')
        or getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', '')
    )


def extract_text_via_rest(image_path: str) -> str:
    """Call the Vision REST endpoint with an API key. Returns plain text."""
    api_key = settings.GOOGLE_CLOUD_API_KEY
    if not api_key:
        raise RuntimeError('GOOGLE_CLOUD_API_KEY is not set.')

    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(image_path)
    if path.stat().st_size > MAX_BYTES:
        raise ValueError(f'Image exceeds {MAX_BYTES // 1024 // 1024} MB limit.')

    with open(path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('ascii')

    body = {
        'requests': [{
            'image': {'content': content_b64},
            'features': [{'type': 'DOCUMENT_TEXT_DETECTION', 'maxResults': 1}],
            'imageContext': {'languageHints': ['en']},
        }],
    }
    resp = requests.post(
        f'{VISION_API_URL}?key={api_key}',
        json=body,
        timeout=30,
        headers={'Content-Type': 'application/json'},
    )
    resp.raise_for_status()
    data = resp.json()

    if 'error' in data:
        raise RuntimeError(f"Vision API error: {data['error']}")

    annotations = data.get('responses', [{}])[0]
    if 'error' in annotations:
        raise RuntimeError(f"Vision per-image error: {annotations['error']}")

    full_text = annotations.get('fullTextAnnotation', {}).get('text')
    if full_text:
        return full_text

    # Fallback to the older textAnnotations array
    text_annotations = annotations.get('textAnnotations') or []
    if text_annotations:
        return text_annotations[0].get('description', '')

    return ''


def extract_text_via_sdk(image_path: str) -> str:
    """Use the google-cloud-vision SDK when GOOGLE_APPLICATION_CREDENTIALS is set."""
    from google.cloud import vision  # lazy import

    client = vision.ImageAnnotatorClient()
    with open(image_path, 'rb') as f:
        image = vision.Image(content=f.read())
    response = client.document_text_detection(image=image)
    if response.error.message:
        raise RuntimeError(f'Vision SDK error: {response.error.message}')
    return response.full_text_annotation.text or ''


def extract_text(image_path: str) -> str:
    """Main entry point — tries REST first (uses API key), then SDK."""
    if getattr(settings, 'GOOGLE_CLOUD_API_KEY', ''):
        logger.info('Using Google Vision REST API for OCR (%s)', image_path)
        return extract_text_via_rest(image_path)
    logger.info('Using Google Vision SDK for OCR (%s)', image_path)
    return extract_text_via_sdk(image_path)
