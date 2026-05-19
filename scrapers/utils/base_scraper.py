"""
Base scraper with retry, rate limiting, and session management.
"""
import time
import logging
import random
from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-ZA,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


class BaseScraper(ABC):
    name: str = 'base'
    base_url: str = ''
    rate_limit_seconds: float = 2.0

    def __init__(self, api_base_url: str = 'http://localhost:8000/api/v1', api_token: str = ''):
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.api_base_url = api_base_url
        self.api_token = api_token
        self._last_request = 0

    def get(self, url: str, **kwargs) -> BeautifulSoup | None:
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - elapsed + random.uniform(0.1, 0.5))

        for attempt in range(3):
            try:
                resp = self.session.get(url, timeout=30, **kwargs)
                resp.raise_for_status()
                self._last_request = time.time()
                return BeautifulSoup(resp.text, 'lxml')
            except Exception as e:
                logger.warning(f'[{self.name}] GET {url} failed (attempt {attempt+1}): {e}')
                time.sleep(2 ** attempt)
        return None

    def post_to_api(self, endpoint: str, data: dict) -> dict | None:
        headers = {'Authorization': f'Bearer {self.api_token}', 'Content-Type': 'application/json'}
        try:
            resp = requests.post(f'{self.api_base_url}{endpoint}', json=data, headers=headers, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f'[{self.name}] API POST {endpoint} failed: {e}')
            return None

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def run(self):
        logger.info(f'[{self.name}] Starting scrape...')
        results = self.scrape()
        logger.info(f'[{self.name}] Scraped {len(results)} items.')
        return results
