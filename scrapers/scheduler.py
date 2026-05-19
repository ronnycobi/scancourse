"""
APScheduler-based scraper scheduler.
Runs scrapers on a schedule and pushes results to the Django API.
"""
import logging
import os
import json
import time
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from universities.sa_universities_scraper import SAUniversitiesScraper
from bursaries.bursaries_scraper import BursariesScraper

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://backend:8000/api/v1')
API_TOKEN = os.environ.get('SCRAPER_API_TOKEN', '')


def get_admin_token():
    try:
        resp = requests.post(f'{API_BASE_URL}/auth/login/', json={
            'email': os.environ.get('SCRAPER_EMAIL', 'admin@scancourse.co.za'),
            'password': os.environ.get('SCRAPER_PASSWORD', 'changeme123'),
        }, timeout=10)
        return resp.json().get('access', '')
    except Exception as e:
        logger.error(f'Failed to get admin token: {e}')
        return ''


def push_institutions(institutions: list[dict], token: str):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    for inst in institutions:
        try:
            resp = requests.post(f'{API_BASE_URL}/institutions/', json=inst, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                logger.info(f'Saved institution: {inst["name"]}')
        except Exception as e:
            logger.error(f'Failed to push institution {inst.get("name")}: {e}')
        time.sleep(0.2)


def push_bursaries(bursaries: list[dict], token: str):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    for bur in bursaries:
        try:
            resp = requests.post(f'{API_BASE_URL}/bursaries/', json=bur, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                logger.info(f'Saved bursary: {bur["name"]}')
        except Exception as e:
            logger.error(f'Failed to push bursary {bur.get("name")}: {e}')
        time.sleep(0.2)


def run_institutions_scrape():
    logger.info('=== Running institutions scrape ===')
    token = get_admin_token()
    if not token:
        logger.error('No API token — skipping institutions scrape')
        return
    scraper = SAUniversitiesScraper(API_BASE_URL, token)
    institutions = scraper.run()
    push_institutions(institutions, token)
    courses = scraper.scrape_courses()
    logger.info(f'Institutions: {len(institutions)}, Courses: {len(courses)}')


def run_bursaries_scrape():
    logger.info('=== Running bursaries scrape ===')
    token = get_admin_token()
    if not token:
        logger.error('No API token — skipping bursaries scrape')
        return
    scraper = BursariesScraper(API_BASE_URL, token)
    bursaries = scraper.run()
    push_bursaries(bursaries, token)
    logger.info(f'Bursaries: {len(bursaries)}')


def main():
    scheduler = BlockingScheduler(timezone='Africa/Johannesburg')

    # Run institutions scrape daily at 3am
    scheduler.add_job(
        run_institutions_scrape,
        CronTrigger(hour=3, minute=0),
        id='institutions_scrape',
        name='SA Institutions Scrape',
    )

    # Run bursaries scrape every 6 hours
    scheduler.add_job(
        run_bursaries_scrape,
        CronTrigger(hour='*/6'),
        id='bursaries_scrape',
        name='Bursaries Scrape',
    )

    # Run immediately on startup
    run_institutions_scrape()
    run_bursaries_scrape()

    logger.info('Scheduler started.')
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('Scheduler stopped.')


if __name__ == '__main__':
    main()
