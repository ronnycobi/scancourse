"""
Management command to seed initial SA data into the database.
Run: python manage.py shell < scripts/seed_data.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scancourse.settings.development')
django.setup()

from apps.institutions.models import Institution
from apps.courses.models import Course, CourseOffering
from apps.bursaries.models import Bursary

SA_INSTITUTIONS = [
    {'name': 'University of Cape Town', 'short_name': 'UCT', 'institution_type': 'university', 'province': 'WC', 'city': 'Cape Town', 'website': 'https://www.uct.ac.za', 'application_url': 'https://www.uct.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 30},
    {'name': 'University of the Witwatersrand', 'short_name': 'Wits', 'institution_type': 'university', 'province': 'GP', 'city': 'Johannesburg', 'website': 'https://www.wits.ac.za', 'application_url': 'https://www.wits.ac.za/application', 'nsfas_accredited': True, 'min_aps': 28},
    {'name': 'University of Pretoria', 'short_name': 'UP', 'institution_type': 'university', 'province': 'GP', 'city': 'Pretoria', 'website': 'https://www.up.ac.za', 'application_url': 'https://www.up.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 26},
    {'name': 'Stellenbosch University', 'short_name': 'SU', 'institution_type': 'university', 'province': 'WC', 'city': 'Stellenbosch', 'website': 'https://www.sun.ac.za', 'application_url': 'https://www.sun.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 28},
    {'name': 'University of KwaZulu-Natal', 'short_name': 'UKZN', 'institution_type': 'university', 'province': 'KZN', 'city': 'Durban', 'website': 'https://www.ukzn.ac.za', 'application_url': 'https://www.ukzn.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 24},
    {'name': 'University of Johannesburg', 'short_name': 'UJ', 'institution_type': 'university', 'province': 'GP', 'city': 'Johannesburg', 'website': 'https://www.uj.ac.za', 'application_url': 'https://www.uj.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 22},
    {'name': 'Nelson Mandela University', 'short_name': 'NMU', 'institution_type': 'university', 'province': 'EC', 'city': 'Gqeberha', 'website': 'https://www.mandela.ac.za', 'application_url': 'https://www.mandela.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 22},
    {'name': 'Tshwane University of Technology', 'short_name': 'TUT', 'institution_type': 'university_of_technology', 'province': 'GP', 'city': 'Pretoria', 'website': 'https://www.tut.ac.za', 'application_url': 'https://www.tut.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 18},
    {'name': 'Cape Peninsula University of Technology', 'short_name': 'CPUT', 'institution_type': 'university_of_technology', 'province': 'WC', 'city': 'Cape Town', 'website': 'https://www.cput.ac.za', 'application_url': 'https://www.cput.ac.za/apply', 'nsfas_accredited': True, 'min_aps': 18},
]

SA_COURSES = [
    {'name': 'BSc Computer Science', 'field': 'ict', 'level': 'degree', 'duration_years': 3, 'career_opportunities': 'Software Developer, Data Scientist, IT Manager', 'salary_min': 25000, 'salary_max': 80000},
    {'name': 'BCom Accounting', 'field': 'business', 'level': 'degree', 'duration_years': 3, 'career_opportunities': 'Accountant, Auditor, Financial Manager', 'salary_min': 22000, 'salary_max': 70000},
    {'name': 'BEng Civil Engineering', 'field': 'engineering', 'level': 'degree', 'duration_years': 4, 'career_opportunities': 'Civil Engineer, Project Manager, Structural Engineer', 'salary_min': 30000, 'salary_max': 90000},
    {'name': 'MBChB (Medicine)', 'field': 'health', 'level': 'degree', 'duration_years': 6, 'career_opportunities': 'Medical Doctor, Specialist, General Practitioner', 'salary_min': 50000, 'salary_max': 150000},
    {'name': 'LLB (Law)', 'field': 'law', 'level': 'degree', 'duration_years': 4, 'career_opportunities': 'Advocate, Attorney, Corporate Counsel', 'salary_min': 25000, 'salary_max': 100000},
    {'name': 'BEd (Education)', 'field': 'education', 'level': 'degree', 'duration_years': 4, 'career_opportunities': 'Teacher, Education Manager, Curriculum Developer', 'salary_min': 18000, 'salary_max': 45000},
    {'name': 'Diploma in Information Technology', 'field': 'ict', 'level': 'diploma', 'duration_years': 3, 'career_opportunities': 'IT Support, Network Technician, Database Admin', 'salary_min': 15000, 'salary_max': 40000},
    {'name': 'BCom Finance', 'field': 'business', 'level': 'degree', 'duration_years': 3, 'career_opportunities': 'Financial Analyst, Investment Banker, Portfolio Manager', 'salary_min': 24000, 'salary_max': 80000},
    {'name': 'BArch (Architecture)', 'field': 'built_environment', 'level': 'degree', 'duration_years': 5, 'career_opportunities': 'Architect, Urban Designer, Project Manager', 'salary_min': 28000, 'salary_max': 75000},
]

COURSE_OFFERINGS = [
    ('BSc Computer Science', 'UCT', 32, '30 September 2025'),
    ('BSc Computer Science', 'Wits', 30, '31 August 2025'),
    ('BSc Computer Science', 'UP', 28, '30 June 2025'),
    ('BCom Accounting', 'UCT', 30, '30 September 2025'),
    ('BCom Accounting', 'Wits', 28, '31 August 2025'),
    ('BEng Civil Engineering', 'UCT', 34, '30 September 2025'),
    ('BEng Civil Engineering', 'UP', 30, '30 June 2025'),
    ('MBChB (Medicine)', 'UCT', 40, '30 July 2025'),
    ('MBChB (Medicine)', 'UKZN', 36, '30 June 2025'),
    ('LLB (Law)', 'UCT', 36, '30 September 2025'),
    ('LLB (Law)', 'Wits', 34, '31 August 2025'),
    ('BEd (Education)', 'UP', 24, '30 June 2025'),
    ('Diploma in Information Technology', 'TUT', 18, '30 April 2025'),
    ('Diploma in Information Technology', 'CPUT', 18, '30 April 2025'),
    ('BCom Finance', 'UP', 28, '30 June 2025'),
]


def seed():
    print('Seeding institutions...')
    for data in SA_INSTITUTIONS:
        inst, created = Institution.objects.get_or_create(name=data['name'], defaults=data)
        if created:
            print(f'  Created: {inst.name}')

    print('Seeding courses...')
    for data in SA_COURSES:
        course, created = Course.objects.get_or_create(name=data['name'], defaults=data)
        if created:
            print(f'  Created: {course.name}')

    print('Seeding course offerings...')
    for course_name, inst_name, min_aps, deadline in COURSE_OFFERINGS:
        try:
            from datetime import datetime
            try:
                deadline_date = datetime.strptime(deadline, '%d %B %Y').date()
            except ValueError:
                deadline_date = None
            course = Course.objects.get(name=course_name)
            inst = Institution.objects.get(short_name=inst_name)
            offering, created = CourseOffering.objects.get_or_create(
                course=course, institution=inst,
                defaults={'min_aps': min_aps, 'application_deadline': deadline_date}
            )
            if created:
                print(f'  Offering: {course_name} @ {inst_name} (APS {min_aps})')
        except (Course.DoesNotExist, Institution.DoesNotExist) as e:
            print(f'  Skip: {e}')

    print('\nSeeding complete!')


if __name__ == '__main__':
    seed()
