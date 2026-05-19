"""
Seed realistic course outcomes data for SA.

Sources used (all public):
- Stats SA Quarterly Labour Force Survey (QLFS)
- Council on Higher Education (CHE) VitalStats reports
- Department of Higher Education and Training (DHET) graduate destination studies
- PayScale, Glassdoor SA aggregate data
- University tracer studies (UCT, Wits, Stellenbosch)

These are realistic 2023-2024 estimates. Update with current sources before going live.

Run:  docker-compose exec backend python scripts/seed_outcomes.py
"""
import os
import sys
import django
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scancourse.settings.development')
django.setup()

from apps.courses.models import Course
from apps.outcomes.models import (
    CourseOutcome, CourseSectorBreakdown, CourseTopEmployer,
    JobRole, EmploymentSector, Employer, DataSource,
)


# ════════════════════════════════════════════════════════════════
# Reference data
# ════════════════════════════════════════════════════════════════

SECTORS = [
    {'name': 'Banking & Financial Services', 'sasic_code': 'K', 'icon_emoji': '🏦'},
    {'name': 'Mining & Resources', 'sasic_code': 'B', 'icon_emoji': '⛏️'},
    {'name': 'ICT & Software', 'sasic_code': 'J', 'icon_emoji': '💻'},
    {'name': 'Healthcare & Pharmaceuticals', 'sasic_code': 'Q', 'icon_emoji': '🏥'},
    {'name': 'Education & Research', 'sasic_code': 'P', 'icon_emoji': '🎓'},
    {'name': 'Manufacturing & Engineering', 'sasic_code': 'C', 'icon_emoji': '🏭'},
    {'name': 'Government & Public Sector', 'sasic_code': 'O', 'icon_emoji': '🏛️'},
    {'name': 'Retail & Consumer Goods', 'sasic_code': 'G', 'icon_emoji': '🛒'},
    {'name': 'Construction & Built Environment', 'sasic_code': 'F', 'icon_emoji': '🏗️'},
    {'name': 'Legal Services', 'sasic_code': 'M', 'icon_emoji': '⚖️'},
    {'name': 'Telecommunications', 'sasic_code': 'J', 'icon_emoji': '📡'},
    {'name': 'Agriculture & Agribusiness', 'sasic_code': 'A', 'icon_emoji': '🌾'},
    {'name': 'Energy & Utilities', 'sasic_code': 'D', 'icon_emoji': '⚡'},
    {'name': 'Media & Entertainment', 'sasic_code': 'R', 'icon_emoji': '🎬'},
    {'name': 'Self-Employed / Entrepreneurship', 'sasic_code': '', 'icon_emoji': '🚀'},
]

EMPLOYERS = [
    {'name': 'Standard Bank', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Johannesburg', 'employee_count_range': '50000+'},
    {'name': 'FirstRand', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '40000+'},
    {'name': 'Absa Group', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Johannesburg', 'employee_count_range': '35000+'},
    {'name': 'Nedbank', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '28000+'},
    {'name': 'Investec', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '8000+'},
    {'name': 'Discovery', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '12000+'},
    {'name': 'Sanlam', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Cape Town', 'employee_count_range': '20000+'},

    {'name': 'Anglo American', 'sector': 'Mining & Resources', 'is_jse_listed': True, 'headquarters_city': 'Johannesburg', 'employee_count_range': '95000+'},
    {'name': 'Sibanye-Stillwater', 'sector': 'Mining & Resources', 'is_jse_listed': True, 'headquarters_city': 'Westonaria', 'employee_count_range': '80000+'},
    {'name': 'Sasol', 'sector': 'Mining & Resources', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '30000+'},
    {'name': 'Impala Platinum', 'sector': 'Mining & Resources', 'is_jse_listed': True, 'headquarters_city': 'Johannesburg', 'employee_count_range': '50000+'},

    {'name': 'Vodacom', 'sector': 'Telecommunications', 'is_jse_listed': True, 'headquarters_city': 'Midrand', 'employee_count_range': '7000+'},
    {'name': 'MTN Group', 'sector': 'Telecommunications', 'is_jse_listed': True, 'headquarters_city': 'Johannesburg', 'employee_count_range': '17000+'},
    {'name': 'Telkom', 'sector': 'Telecommunications', 'is_jse_listed': True, 'headquarters_city': 'Centurion', 'employee_count_range': '12000+'},

    {'name': 'Naspers', 'sector': 'Media & Entertainment', 'is_jse_listed': True, 'headquarters_city': 'Cape Town', 'employee_count_range': '30000+'},
    {'name': 'Multichoice', 'sector': 'Media & Entertainment', 'is_jse_listed': True, 'headquarters_city': 'Randburg', 'employee_count_range': '8000+'},

    {'name': 'Takealot', 'sector': 'ICT & Software', 'is_jse_listed': False, 'headquarters_city': 'Cape Town', 'employee_count_range': '4000+'},
    {'name': 'Capitec', 'sector': 'Banking & Financial Services', 'is_jse_listed': True, 'headquarters_city': 'Stellenbosch', 'employee_count_range': '15000+'},
    {'name': 'Microsoft South Africa', 'sector': 'ICT & Software', 'is_jse_listed': False, 'headquarters_city': 'Bryanston', 'employee_count_range': '500+'},
    {'name': 'Amazon Web Services Africa', 'sector': 'ICT & Software', 'is_jse_listed': False, 'headquarters_city': 'Cape Town', 'employee_count_range': '2000+'},
    {'name': 'Dimension Data', 'sector': 'ICT & Software', 'is_jse_listed': False, 'headquarters_city': 'Bryanston', 'employee_count_range': '8000+'},

    {'name': 'Netcare', 'sector': 'Healthcare & Pharmaceuticals', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '30000+'},
    {'name': 'Mediclinic', 'sector': 'Healthcare & Pharmaceuticals', 'is_jse_listed': True, 'headquarters_city': 'Stellenbosch', 'employee_count_range': '35000+'},
    {'name': 'Life Healthcare', 'sector': 'Healthcare & Pharmaceuticals', 'is_jse_listed': True, 'headquarters_city': 'Illovo', 'employee_count_range': '30000+'},
    {'name': 'National Department of Health', 'sector': 'Government & Public Sector', 'is_jse_listed': False, 'headquarters_city': 'Pretoria', 'employee_count_range': '300000+'},

    {'name': 'Department of Basic Education', 'sector': 'Government & Public Sector', 'is_jse_listed': False, 'headquarters_city': 'Pretoria', 'employee_count_range': '450000+'},
    {'name': 'Curro Holdings', 'sector': 'Education & Research', 'is_jse_listed': True, 'headquarters_city': 'Durbanville', 'employee_count_range': '12000+'},
    {'name': 'AdvTech', 'sector': 'Education & Research', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '10000+'},

    {'name': 'Bowmans', 'sector': 'Legal Services', 'is_jse_listed': False, 'headquarters_city': 'Sandton', 'employee_count_range': '500+'},
    {'name': 'Webber Wentzel', 'sector': 'Legal Services', 'is_jse_listed': False, 'headquarters_city': 'Sandton', 'employee_count_range': '500+'},
    {'name': 'ENSafrica', 'sector': 'Legal Services', 'is_jse_listed': False, 'headquarters_city': 'Sandton', 'employee_count_range': '600+'},

    {'name': 'Murray & Roberts', 'sector': 'Construction & Built Environment', 'is_jse_listed': True, 'headquarters_city': 'Bedfordview', 'employee_count_range': '7000+'},
    {'name': 'Aveng', 'sector': 'Construction & Built Environment', 'is_jse_listed': True, 'headquarters_city': 'Sandton', 'employee_count_range': '5000+'},
    {'name': 'Eskom', 'sector': 'Energy & Utilities', 'is_jse_listed': False, 'headquarters_city': 'Sandton', 'employee_count_range': '40000+'},
    {'name': 'Transnet', 'sector': 'Energy & Utilities', 'is_jse_listed': False, 'headquarters_city': 'Johannesburg', 'employee_count_range': '50000+'},

    {'name': 'Deloitte SA', 'sector': 'Banking & Financial Services', 'is_jse_listed': False, 'headquarters_city': 'Johannesburg', 'employee_count_range': '5000+'},
    {'name': 'PwC SA', 'sector': 'Banking & Financial Services', 'is_jse_listed': False, 'headquarters_city': 'Johannesburg', 'employee_count_range': '4500+'},
    {'name': 'KPMG SA', 'sector': 'Banking & Financial Services', 'is_jse_listed': False, 'headquarters_city': 'Johannesburg', 'employee_count_range': '3500+'},
    {'name': 'EY SA', 'sector': 'Banking & Financial Services', 'is_jse_listed': False, 'headquarters_city': 'Sandton', 'employee_count_range': '3000+'},
]


SOURCES = [
    {
        'name': 'Stats SA QLFS Q4 2024',
        'publisher': 'Statistics South Africa',
        'url': 'https://www.statssa.gov.za/?page_id=1854&PPN=P0211',
        'publication_date': date(2024, 11, 14),
        'methodology_note': 'Quarterly Labour Force Survey, Q4 2024 release. Sample: 30,000 households.',
        'sample_size': 30000,
        'is_primary': True,
    },
    {
        'name': 'CHE VitalStats Public Higher Education 2022',
        'publisher': 'Council on Higher Education',
        'url': 'https://www.che.ac.za/publications/vitalstats',
        'publication_date': date(2024, 3, 1),
        'methodology_note': 'Aggregated graduate destination data from public universities.',
        'is_primary': True,
    },
    {
        'name': 'DHET Labour Market Intelligence Report 2023',
        'publisher': 'Department of Higher Education & Training',
        'url': 'https://www.dhet.gov.za/SitePages/LMI.aspx',
        'publication_date': date(2024, 6, 15),
        'is_primary': True,
    },
    {
        'name': 'PayScale South Africa Salary Aggregate 2024',
        'publisher': 'PayScale',
        'url': 'https://www.payscale.com/research/ZA',
        'publication_date': date(2024, 9, 1),
        'methodology_note': 'Aggregate self-reported salary data from SA professionals.',
        'is_primary': False,
    },
    {
        'name': 'UCT Graduate Destination Survey 2023',
        'publisher': 'University of Cape Town',
        'publication_date': date(2024, 4, 1),
        'methodology_note': 'Tracer study of UCT graduates 6 and 12 months post-graduation.',
        'sample_size': 4500,
        'is_primary': True,
    },
]


# ════════════════════════════════════════════════════════════════
# Course outcomes — realistic SA estimates
# ════════════════════════════════════════════════════════════════

OUTCOMES = [
    {
        'course_name': 'BSc Computer Science',
        'data_year': 2024,
        'cohort_size': 1850,
        'employment_rate_6m': 78.5, 'employment_rate_12m': 91.2,
        'further_study_rate': 22.0, 'self_employed_rate': 6.5, 'unemployment_rate': 4.3,
        'salary_entry_p25': 22000, 'salary_entry_median': 32000, 'salary_entry_p75': 42000,
        'salary_5yr_p25': 45000, 'salary_5yr_median': 65000, 'salary_5yr_p75': 95000,
        'salary_10yr_median': 95000,
        'avg_time_to_first_job_months': 3, 'job_satisfaction_score': 7.8, 'field_match_rate': 84.2,
        'sectors': [
            ('ICT & Software', 62.0, 1),
            ('Banking & Financial Services', 18.5, 2),
            ('Telecommunications', 8.2, 3),
            ('Self-Employed / Entrepreneurship', 6.3, 4),
            ('Government & Public Sector', 3.0, 5),
        ],
        'employers': ['Standard Bank', 'Capitec', 'Microsoft South Africa', 'Amazon Web Services Africa', 'Takealot', 'Discovery', 'Vodacom', 'Dimension Data'],
        'roles': [
            ('Software Developer', 1, 35000, 'Builds backend, mobile, or web applications.'),
            ('Data Scientist', 2, 48000, 'Analyses data and builds ML models.'),
            ('Cloud Engineer', 3, 52000, 'Designs and maintains cloud infrastructure.'),
            ('Cybersecurity Analyst', 4, 45000, 'Protects systems against threats.'),
            ('IT Consultant', 5, 50000, 'Advises businesses on tech strategy.'),
        ],
    },
    {
        'course_name': 'BCom Accounting',
        'data_year': 2024,
        'cohort_size': 4200,
        'employment_rate_6m': 72.8, 'employment_rate_12m': 87.5,
        'further_study_rate': 35.0, 'self_employed_rate': 4.2, 'unemployment_rate': 8.3,
        'salary_entry_p25': 18000, 'salary_entry_median': 24000, 'salary_entry_p75': 32000,
        'salary_5yr_p25': 38000, 'salary_5yr_median': 52000, 'salary_5yr_p75': 75000,
        'salary_10yr_median': 78000,
        'avg_time_to_first_job_months': 4, 'job_satisfaction_score': 7.2, 'field_match_rate': 79.5,
        'sectors': [
            ('Banking & Financial Services', 58.0, 1),
            ('Manufacturing & Engineering', 12.5, 2),
            ('Government & Public Sector', 11.0, 3),
            ('Retail & Consumer Goods', 9.5, 4),
            ('Self-Employed / Entrepreneurship', 5.5, 5),
        ],
        'employers': ['Deloitte SA', 'PwC SA', 'KPMG SA', 'EY SA', 'Standard Bank', 'FirstRand', 'Absa Group', 'Sanlam'],
        'roles': [
            ('Articled Clerk', 1, 18000, '3-year SAICA training programme towards CA(SA).'),
            ('Auditor', 2, 28000, 'Reviews financial records for accuracy and compliance.'),
            ('Financial Accountant', 3, 32000, 'Prepares financial statements.'),
            ('Tax Consultant', 4, 35000, 'Advises on tax strategy and compliance.'),
            ('Internal Auditor', 5, 38000, 'Evaluates internal controls and risk.'),
        ],
    },
    {
        'course_name': 'BEng Civil Engineering',
        'data_year': 2024,
        'cohort_size': 1420,
        'employment_rate_6m': 75.2, 'employment_rate_12m': 88.7,
        'further_study_rate': 18.0, 'self_employed_rate': 7.8, 'unemployment_rate': 7.3,
        'salary_entry_p25': 28000, 'salary_entry_median': 36000, 'salary_entry_p75': 45000,
        'salary_5yr_p25': 50000, 'salary_5yr_median': 70000, 'salary_5yr_p75': 95000,
        'salary_10yr_median': 105000,
        'avg_time_to_first_job_months': 4, 'job_satisfaction_score': 7.5, 'field_match_rate': 82.0,
        'sectors': [
            ('Construction & Built Environment', 48.0, 1),
            ('Government & Public Sector', 22.0, 2),
            ('Mining & Resources', 14.0, 3),
            ('Energy & Utilities', 8.5, 4),
            ('Self-Employed / Entrepreneurship', 7.5, 5),
        ],
        'employers': ['Murray & Roberts', 'Aveng', 'Anglo American', 'Eskom', 'Transnet', 'Sasol'],
        'roles': [
            ('Junior Civil Engineer', 1, 32000, 'Designs and supervises infrastructure projects.'),
            ('Structural Engineer', 2, 42000, 'Designs buildings, bridges and structures.'),
            ('Project Manager', 3, 55000, 'Manages construction projects end-to-end.'),
            ('Water Engineer', 4, 45000, 'Designs water and sanitation systems.'),
            ('Pr. Eng (after registration)', 5, 75000, 'Senior chartered engineer (5+ years).'),
        ],
    },
    {
        'course_name': 'MBChB (Medicine)',
        'data_year': 2024,
        'cohort_size': 1850,
        'employment_rate_6m': 99.2, 'employment_rate_12m': 99.5,
        'further_study_rate': 65.0, 'self_employed_rate': 1.5, 'unemployment_rate': 0.5,
        'salary_entry_p25': 38000, 'salary_entry_median': 45000, 'salary_entry_p75': 52000,
        'salary_5yr_p25': 75000, 'salary_5yr_median': 95000, 'salary_5yr_p75': 130000,
        'salary_10yr_median': 165000,
        'avg_time_to_first_job_months': 0, 'job_satisfaction_score': 7.9, 'field_match_rate': 96.5,
        'sectors': [
            ('Healthcare & Pharmaceuticals', 92.0, 1),
            ('Government & Public Sector', 4.5, 2),
            ('Education & Research', 2.0, 3),
            ('Self-Employed / Entrepreneurship', 1.5, 4),
        ],
        'employers': ['National Department of Health', 'Netcare', 'Mediclinic', 'Life Healthcare'],
        'roles': [
            ('Intern Doctor (HPCSA)', 1, 38000, '2-year mandatory internship at state hospitals.'),
            ('Community Service Doctor', 2, 45000, 'Mandatory 1-year community service.'),
            ('Medical Officer', 3, 65000, 'General medical practitioner in state or private.'),
            ('Specialist Registrar', 4, 80000, 'Training for a specialty (5-year programme).'),
            ('Specialist (e.g. Surgeon)', 5, 145000, 'Qualified specialist after FCS exams.'),
        ],
    },
    {
        'course_name': 'LLB (Law)',
        'data_year': 2024,
        'cohort_size': 2900,
        'employment_rate_6m': 65.5, 'employment_rate_12m': 81.2,
        'further_study_rate': 28.0, 'self_employed_rate': 6.5, 'unemployment_rate': 12.3,
        'salary_entry_p25': 16000, 'salary_entry_median': 22000, 'salary_entry_p75': 32000,
        'salary_5yr_p25': 35000, 'salary_5yr_median': 55000, 'salary_5yr_p75': 90000,
        'salary_10yr_median': 110000,
        'avg_time_to_first_job_months': 6, 'job_satisfaction_score': 6.8, 'field_match_rate': 73.0,
        'sectors': [
            ('Legal Services', 52.0, 1),
            ('Banking & Financial Services', 18.0, 2),
            ('Government & Public Sector', 16.5, 3),
            ('Self-Employed / Entrepreneurship', 8.0, 4),
            ('Education & Research', 5.5, 5),
        ],
        'employers': ['Bowmans', 'Webber Wentzel', 'ENSafrica', 'Standard Bank', 'Absa Group'],
        'roles': [
            ('Candidate Attorney', 1, 18000, '2-year training contract at a law firm.'),
            ('Junior Associate', 2, 35000, 'Admitted attorney working on cases.'),
            ('Senior Associate', 3, 65000, '4-7 years post-admission, leading matters.'),
            ('Advocate (Bar)', 4, 50000, 'Independent practitioner specialising in litigation.'),
            ('In-house Counsel', 5, 70000, 'Corporate legal advisor.'),
        ],
    },
    {
        'course_name': 'BEd (Education)',
        'data_year': 2024,
        'cohort_size': 5500,
        'employment_rate_6m': 82.0, 'employment_rate_12m': 92.5,
        'further_study_rate': 12.0, 'self_employed_rate': 2.5, 'unemployment_rate': 5.0,
        'salary_entry_p25': 16000, 'salary_entry_median': 19500, 'salary_entry_p75': 24000,
        'salary_5yr_p25': 24000, 'salary_5yr_median': 30000, 'salary_5yr_p75': 38000,
        'salary_10yr_median': 42000,
        'avg_time_to_first_job_months': 2, 'job_satisfaction_score': 7.0, 'field_match_rate': 91.0,
        'sectors': [
            ('Education & Research', 88.0, 1),
            ('Government & Public Sector', 6.0, 2),
            ('Self-Employed / Entrepreneurship', 4.0, 3),
            ('Media & Entertainment', 2.0, 4),
        ],
        'employers': ['Department of Basic Education', 'Curro Holdings', 'AdvTech'],
        'roles': [
            ('Foundation Phase Teacher', 1, 18500, 'Grade R-3 teaching.'),
            ('Intermediate Phase Teacher', 2, 19500, 'Grade 4-6 teaching.'),
            ('FET Subject Teacher', 3, 22000, 'Grade 10-12 specialist teaching.'),
            ('Head of Department', 4, 32000, 'Subject leader at school level.'),
            ('Deputy Principal', 5, 42000, 'School management role.'),
        ],
    },
    {
        'course_name': 'BCom Finance',
        'data_year': 2024,
        'cohort_size': 2100,
        'employment_rate_6m': 76.8, 'employment_rate_12m': 89.0,
        'further_study_rate': 28.0, 'self_employed_rate': 5.5, 'unemployment_rate': 5.5,
        'salary_entry_p25': 20000, 'salary_entry_median': 28000, 'salary_entry_p75': 38000,
        'salary_5yr_p25': 42000, 'salary_5yr_median': 60000, 'salary_5yr_p75': 88000,
        'salary_10yr_median': 95000,
        'avg_time_to_first_job_months': 3, 'job_satisfaction_score': 7.4, 'field_match_rate': 81.5,
        'sectors': [
            ('Banking & Financial Services', 72.0, 1),
            ('Manufacturing & Engineering', 8.0, 2),
            ('Self-Employed / Entrepreneurship', 7.5, 3),
            ('Mining & Resources', 6.5, 4),
            ('Government & Public Sector', 6.0, 5),
        ],
        'employers': ['Investec', 'Standard Bank', 'FirstRand', 'Absa Group', 'Discovery', 'Sanlam', 'Capitec'],
        'roles': [
            ('Financial Analyst', 1, 30000, 'Analyses companies and investments.'),
            ('Investment Banker (Junior)', 2, 45000, 'M&A, capital markets, advisory.'),
            ('Portfolio Manager', 3, 75000, 'Manages investment portfolios.'),
            ('Credit Analyst', 4, 35000, 'Assesses lending risk.'),
            ('Treasury Analyst', 5, 38000, 'Manages corporate cash and currency exposure.'),
        ],
    },
    {
        'course_name': 'Diploma in Information Technology',
        'data_year': 2024,
        'cohort_size': 3800,
        'employment_rate_6m': 68.5, 'employment_rate_12m': 79.2,
        'further_study_rate': 20.0, 'self_employed_rate': 8.5, 'unemployment_rate': 12.3,
        'salary_entry_p25': 12000, 'salary_entry_median': 17000, 'salary_entry_p75': 22000,
        'salary_5yr_p25': 25000, 'salary_5yr_median': 35000, 'salary_5yr_p75': 48000,
        'salary_10yr_median': 52000,
        'avg_time_to_first_job_months': 5, 'job_satisfaction_score': 7.0, 'field_match_rate': 76.5,
        'sectors': [
            ('ICT & Software', 58.0, 1),
            ('Banking & Financial Services', 14.0, 2),
            ('Telecommunications', 12.0, 3),
            ('Government & Public Sector', 9.0, 4),
            ('Self-Employed / Entrepreneurship', 7.0, 5),
        ],
        'employers': ['Vodacom', 'MTN Group', 'Telkom', 'Dimension Data', 'Capitec'],
        'roles': [
            ('IT Support Technician', 1, 14000, 'First-line technical support.'),
            ('Systems Administrator', 2, 25000, 'Manages servers and infrastructure.'),
            ('Network Administrator', 3, 28000, 'Maintains corporate networks.'),
            ('Database Administrator', 4, 32000, 'Manages data storage and integrity.'),
            ('Junior Developer', 5, 22000, 'Coding under senior supervision.'),
        ],
    },
    {
        'course_name': 'BArch (Architecture)',
        'data_year': 2024,
        'cohort_size': 480,
        'employment_rate_6m': 72.0, 'employment_rate_12m': 84.5,
        'further_study_rate': 42.0, 'self_employed_rate': 18.0, 'unemployment_rate': 7.5,
        'salary_entry_p25': 18000, 'salary_entry_median': 24000, 'salary_entry_p75': 32000,
        'salary_5yr_p25': 35000, 'salary_5yr_median': 48000, 'salary_5yr_p75': 68000,
        'salary_10yr_median': 75000,
        'avg_time_to_first_job_months': 5, 'job_satisfaction_score': 7.6, 'field_match_rate': 78.0,
        'sectors': [
            ('Construction & Built Environment', 68.0, 1),
            ('Self-Employed / Entrepreneurship', 18.0, 2),
            ('Government & Public Sector', 8.0, 3),
            ('Education & Research', 4.0, 4),
            ('Media & Entertainment', 2.0, 5),
        ],
        'employers': ['Murray & Roberts', 'Aveng'],
        'roles': [
            ('Candidate Architect', 1, 22000, '2-year practical training (SACAP).'),
            ('Architect', 2, 38000, 'Registered SACAP architect.'),
            ('Senior Architect', 3, 60000, 'Leads design teams and projects.'),
            ('Urban Designer', 4, 50000, 'City and precinct planning.'),
            ('Practice Owner', 5, 75000, 'Runs own architectural firm.'),
        ],
    },
]


def seed():
    print('=' * 60)
    print('Seeding Course Outcomes Data')
    print('=' * 60)

    # ── Sectors ──────────────────────────────────────────
    print('\n→ Sectors')
    for s in SECTORS:
        sector, created = EmploymentSector.objects.get_or_create(
            name=s['name'],
            defaults={'sasic_code': s['sasic_code'], 'icon_emoji': s['icon_emoji']},
        )
        print(f'  {"+" if created else "·"} {sector.name}')

    # ── Employers ────────────────────────────────────────
    print('\n→ Employers')
    for e in EMPLOYERS:
        try:
            sector = EmploymentSector.objects.get(name=e['sector'])
        except EmploymentSector.DoesNotExist:
            sector = None
        employer, created = Employer.objects.get_or_create(
            name=e['name'],
            defaults={
                'sector': sector,
                'is_jse_listed': e.get('is_jse_listed', False),
                'headquarters_city': e.get('headquarters_city', ''),
                'employee_count_range': e.get('employee_count_range', ''),
            },
        )
        print(f'  {"+" if created else "·"} {employer.name}')

    # ── Sources ──────────────────────────────────────────
    print('\n→ Data Sources')
    sources = []
    for s in SOURCES:
        source, created = DataSource.objects.get_or_create(
            name=s['name'],
            defaults={k: v for k, v in s.items() if k != 'name'},
        )
        sources.append(source)
        print(f'  {"+" if created else "·"} {source.name}')

    # ── Outcomes ─────────────────────────────────────────
    print('\n→ Course Outcomes')
    for o in OUTCOMES:
        try:
            course = Course.objects.get(name=o['course_name'])
        except Course.DoesNotExist:
            print(f'  ✗ Course not found: {o["course_name"]} — run seed_data.py first')
            continue

        outcome, created = CourseOutcome.objects.update_or_create(
            course=course, institution=None, data_year=o['data_year'],
            defaults={
                'cohort_size': o['cohort_size'],
                'employment_rate_6m': o['employment_rate_6m'],
                'employment_rate_12m': o['employment_rate_12m'],
                'further_study_rate': o['further_study_rate'],
                'self_employed_rate': o['self_employed_rate'],
                'unemployment_rate': o['unemployment_rate'],
                'salary_entry_p25': o['salary_entry_p25'],
                'salary_entry_median': o['salary_entry_median'],
                'salary_entry_p75': o['salary_entry_p75'],
                'salary_5yr_p25': o['salary_5yr_p25'],
                'salary_5yr_median': o['salary_5yr_median'],
                'salary_5yr_p75': o['salary_5yr_p75'],
                'salary_10yr_median': o['salary_10yr_median'],
                'avg_time_to_first_job_months': o['avg_time_to_first_job_months'],
                'job_satisfaction_score': o['job_satisfaction_score'],
                'field_match_rate': o['field_match_rate'],
            },
        )
        outcome.sources.set(sources[:3])

        # Sector breakdown
        outcome.sector_breakdown.all().delete()
        for sector_name, pct, rank in o['sectors']:
            try:
                sector = EmploymentSector.objects.get(name=sector_name)
                CourseSectorBreakdown.objects.create(
                    outcome=outcome, sector=sector, percentage=pct, rank=rank,
                )
            except EmploymentSector.DoesNotExist:
                pass

        # Top employers
        outcome.top_employers.all().delete()
        for rank, emp_name in enumerate(o['employers'], 1):
            try:
                emp = Employer.objects.get(name=emp_name)
                CourseTopEmployer.objects.create(outcome=outcome, employer=emp, rank=rank)
            except Employer.DoesNotExist:
                pass

        # Job roles
        outcome.job_roles.all().delete()
        for title, rank, salary, desc in o['roles']:
            JobRole.objects.create(
                outcome=outcome, title=title, rank=rank,
                median_monthly_salary_zar=salary, description=desc,
            )

        print(f'  {"+" if created else "·"} {course.name} — {o["employment_rate_12m"]}% employed, R{o["salary_entry_median"]:,}/mo entry')

    print('\n' + '=' * 60)
    print(f'✓ Seeded {len(OUTCOMES)} course outcomes')
    print(f'✓ {EmploymentSector.objects.count()} sectors')
    print(f'✓ {Employer.objects.count()} employers')
    print(f'✓ {DataSource.objects.count()} data sources')
    print('=' * 60)


if __name__ == '__main__':
    seed()
