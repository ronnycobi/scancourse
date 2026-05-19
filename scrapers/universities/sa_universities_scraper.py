"""
Scraper for South African universities, courses, and application info.
Targets SAQA-registered institutions.
"""
import logging
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


# Seed data for SA institutions (scrapers augment this with live data)
SA_INSTITUTIONS_SEED = [
    {
        'name': 'University of Cape Town',
        'short_name': 'UCT',
        'institution_type': 'university',
        'province': 'WC',
        'city': 'Cape Town',
        'website': 'https://www.uct.ac.za',
        'application_url': 'https://www.uct.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 30,
    },
    {
        'name': 'University of the Witwatersrand',
        'short_name': 'Wits',
        'institution_type': 'university',
        'province': 'GP',
        'city': 'Johannesburg',
        'website': 'https://www.wits.ac.za',
        'application_url': 'https://www.wits.ac.za/application',
        'nsfas_accredited': True,
        'min_aps': 28,
    },
    {
        'name': 'University of Pretoria',
        'short_name': 'UP',
        'institution_type': 'university',
        'province': 'GP',
        'city': 'Pretoria',
        'website': 'https://www.up.ac.za',
        'application_url': 'https://www.up.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 26,
    },
    {
        'name': 'Stellenbosch University',
        'short_name': 'SU',
        'institution_type': 'university',
        'province': 'WC',
        'city': 'Stellenbosch',
        'website': 'https://www.sun.ac.za',
        'application_url': 'https://www.sun.ac.za/english/apply',
        'nsfas_accredited': True,
        'min_aps': 28,
    },
    {
        'name': 'University of KwaZulu-Natal',
        'short_name': 'UKZN',
        'institution_type': 'university',
        'province': 'KZN',
        'city': 'Durban',
        'website': 'https://www.ukzn.ac.za',
        'application_url': 'https://www.ukzn.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 24,
    },
    {
        'name': 'University of Johannesburg',
        'short_name': 'UJ',
        'institution_type': 'university',
        'province': 'GP',
        'city': 'Johannesburg',
        'website': 'https://www.uj.ac.za',
        'application_url': 'https://www.uj.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 22,
    },
    {
        'name': 'Nelson Mandela University',
        'short_name': 'NMU',
        'institution_type': 'university',
        'province': 'EC',
        'city': 'Port Elizabeth',
        'website': 'https://www.mandela.ac.za',
        'application_url': 'https://www.mandela.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 22,
    },
    {
        'name': 'Rhodes University',
        'short_name': 'RU',
        'institution_type': 'university',
        'province': 'EC',
        'city': 'Makhanda',
        'website': 'https://www.ru.ac.za',
        'application_url': 'https://www.ru.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 26,
    },
    {
        'name': 'University of the Free State',
        'short_name': 'UFS',
        'institution_type': 'university',
        'province': 'FS',
        'city': 'Bloemfontein',
        'website': 'https://www.ufs.ac.za',
        'application_url': 'https://www.ufs.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 22,
    },
    {
        'name': 'North-West University',
        'short_name': 'NWU',
        'institution_type': 'university',
        'province': 'NW',
        'city': 'Potchefstroom',
        'website': 'https://www.nwu.ac.za',
        'application_url': 'https://www.nwu.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 22,
    },
    {
        'name': 'Tshwane University of Technology',
        'short_name': 'TUT',
        'institution_type': 'university_of_technology',
        'province': 'GP',
        'city': 'Pretoria',
        'website': 'https://www.tut.ac.za',
        'application_url': 'https://www.tut.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 18,
    },
    {
        'name': 'Cape Peninsula University of Technology',
        'short_name': 'CPUT',
        'institution_type': 'university_of_technology',
        'province': 'WC',
        'city': 'Cape Town',
        'website': 'https://www.cput.ac.za',
        'application_url': 'https://www.cput.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 18,
    },
    {
        'name': 'Durban University of Technology',
        'short_name': 'DUT',
        'institution_type': 'university_of_technology',
        'province': 'KZN',
        'city': 'Durban',
        'website': 'https://www.dut.ac.za',
        'application_url': 'https://www.dut.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 18,
    },
    {
        'name': 'Vaal University of Technology',
        'short_name': 'VUT',
        'institution_type': 'university_of_technology',
        'province': 'GP',
        'city': 'Vanderbijlpark',
        'website': 'https://www.vut.ac.za',
        'application_url': 'https://www.vut.ac.za/apply',
        'nsfas_accredited': True,
        'min_aps': 16,
    },
]

SA_COURSES_SEED = [
    {
        'name': 'Bachelor of Science in Computer Science',
        'field': 'ict',
        'level': 'degree',
        'duration_years': 3,
        'career_opportunities': 'Software Developer, Data Scientist, IT Manager, Systems Analyst',
        'salary_min': 25000,
        'salary_max': 80000,
    },
    {
        'name': 'Bachelor of Commerce in Accounting',
        'field': 'business',
        'level': 'degree',
        'duration_years': 3,
        'career_opportunities': 'Accountant, Auditor, Financial Manager, Tax Consultant',
        'salary_min': 22000,
        'salary_max': 70000,
    },
    {
        'name': 'Bachelor of Engineering in Civil Engineering',
        'field': 'engineering',
        'level': 'degree',
        'duration_years': 4,
        'career_opportunities': 'Civil Engineer, Structural Engineer, Project Manager, Town Planner',
        'salary_min': 30000,
        'salary_max': 90000,
    },
    {
        'name': 'Bachelor of Medicine and Bachelor of Surgery (MBChB)',
        'field': 'health',
        'level': 'degree',
        'duration_years': 6,
        'career_opportunities': 'Medical Doctor, Specialist, Surgeon, General Practitioner',
        'salary_min': 50000,
        'salary_max': 150000,
    },
    {
        'name': 'Bachelor of Laws (LLB)',
        'field': 'law',
        'level': 'degree',
        'duration_years': 4,
        'career_opportunities': 'Advocate, Attorney, Corporate Counsel, Magistrate',
        'salary_min': 25000,
        'salary_max': 100000,
    },
    {
        'name': 'Bachelor of Education',
        'field': 'education',
        'level': 'degree',
        'duration_years': 4,
        'career_opportunities': 'Teacher, Education Manager, Curriculum Developer, Tutor',
        'salary_min': 18000,
        'salary_max': 45000,
    },
    {
        'name': 'Diploma in Information Technology',
        'field': 'ict',
        'level': 'diploma',
        'duration_years': 3,
        'career_opportunities': 'IT Support, Network Technician, Database Administrator',
        'salary_min': 15000,
        'salary_max': 40000,
    },
    {
        'name': 'Diploma in Nursing',
        'field': 'health',
        'level': 'diploma',
        'duration_years': 4,
        'career_opportunities': 'Registered Nurse, Ward Manager, Community Health Nurse',
        'salary_min': 16000,
        'salary_max': 42000,
    },
    {
        'name': 'Bachelor of Commerce in Finance',
        'field': 'business',
        'level': 'degree',
        'duration_years': 3,
        'career_opportunities': 'Financial Analyst, Investment Banker, Portfolio Manager',
        'salary_min': 24000,
        'salary_max': 80000,
    },
    {
        'name': 'Bachelor of Architecture',
        'field': 'built_environment',
        'level': 'degree',
        'duration_years': 5,
        'career_opportunities': 'Architect, Urban Designer, Interior Designer, Project Manager',
        'salary_min': 28000,
        'salary_max': 75000,
    },
]


class SAUniversitiesScraper(BaseScraper):
    name = 'sa_universities'

    def scrape(self) -> list[dict]:
        return SA_INSTITUTIONS_SEED

    def scrape_courses(self) -> list[dict]:
        return SA_COURSES_SEED

    def scrape_uct_courses(self):
        """Attempt to scrape UCT course listings."""
        soup = self.get('https://www.uct.ac.za/apply/requirements')
        if not soup:
            return []
        courses = []
        # Parse course requirements table if structure matches
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    name = cols[0].get_text(strip=True)
                    aps_text = cols[1].get_text(strip=True)
                    aps_match = re.search(r'\d+', aps_text)
                    if name and aps_match:
                        courses.append({
                            'name': name,
                            'institution': 'UCT',
                            'min_aps': int(aps_match.group()),
                        })
        return courses


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scraper = SAUniversitiesScraper()
    institutions = scraper.run()
    print(f'Institutions: {len(institutions)}')
    courses = scraper.scrape_courses()
    print(f'Courses: {len(courses)}')
