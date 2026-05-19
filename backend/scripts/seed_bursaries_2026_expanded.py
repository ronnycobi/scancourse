"""
Expansion pack: ~50 additional SA bursaries for the 2026 academic year.
Run AFTER seed_bursaries_2026.py.

These are real publicly-advertised programmes. Deadlines are typical
windows — always reconfirm on the provider's site before applying.

Run:  python manage.py shell < scripts/seed_bursaries_2026_expanded.py
"""
from datetime import date
from apps.bursaries.models import Bursary

MORE_BURSARIES_2026 = [
    # ── Mining (beyond the big three) ──────────────────────────────────────
    {
        'name': 'Sibanye-Stillwater Bursary 2026', 'provider': 'Sibanye-Stillwater',
        'description': 'Full bursary for mining, metallurgical, mechanical, electrical and chemical engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, Grade 12 ≥65% Maths and Physical Sciences.',
        'min_grade_average': 65,
        'application_url': 'https://www.sibanyestillwater.com/sustainability/society/bursaries/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Gold Fields Bursary 2026', 'provider': 'Gold Fields',
        'description': 'Bursary for engineering and geosciences students. Vacation work and graduate employment included.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL', 'eligibility': 'SA citizen, financial need, ≥60% Maths/Science.',
        'min_grade_average': 60,
        'application_url': 'https://www.goldfields.com/bursaries.php',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'AngloGold Ashanti Bursary 2026', 'provider': 'AngloGold Ashanti',
        'description': 'Bursary for mining, metallurgy, mechanical and electrical engineering, geology and surveying.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, financial need, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.anglogoldashanti.com/sustainability/people/communities/',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'Implats Bursary 2026', 'provider': 'Impala Platinum (Implats)',
        'description': 'Bursary for engineering, metallurgy, mining and geology students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen from a community near Implats operations preferred.',
        'min_grade_average': 60,
        'application_url': 'https://www.implats.co.za/bursaries.php',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Exxaro Resources Bursary 2026', 'provider': 'Exxaro Resources',
        'description': 'Full bursary for engineering, metallurgy and mining-related studies.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% Maths and Physical Sciences.',
        'min_grade_average': 65,
        'application_url': 'https://www.exxaro.com/careers/bursaries-and-internships/',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'Harmony Gold Bursary 2026', 'provider': 'Harmony Gold Mining',
        'description': 'Bursary for engineering, geology and mining-related disciplines.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Science.',
        'min_grade_average': 60,
        'application_url': 'https://www.harmony.co.za/sustainability/social/bursary-programme/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Northam Platinum Bursary 2026', 'provider': 'Northam Platinum',
        'description': 'Bursary for engineering, metallurgy and mining students from communities near Northam.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'LP', 'eligibility': 'SA citizen, preferably Limpopo / North West.',
        'min_grade_average': 60,
        'application_url': 'https://www.northam.co.za/sustainability/social-investment',
        'application_deadline': date(2026, 8, 31),
    },

    # ── Industrial / pulp & paper / chemicals ──────────────────────────────
    {
        'name': 'Sappi Bursary 2026', 'provider': 'Sappi Southern Africa',
        'description': 'Bursary for engineering (chemical, mechanical, electrical, industrial), forestry and pulp-and-paper students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'vacation_work'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths and Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.sappi.com/sappi-bursary-scheme-south-africa',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Mondi Bursary 2026', 'provider': 'Mondi Group',
        'description': 'Bursary for chemical, mechanical, electrical and industrial engineering, pulp and paper technology.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.mondigroup.com/en/careers/students-and-graduates/',
        'application_deadline': date(2026, 8, 31),
    },

    # ── Financial services ────────────────────────────────────────────────
    {
        'name': 'Sanlam Bursary 2026', 'provider': 'Sanlam',
        'description': 'Bursary for BCom Actuarial Science, Finance, Accounting and Quantitative Risk Management.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥75% Maths in Grade 12.',
        'min_grade_average': 75,
        'application_url': 'https://www.sanlam.co.za/careers/students-and-graduates',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Liberty Group Bursary 2026', 'provider': 'Liberty Group',
        'description': 'Bursary for BCom Actuarial Science, Finance and IT-related degrees.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥70% Maths, financial need.',
        'min_grade_average': 70,
        'application_url': 'https://www.liberty.co.za/about-us/careers',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Momentum Metropolitan Bursary 2026', 'provider': 'Momentum Metropolitan',
        'description': 'Bursary for actuarial science, finance, IT and data science students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥70% Maths.',
        'min_grade_average': 70,
        'application_url': 'https://www.momentummetropolitan.co.za/en/about-us/careers',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'Capitec Bank Bursary 2026', 'provider': 'Capitec Bank',
        'description': 'Bursary for BCom, IT, computer science and data science students.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% average, financial need.',
        'min_grade_average': 65,
        'application_url': 'https://www.capitecbank.co.za/about-us/careers/bursaries/',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'KPMG Bursary 2026', 'provider': 'KPMG South Africa',
        'description': 'Full bursary for CA(SA) stream students at SAICA-accredited universities.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, Grade 12 ≥70% Maths, on CA pathway.',
        'min_grade_average': 70,
        'application_url': 'https://kpmg.com/za/en/home/careers/students.html',
        'application_deadline': date(2026, 5, 31),
    },
    {
        'name': 'EY (Ernst & Young) Bursary 2026', 'provider': 'EY South Africa',
        'description': 'Bursary for chartered accountancy (CA) stream and consulting graduate programme.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥70% Maths, on CA pathway.',
        'min_grade_average': 70,
        'application_url': 'https://www.ey.com/en_za/careers/students',
        'application_deadline': date(2026, 5, 31),
    },
    {
        'name': 'BDO South Africa Bursary 2026', 'provider': 'BDO South Africa',
        'description': 'Bursary for BCom Accounting students on the CA(SA) pathway.',
        'field': 'business', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% Maths.',
        'min_grade_average': 65,
        'application_url': 'https://www.bdo.co.za/en-za/careers/students-and-graduates',
        'application_deadline': date(2026, 6, 30),
    },

    # ── Engineering consultancies ─────────────────────────────────────────
    {
        'name': 'AECOM Bursary 2026', 'provider': 'AECOM',
        'description': 'Bursary for civil, structural, mechanical, electrical and environmental engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'vacation_work'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://aecom.com/za/about/careers/students/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'WSP Bursary 2026', 'provider': 'WSP in Africa',
        'description': 'Bursary for civil, structural, mechanical, electrical and environmental engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'vacation_work'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.wsp.com/en-za/careers',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'GIBB Bursary 2026', 'provider': 'GIBB Engineering and Architecture',
        'description': 'Bursary for civil, structural, transportation, mechanical and electrical engineering students.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'vacation_work'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.gibb.co.za/careers',
        'application_deadline': date(2026, 8, 31),
    },
    {
        'name': 'Aurecon Bursary 2026', 'provider': 'Aurecon',
        'description': 'Bursary for engineering students across civil, mechanical, electrical and environmental disciplines.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥60% Maths/Physical Sciences.',
        'min_grade_average': 60,
        'application_url': 'https://www.aurecongroup.com/careers/early-careers',
        'application_deadline': date(2026, 8, 31),
    },

    # ── Tech / ICT ────────────────────────────────────────────────────────
    {
        'name': 'Microsoft 4Afrika Scholarship 2026', 'provider': 'Microsoft Africa',
        'description': 'Scholarship for African students in STEM disciplines, focused on computer science, data science and AI.',
        'field': 'ict', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'mentorship', 'laptop'],
        'province': 'ALL', 'eligibility': 'African student studying STEM at a SA institution.',
        'application_url': 'https://www.microsoft.com/africa/4afrika/',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'IBM Scholarship Programme 2026', 'provider': 'IBM South Africa',
        'description': 'Scholarship for computer science, data science and AI students.',
        'field': 'ict', 'funding_type': 'partial',
        'coverage': ['tuition', 'mentorship', 'laptop'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% in IT/Maths subjects.',
        'min_grade_average': 65,
        'application_url': 'https://www.ibm.com/employment/za/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Naspers Labs Scholarship 2026', 'provider': 'Naspers Foundry / Labs',
        'description': 'Scholarship for IT, data science and software engineering students.',
        'field': 'ict', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'books', 'stipend', 'laptop'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% average, financial need.',
        'min_grade_average': 65,
        'application_url': 'https://www.naspers.com/social-investment',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'MultiChoice Talent Factory Bursary 2026', 'provider': 'MultiChoice Group',
        'description': 'Bursary for media, film, broadcast technology and journalism students.',
        'field': 'arts', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books', 'mentorship'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying media / film / journalism.',
        'min_grade_average': 60,
        'application_url': 'https://multichoicetalentfactory.com/',
        'application_deadline': date(2026, 8, 31),
    },

    # ── Foundations / scholarships ─────────────────────────────────────────
    {
        'name': 'Mandela Rhodes Scholarship 2026', 'provider': 'Mandela Rhodes Foundation',
        'description': 'Postgraduate scholarship for exceptional African students with strong leadership potential.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'leadership_programme'],
        'province': 'ALL', 'eligibility': 'African citizen aged 19–30, completing/completed undergraduate degree with distinction.',
        'min_grade_average': 75,
        'application_url': 'https://www.mandelarhodes.org/scholarship/',
        'application_deadline': date(2026, 4, 30),
    },
    {
        'name': 'Oppenheimer Memorial Trust Bursary 2026', 'provider': 'Oppenheimer Memorial Trust',
        'description': 'Postgraduate scholarship for SA students pursuing masters or doctoral study at international universities.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'travel', 'accommodation', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, accepted into postgraduate study abroad.',
        'min_grade_average': 70,
        'application_url': 'https://www.omt.org.za/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Klaus-Jürgen Bathe Leadership Programme 2026', 'provider': 'Klaus-Jürgen Bathe Foundation',
        'description': 'Full undergraduate scholarship and leadership programme at UCT for top SA students.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'leadership_programme'],
        'province': 'WC', 'eligibility': 'SA citizen, Grade 12 ≥80% average, accepted into UCT undergraduate programme.',
        'min_grade_average': 80,
        'application_url': 'https://www.kjb.uct.ac.za/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'DG Murray Trust Pathways for Excellence 2026', 'provider': 'DG Murray Trust',
        'description': 'Funding programme for students at innovative SA initiatives in the social sector.',
        'field': 'humanities', 'funding_type': 'partial',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen at an accredited programme.',
        'application_url': 'https://dgmt.co.za/',
        'application_deadline': date(2026, 9, 30),
    },
    {
        'name': 'Canon Collins Scholarship 2026', 'provider': 'Canon Collins Trust',
        'description': 'Postgraduate scholarship for Southern Africans studying at SA or UK universities.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'stipend', 'travel'],
        'province': 'ALL', 'eligibility': 'Southern African citizen, ≥65% undergraduate average, social-justice commitment.',
        'min_grade_average': 65,
        'application_url': 'https://canoncollins.org/scholarships/',
        'application_deadline': date(2026, 2, 28),
    },
    {
        'name': 'Albertina Sisulu Executive Leadership Programme 2026', 'provider': 'ASELPH',
        'description': 'Postgraduate leadership programme in public health for healthcare practitioners.',
        'field': 'health', 'funding_type': 'partial',
        'coverage': ['tuition', 'mentorship'],
        'province': 'ALL', 'eligibility': 'SA healthcare practitioner with relevant experience.',
        'application_url': 'https://www.aselph.org.za/',
        'application_deadline': date(2026, 9, 30),
    },

    # ── Provincial bursaries ───────────────────────────────────────────────
    {
        'name': 'Gauteng City Region Academy Bursary 2026', 'provider': 'Gauteng Provincial Government',
        'description': 'Provincial bursary for Gauteng residents studying at SA public institutions.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'GP', 'eligibility': 'Gauteng resident, SA citizen, financial need.',
        'application_url': 'https://gcra.gauteng.gov.za/bursaries/',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'KZN Premier\'s Bursary 2026', 'provider': 'KZN Office of the Premier',
        'description': 'Bursary for KZN residents studying scarce-skills disciplines.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'KZN', 'eligibility': 'KZN resident, SA citizen, financial need.',
        'application_url': 'https://www.kznonline.gov.za/index.php/bursaries',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'Western Cape Government Bursary 2026', 'provider': 'Western Cape Government',
        'description': 'Provincial bursary across multiple departments (Health, Agriculture, Education).',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'WC', 'eligibility': 'Western Cape resident, SA citizen.',
        'application_url': 'https://www.westerncape.gov.za/general-publication/bursaries-and-financial-aid',
        'application_deadline': date(2026, 2, 28),
    },
    {
        'name': 'Eastern Cape Premier\'s Bursary 2026', 'provider': 'Eastern Cape Provincial Government',
        'description': 'Provincial bursary for EC residents studying scarce-skills disciplines.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'EC', 'eligibility': 'Eastern Cape resident, SA citizen, financial need.',
        'application_url': 'https://www.ecprov.gov.za/bursaries',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'Limpopo Provincial Bursary 2026', 'provider': 'Limpopo Provincial Government',
        'description': 'Provincial bursary for Limpopo residents studying scarce-skills fields.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation'],
        'province': 'LP', 'eligibility': 'Limpopo resident, SA citizen.',
        'application_url': 'https://www.limpopo.gov.za/index.php/services/education',
        'application_deadline': date(2026, 2, 28),
    },
    {
        'name': 'Mpumalanga Provincial Bursary 2026', 'provider': 'Mpumalanga Provincial Government',
        'description': 'Provincial bursary for Mpumalanga residents.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation'],
        'province': 'MP', 'eligibility': 'Mpumalanga resident, SA citizen.',
        'application_url': 'https://www.mpumalanga.gov.za/',
        'application_deadline': date(2026, 2, 28),
    },
    {
        'name': 'Northern Cape Premier\'s Bursary 2026', 'provider': 'Northern Cape Provincial Government',
        'description': 'Provincial bursary for NC residents.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition'],
        'province': 'NC', 'eligibility': 'Northern Cape resident, SA citizen.',
        'application_url': 'https://www.northern-cape.gov.za/',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'Free State Provincial Bursary 2026', 'provider': 'Free State Provincial Government',
        'description': 'Provincial bursary for Free State residents.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition'],
        'province': 'FS', 'eligibility': 'Free State resident, SA citizen.',
        'application_url': 'https://www.freestateonline.gov.za/',
        'application_deadline': date(2026, 1, 31),
    },
    {
        'name': 'North West Premier\'s Bursary 2026', 'provider': 'North West Provincial Government',
        'description': 'Provincial bursary for North West residents.',
        'field': 'any', 'funding_type': 'full',
        'coverage': ['tuition'],
        'province': 'NW', 'eligibility': 'North West resident, SA citizen.',
        'application_url': 'https://www.nwpg.gov.za/',
        'application_deadline': date(2026, 1, 31),
    },

    # ── SETAs ─────────────────────────────────────────────────────────────
    {
        'name': 'MerSETA Bursary 2026', 'provider': 'Manufacturing, Engineering and Related Services SETA',
        'description': 'Bursary for engineering, manufacturing and trade-related qualifications.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying engineering or trade qualification.',
        'application_url': 'https://www.merseta.org.za/our-services/bursaries-grants/',
        'application_deadline': date(2026, 4, 30),
    },
    {
        'name': 'ETDP SETA Bursary 2026', 'provider': 'Education, Training and Development Practices SETA',
        'description': 'Bursary for education, training and development qualifications.',
        'field': 'education', 'funding_type': 'partial',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying education or HR development.',
        'application_url': 'https://www.etdpseta.org.za/education/learner/bursary',
        'application_deadline': date(2026, 3, 31),
    },
    {
        'name': 'HWSETA Bursary 2026', 'provider': 'Health and Welfare SETA',
        'description': 'Bursary for healthcare and welfare studies (nursing, social work, OT, etc.).',
        'field': 'health', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying health/welfare-related qualification.',
        'application_url': 'https://www.hwseta.org.za/bursaries/',
        'application_deadline': date(2026, 3, 31),
    },
    {
        'name': 'AgriSETA Bursary 2026', 'provider': 'Agricultural SETA',
        'description': 'Bursary for agriculture, agribusiness and related disciplines.',
        'field': 'agriculture', 'funding_type': 'full',
        'coverage': ['tuition', 'accommodation', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying agriculture-related qualification.',
        'application_url': 'https://www.agriseta.co.za/bursaries/',
        'application_deadline': date(2026, 4, 30),
    },
    {
        'name': 'FoodBev SETA Bursary 2026', 'provider': 'Food and Beverages Manufacturing SETA',
        'description': 'Bursary for food technology, beverage technology and related qualifications.',
        'field': 'science', 'funding_type': 'partial',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying food science / food tech.',
        'application_url': 'https://www.foodbev.co.za/skillsfunding/bursaries/',
        'application_deadline': date(2026, 3, 31),
    },
    {
        'name': 'CHIETA Bursary 2026', 'provider': 'Chemical Industries Education and Training Authority',
        'description': 'Bursary for chemical engineering, chemistry and related disciplines.',
        'field': 'engineering', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'stipend'],
        'province': 'ALL', 'eligibility': 'SA citizen, studying chemical engineering or chemistry.',
        'application_url': 'https://www.chieta.org.za/bursaries/',
        'application_deadline': date(2026, 3, 31),
    },

    # ── Law firms ─────────────────────────────────────────────────────────
    {
        'name': 'Webber Wentzel Bursary 2026', 'provider': 'Webber Wentzel',
        'description': 'Bursary for LLB students with strong academic record and leadership potential.',
        'field': 'law', 'funding_type': 'full',
        'coverage': ['tuition', 'books', 'mentorship'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% average in undergraduate study, on LLB pathway.',
        'min_grade_average': 65,
        'application_url': 'https://www.webberwentzel.com/Pages/Careers/Bursary.aspx',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'ENS Africa Bursary 2026', 'provider': 'Edward Nathan Sonnenbergs (ENSafrica)',
        'description': 'Bursary for LLB students. Includes mentorship and articles upon completion.',
        'field': 'law', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, ≥65% in undergraduate / first year LLB.',
        'min_grade_average': 65,
        'application_url': 'https://www.ensafrica.com/Careers/',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Cliffe Dekker Hofmeyr Bursary 2026', 'provider': 'Cliffe Dekker Hofmeyr',
        'description': 'Bursary for LLB students with a commitment to legal practice.',
        'field': 'law', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, top-quartile academic results.',
        'min_grade_average': 65,
        'application_url': 'https://www.cliffedekkerhofmeyr.com/en/careers/students.html',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Bowmans Bursary 2026', 'provider': 'Bowman Gilfillan Africa Group',
        'description': 'Bursary for LLB and commercial-law students.',
        'field': 'law', 'funding_type': 'full',
        'coverage': ['tuition', 'books'],
        'province': 'ALL', 'eligibility': 'SA citizen, strong academic record.',
        'min_grade_average': 65,
        'application_url': 'https://bowmanslaw.com/careers/students/',
        'application_deadline': date(2026, 6, 30),
    },

    # ── Women / under-represented ──────────────────────────────────────────
    {
        'name': 'Women in Engineering Bursary 2026', 'provider': 'WomEng (Women in Engineering SA)',
        'description': 'Bursary and mentorship programme for female engineering students.',
        'field': 'engineering', 'funding_type': 'partial',
        'coverage': ['tuition', 'mentorship'],
        'province': 'ALL', 'eligibility': 'SA female student studying engineering.',
        'application_url': 'https://www.womeng.org/',
        'application_deadline': date(2026, 6, 30),
    },
    {
        'name': 'Mastercard Foundation Scholars at UCT 2026', 'provider': 'Mastercard Foundation',
        'description': 'Comprehensive scholarship at UCT for African students with academic excellence and community leadership.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'mentorship', 'travel'],
        'province': 'WC', 'eligibility': 'African student with strong academic record, financial need.',
        'min_grade_average': 70,
        'application_url': 'https://www.uct.ac.za/main/teaching-and-learning/mastercard-foundation-scholars-program',
        'application_deadline': date(2026, 7, 31),
    },
    {
        'name': 'Mastercard Foundation Scholars at Wits 2026', 'provider': 'Mastercard Foundation',
        'description': 'Comprehensive scholarship at Wits for African students from disadvantaged backgrounds.',
        'field': 'any', 'funding_type': 'scholarship',
        'coverage': ['tuition', 'accommodation', 'books', 'stipend', 'mentorship', 'travel'],
        'province': 'GP', 'eligibility': 'African student, financial need, strong academic record.',
        'min_grade_average': 70,
        'application_url': 'https://www.wits.ac.za/mastercardfoundation/',
        'application_deadline': date(2026, 8, 31),
    },
]


def run():
    created = 0
    updated = 0
    for b in MORE_BURSARIES_2026:
        obj, made = Bursary.objects.get_or_create(
            name=b['name'],
            defaults={**b, 'is_active': True},
        )
        if made:
            created += 1
        else:
            for k, v in b.items():
                setattr(obj, k, v)
            obj.is_active = True
            obj.save()
            updated += 1
    return created, updated


c, u = run()
total = Bursary.objects.filter(is_active=True).count()
print(f'Added: {c}    Updated: {u}    Active bursaries now: {total}')

from collections import Counter
print('\nBy field:')
for field, n in Counter(
    Bursary.objects.filter(is_active=True).values_list('field', flat=True)
).most_common():
    print(f'  {field:<15} {n}')
print('\nBy province:')
for prov, n in Counter(
    Bursary.objects.filter(is_active=True).values_list('province', flat=True)
).most_common():
    print(f'  {prov:<5} {n}')
