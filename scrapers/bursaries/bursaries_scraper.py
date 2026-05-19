"""
Bursary scraper for South African bursary opportunities.
"""
import logging
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

BURSARY_SEED_DATA = [
    {
        'name': 'NSFAS Bursary',
        'provider': 'National Student Financial Aid Scheme',
        'description': 'Government bursary for eligible students at public universities and TVET colleges in South Africa.',
        'field': 'any',
        'funding_type': 'nsfas',
        'coverage': ['tuition', 'accommodation', 'food', 'transport', 'books'],
        'province': 'ALL',
        'eligibility': 'South African citizen, household income below R350,000/year, enrolled at public institution',
        'max_household_income': 350000,
        'application_url': 'https://www.nsfas.org.za/content/apply.html',
    },
    {
        'name': 'Sasol Bursary',
        'provider': 'Sasol Limited',
        'description': 'Sasol offers bursaries to academically excellent students studying engineering and related fields.',
        'field': 'engineering',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'Studying engineering, IT or science, South African citizen, excellent academic record',
        'min_grade_average': 70,
        'application_url': 'https://www.sasol.com/careers/bursaries',
    },
    {
        'name': 'Investec Bursary',
        'provider': 'Investec Bank',
        'description': 'Investec supports talented students pursuing careers in finance, accounting and related fields.',
        'field': 'business',
        'funding_type': 'full',
        'coverage': ['tuition', 'books', 'accommodation'],
        'province': 'ALL',
        'eligibility': 'Studying finance, accounting or economics, South African citizen',
        'min_grade_average': 65,
        'application_url': 'https://www.investec.com/careers/bursary',
    },
    {
        'name': 'Department of Health Bursary',
        'provider': 'National Department of Health',
        'description': 'Bursaries for students studying health sciences to address healthcare shortages in South Africa.',
        'field': 'health',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying health sciences, committed to community service',
        'application_url': 'https://www.health.gov.za/bursaries',
    },
    {
        'name': 'Standard Bank Bursary',
        'provider': 'Standard Bank Group',
        'description': 'Standard Bank supports students in commerce, finance and IT disciplines.',
        'field': 'business',
        'funding_type': 'full',
        'coverage': ['tuition', 'books', 'accommodation', 'stipend'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying commerce, finance or IT, strong academic record',
        'min_grade_average': 65,
        'application_url': 'https://www.standardbank.co.za/standardbank/Personal/Students-and-graduates/Bursary',
    },
    {
        'name': 'Department of Basic Education Bursary',
        'provider': 'Department of Basic Education',
        'description': 'Bursary for students pursuing education degrees to become teachers.',
        'field': 'education',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying teaching/education, committed to teaching post',
        'application_url': 'https://www.education.gov.za/Bursaries.aspx',
    },
    {
        'name': 'Anglo American Bursary',
        'provider': 'Anglo American',
        'description': 'Anglo American supports South African students in mining engineering and related fields.',
        'field': 'engineering',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying mining or related engineering, strong academic results',
        'min_grade_average': 65,
        'application_url': 'https://www.angloamerican.com/careers/bursaries',
    },
    {
        'name': 'Eskom Bursary',
        'provider': 'Eskom Holdings SOC',
        'description': 'Eskom provides bursaries for students studying engineering and related technical fields.',
        'field': 'engineering',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying engineering or IT, minimum 60% average',
        'min_grade_average': 60,
        'application_url': 'https://www.eskom.co.za/careers/bursaries',
    },
    {
        'name': 'Vodacom Bursary',
        'provider': 'Vodacom Group',
        'description': 'Vodacom supports ICT students with bursaries and mentorship programmes.',
        'field': 'ict',
        'funding_type': 'full',
        'coverage': ['tuition', 'books', 'accommodation'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying ICT, computer science or engineering',
        'min_grade_average': 65,
        'application_url': 'https://www.vodacom.co.za/careers/bursary',
    },
    {
        'name': 'Transnet Bursary',
        'provider': 'Transnet SOC',
        'description': 'Transnet provides bursaries for engineering and commerce students.',
        'field': 'engineering',
        'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'South African citizen, studying engineering or commerce, financial need',
        'application_url': 'https://www.transnet.net/careers/bursaries',
    },
]


class BursariesScraper(BaseScraper):
    name = 'bursaries'

    def scrape(self) -> list[dict]:
        results = list(BURSARY_SEED_DATA)
        scraped = self._scrape_bursaries_za()
        results.extend(scraped)
        return results

    def _scrape_bursaries_za(self) -> list[dict]:
        bursaries = []
        soup = self.get('https://www.bursaries.co.za/')
        if not soup:
            return []

        listings = soup.select('.bursary-item, .listing-item, article')
        for item in listings[:20]:
            name = item.find(['h2', 'h3', 'h4'])
            if not name:
                continue
            link = item.find('a', href=True)
            deadline_text = item.get_text()
            deadline_match = re.search(r'(\d{1,2}\s+\w+\s+20\d{2})', deadline_text)

            bursaries.append({
                'name': name.get_text(strip=True),
                'provider': 'External',
                'field': 'any',
                'funding_type': 'full',
                'coverage': [],
                'province': 'ALL',
                'eligibility': '',
                'application_url': link['href'] if link else '',
            })
        return bursaries


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scraper = BursariesScraper()
    bursaries = scraper.run()
    print(f'Found {len(bursaries)} bursaries')
    for b in bursaries[:3]:
        print(f'  - {b["name"]} ({b["field"]})')
