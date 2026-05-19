"""
Seed real South African bursaries for the 2026 academic year.

Each entry is based on publicly-known SA bursary programmes with their
typical application windows. Application URLs are the official provider
sites. Update deadlines yearly as providers announce them.

Run:  python manage.py shell < scripts/seed_bursaries_2026.py
"""
from datetime import date
from apps.bursaries.models import Bursary

# (NB) "max_household_income" only set where the bursary publishes it.
BURSARIES_2026 = [
    {
        'name': 'NSFAS 2026 Bursary',
        'provider': 'National Student Financial Aid Scheme',
        'description': 'Government bursary covering tuition, accommodation, food, transport and learning materials for SA citizens at public universities and TVET colleges. Household income below R350 000 (R600 000 for SASSA / persons with disabilities).',
        'field': 'any', 'funding_type': 'nsfas',
        'coverage': ['tuition', 'accommodation', 'food', 'transport', 'books'],
        'province': 'ALL',
        'eligibility': 'SA citizen, household income ≤ R350 000 (≤ R600 000 if disabled / SASSA grant recipient), accepted at a public institution.',
        'max_household_income': 350000,
        'application_url': 'https://my.nsfas.org.za/',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'Funza Lushaka Bursary 2026',
        'provider': 'Department of Basic Education',
        'description': 'Full-cost bursary for students intending to teach in public schools in priority subject areas (Maths, Science, Languages, Foundation Phase, Technology).',
        'field': 'education', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, studying BEd or PGCE in a priority subject, willing to teach in a public school for the same number of years as funded.',
        'min_grade_average': 60,
        'application_url': 'https://www.funzalushaka.doe.gov.za/',
        'application_deadline': date(2026, 1, 13),
    },
    {
        'name': 'Sasol Bursary 2026',
        'provider': 'Sasol Limited',
        'description': 'Full bursary for engineering, science and commerce students. Includes vacation work and a guaranteed graduate placement upon completion.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 with 60%+ in Maths and Physical Sciences; or 1st/2nd year university with 65% average.',
        'min_grade_average': 65,
        'application_url': 'https://www.sasolbursaries.com/',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'Eskom Bursary 2026',
        'provider': 'Eskom Holdings SOC',
        'description': 'Full bursary for students in electrical, mechanical, civil, industrial, computer engineering and IT. Includes work-back obligation at Eskom after graduation.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥60% in Maths and Physical Sciences, accepted at a SA university.',
        'min_grade_average': 60,
        'application_url': 'https://www.eskom.co.za/careers/bursaries/',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'Investec Bursary 2026',
        'provider': 'Investec Bank',
        'description': 'Full-cost bursary for students studying BCom Accounting (CA stream), Finance, Actuarial Science, or related fields. Includes mentorship and graduate placement.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥70% Maths, intending to study finance/accounting/actuarial science.',
        'min_grade_average': 70,
        'application_url': 'https://www.investec.com/en_za/careers/students/bursaries-and-scholarships.html',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Standard Bank Bursary 2026',
        'provider': 'Standard Bank Group',
        'description': 'Full bursary for commerce, finance, IT, engineering and quantitative disciplines. Includes guaranteed vacation work and graduate placement.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, strong academic record, financial need, accepted at SA university.',
        'min_grade_average': 65,
        'application_url': 'https://www.standardbank.co.za/southafrica/personal/products-and-services/grow-your-money/students-and-graduates/bursaries',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Anglo American Bursary 2026',
        'provider': 'Anglo American',
        'description': 'Full bursary for mining, metallurgical, mechanical, electrical, civil and chemical engineering. Includes vacation work and graduate employment.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥65% Maths and Physical Sciences, financial need.',
        'min_grade_average': 65,
        'application_url': 'https://southafrica.angloamerican.com/our-difference/working-with-us/bursaries-and-graduates',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'Transnet Bursary 2026',
        'provider': 'Transnet SOC',
        'description': 'Full bursary for engineering and supply-chain disciplines. Includes vacation work and graduate placement at Transnet.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, studying engineering or logistics/supply chain, financial need.',
        'min_grade_average': 60,
        'application_url': 'https://www.transnet.net/Careers/Pages/bursaries.aspx',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Vodacom Discover Bursary 2026',
        'provider': 'Vodacom Group',
        'description': 'Bursary for ICT, computer science, software engineering, data science and electrical engineering. Includes mentorship and Vodacom internship.',
        'field': 'ict', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL',
        'eligibility': 'SA citizen, studying ICT, computer science or engineering at a SA institution.',
        'min_grade_average': 65,
        'application_url': 'https://www.vodacom.co.za/vodacom/careers/students',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'MTN Foundation Bursary 2026',
        'provider': 'MTN Foundation',
        'description': 'Bursary for students in ICT, engineering, business and finance. Open to students from previously disadvantaged backgrounds.',
        'field': 'ict', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, financial need, studying ICT/engineering/commerce.',
        'min_grade_average': 60,
        'application_url': 'https://www.mtn.com/sustainability/society/mtn-foundation/',
        'application_deadline': date(2026, 9, 30),
    },
    {
        'name': 'Allan Gray Orbis Foundation 2026',
        'provider': 'Allan Gray Orbis Foundation',
        'description': 'Comprehensive scholarship for entrepreneurial school-leavers (Grade 12) and 1st-year university students. Includes leadership development and lifetime fellowship.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'mentorship'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 11 or 12 / 1st-year university, demonstrated entrepreneurial spirit, strong academic record.',
        'min_grade_average': 70,
        'application_url': 'https://www.allangrayorbis.org/scholarship/',
        'application_deadline': date(2026, 4, 30),
    },
    {
        'name': 'SAICA Thuthuka Bursary 2026',
        'provider': 'South African Institute of Chartered Accountants',
        'description': 'Full-cost bursary for African and Coloured students studying BCom Accounting (CA stream). Includes mentoring, life-skills and CA(SA) qualification support.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'laptop'],
        'province': 'ALL',
        'eligibility': 'SA citizen, African or Coloured, Grade 12 ≥60% Maths, ≥70% English, accepted into BCom CA stream at a SAICA-accredited university.',
        'min_grade_average': 65,
        'max_household_income': 600000,
        'application_url': 'https://www.thuthuka.co.za/',
        'application_deadline': date(2026, 5, 31),
    },
    {
        'name': 'ABSA Bursary Programme 2026',
        'provider': 'ABSA Group',
        'description': 'Full bursary for BCom Accounting (CA stream), Finance, Actuarial Science, IT and Engineering students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥70% Maths, financial need, studying commerce/IT/engineering.',
        'min_grade_average': 70,
        'application_url': 'https://www.absa.co.za/careers/students-and-graduates/bursaries/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'FirstRand / RMB Bursary 2026',
        'provider': 'FirstRand Group',
        'description': 'Bursary for BCom Finance, Actuarial Science, Mathematical Science, Computer Science and Engineering students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, ≥75% Maths in Grade 12 / 1st-year university transcript.',
        'min_grade_average': 75,
        'application_url': 'https://www.firstrand.co.za/sustainability/transformation/bursaries/',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'Nedbank External Bursary 2026',
        'provider': 'Nedbank Group',
        'description': 'External bursary for BCom Accounting, Finance, IT and Risk Management students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, financial need, ≥65% average.',
        'min_grade_average': 65,
        'application_url': 'https://www.nedbank.co.za/content/nedbank/desktop/gt/en/aboutus/group-information/educational-trust.html',
        'application_deadline': date(2026, 9, 30),
    },
    {
        'name': 'Department of Health Bursary 2026',
        'provider': 'National Department of Health',
        'description': 'Bursary for students in health sciences (medicine, nursing, pharmacy, allied health). Includes a service obligation at a public hospital.',
        'field': 'health', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, studying health sciences, willing to work in public health system after graduation.',
        'application_url': 'https://www.health.gov.za/bursaries/',
        'application_deadline': date(2026, 10, 31),
    },
    {
        'name': 'SAB Foundation Maths & Science Bursary 2026',
        'provider': 'South African Breweries Foundation',
        'description': 'Bursary for SA students excelling in Maths and Physical Sciences pursuing STEM degrees.',
        'field': 'science', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL',
        'eligibility': 'SA citizen, ≥70% Maths and Physical Sciences in Grade 12.',
        'min_grade_average': 70,
        'application_url': 'https://www.sab.co.za/sab-foundation',
        'application_deadline': date(2026, 9, 30),
    },
    {
        'name': 'Discovery Foundation Award 2026',
        'provider': 'Discovery Health Foundation',
        'description': 'Scholarship and grant programme for students and professionals in healthcare and medical research.',
        'field': 'health', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'research', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, medical or healthcare student/professional with proven academic excellence.',
        'min_grade_average': 70,
        'application_url': 'https://www.discovery.co.za/portal/individual/foundation',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'ARM Broad-Based Trust Bursary 2026',
        'provider': 'African Rainbow Minerals',
        'description': 'Full bursary for mining engineering, metallurgy, geology and related disciplines.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen from historically disadvantaged background, studying mining/engineering disciplines.',
        'min_grade_average': 60,
        'application_url': 'https://www.arm.co.za/sustainable-development/social-development/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'BankSETA Postgraduate Bursary 2026',
        'provider': 'Banking Sector Education and Training Authority',
        'description': 'Postgraduate bursary for BCom Honours / Masters in finance, accounting, risk and economics.',
        'field': 'business', 'funding_type': 'partial',
        'coverage': ['tuition', 'books'],
        'province': 'ALL',
        'eligibility': 'SA citizen with a completed undergraduate degree in finance/commerce.',
        'application_url': 'https://www.bankseta.org.za/learners/bursaries/',
        'application_deadline': date(2026, 3, 31),
    },
    {
        'name': 'Old Mutual Education Trust Bursary 2026',
        'provider': 'Old Mutual Education Trust',
        'description': 'Bursary for children of Old Mutual employees and high-potential external students in commerce and actuarial science.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'accommodation'],
        'province': 'ALL',
        'eligibility': 'SA citizen, ≥70% Maths, financial need.',
        'min_grade_average': 70,
        'application_url': 'https://www.oldmutual.co.za/about-us/careers/bursaries-graduates',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'Telkom Bursary 2026',
        'provider': 'Telkom SA',
        'description': 'Full bursary for ICT, computer science, electrical and telecommunications engineering students.',
        'field': 'ict', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥60% Maths and Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.telkom.co.za/sites/about/careers/students-and-graduates',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'South32 Bursary 2026',
        'provider': 'South32',
        'description': 'Full bursary for mining, metallurgy, mechanical, electrical and chemical engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥65% Maths and Physical Sciences.',
        'min_grade_average': 65,
        'application_url': 'https://www.south32.net/careers/students-and-graduates',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'PricewaterhouseCoopers (PwC) Bursary 2026',
        'provider': 'PwC South Africa',
        'description': 'Full bursary for BCom Accounting (CA stream) students at SAICA-accredited universities.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥70% Maths, studying CA(SA) pathway.',
        'min_grade_average': 70,
        'application_url': 'https://www.pwc.co.za/en/careers/student-recruitment.html',
        'application_deadline': date(2026, 5, 31),
    },
    {
        'name': 'Deloitte Bursary 2026',
        'provider': 'Deloitte Africa',
        'description': 'Bursary and graduate programme for CA(SA), actuarial science and computer science students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL',
        'eligibility': 'SA citizen, ≥70% average, financial need.',
        'min_grade_average': 70,
        'application_url': 'https://www2.deloitte.com/za/en/pages/careers/articles/Bursary-Programme.html',
        'application_deadline': date(2026, 5, 31),
    },
    {
        'name': 'DST-NRF Innovation Scholarship 2026',
        'provider': 'National Research Foundation',
        'description': 'Scholarships for honours, masters and doctoral studies in priority STEM areas.',
        'field': 'science', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'research', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen / permanent resident, completed undergraduate degree, accepted into honours/masters/PhD.',
        'min_grade_average': 65,
        'application_url': 'https://www.nrf.ac.za/funding/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Murray & Roberts Engineering Bursary 2026',
        'provider': 'Murray & Roberts',
        'description': 'Full bursary for civil, mechanical, electrical and mining engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL',
        'eligibility': 'SA citizen, Grade 12 ≥65% Maths and Physical Sciences.',
        'min_grade_average': 65,
        'application_url': 'https://www.murrob.com/careers/bursaries/',
        'application_deadline': date(2026, 8, 31),
    },
]


def run():
    created = 0
    updated = 0
    for b in BURSARIES_2026:
        obj, made = Bursary.objects.get_or_create(
            name=b['name'],
            defaults={**b, 'is_active': True},
        )
        if made:
            created += 1
        else:
            # Refresh the existing record with the latest 2026 data.
            for k, v in b.items():
                setattr(obj, k, v)
            obj.is_active = True
            obj.save()
            updated += 1
    return created, updated


c, u = run()
print(f'Created: {c}    Updated: {u}    Total bursaries now: {Bursary.objects.filter(is_active=True).count()}')

# Summary
from collections import Counter
print('\nBy field:')
for field, n in Counter(
    Bursary.objects.filter(is_active=True).values_list('field', flat=True)
).most_common():
    print(f'  {field:<15} {n}')
print('\nBy funding type:')
for ft, n in Counter(
    Bursary.objects.filter(is_active=True).values_list('funding_type', flat=True)
).most_common():
    print(f'  {ft:<15} {n}')
