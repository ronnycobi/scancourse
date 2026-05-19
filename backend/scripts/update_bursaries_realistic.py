"""
Update bursaries with more realistic / spread-out 2026 application windows,
plus richer eligibility text. Run after seed_bursaries_2026* scripts.

NOTE: Real-world deadlines shift yearly. The dates here reflect typical
provider-announced windows for the 2026 academic year intake. For
production use, ALWAYS confirm against the official application URL.

Run:  python manage.py shell < scripts/update_bursaries_realistic.py
"""
from datetime import date
from apps.bursaries.models import Bursary


UPDATES: dict[str, dict] = {
    # ── Big ones — well-known fixed dates ────────────────────────────────
    'NSFAS 2026 Bursary': {
        'application_deadline': date(2026, 1, 31),
        'eligibility': (
            'SA citizen or permanent resident with valid SA ID. Household '
            'income ≤ R350 000/year (or ≤ R600 000 for persons with '
            'disabilities or SASSA-grant recipients). Must be a first-time '
            'entering student at a public university or TVET college. '
            'Returning students must have passed at least 50% of modules '
            'in the previous year. Cannot have completed a previous '
            'qualification funded by NSFAS.'
        ),
    },
    'Funza Lushaka Bursary 2026': {
        'application_deadline': date(2026, 1, 13),
        'eligibility': (
            'SA citizen with valid SA ID. Studying BEd or PGCE in a priority '
            'subject (Maths, Physical Science, Technology, African '
            'Languages, Foundation Phase, English FAL). Must be at a '
            'public university. Signed undertaking to teach at a public '
            'school for the same number of years as funded. Minimum '
            'admission requirement: 60% in language of teaching and 50%+ '
            'in Maths/Science for those subjects.'
        ),
    },
    # ── Mining sector — typical April-May window for next year's intake ──
    'Sasol Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Grade 12 with minimum: English ≥60%, Maths ≥60%, '
            'Physical Sciences ≥60% (chemical/mechanical/electrical eng) '
            'or studying BSc/BEng/BCom Engineering, IT, Accounting (CA) '
            'or Maths Sciences. 1st/2nd year university applicants need '
            '65% average. Includes vacation work and graduate placement '
            'obligation at Sasol.'
        ),
    },
    'Eskom Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen with valid ID. Grade 12 with English HL ≥50%, '
            'Maths ≥60%, Physical Sciences ≥60%. Studying BEng/BSc Eng '
            '(Electrical, Mechanical, Civil, Industrial, Computer) or BSc '
            'IT/Computer Science. Work-back obligation at Eskom equal to '
            'years funded.'
        ),
    },
    'Anglo American Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Grade 12 with English ≥60%, Maths ≥65%, Physical '
            'Sciences ≥65%. Studying Mining / Metallurgical / Mechanical / '
            'Electrical / Civil / Chemical Engineering or Geology. '
            'Financial need (combined household income ≤ R600 000) '
            'considered. Vacation work and graduate placement included.'
        ),
    },
    'Sibanye-Stillwater Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Maths ≥65% and Physical Sciences ≥65%. Studying '
            'Mining / Metallurgical / Mechanical / Electrical / Chemical / '
            'Industrial Engineering, Geology or Surveying. Vacation work '
            'and work-back obligation included.'
        ),
    },
    'Gold Fields Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'SA citizen. Maths and Physical Sciences ≥60%. Studying '
            'Mining / Metallurgical / Mechanical Engineering, Geology, '
            'Surveying or related disciplines. Vacation work and graduate '
            'employment obligation.'
        ),
    },
    'AngloGold Ashanti Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Maths ≥60%, Physical Sciences ≥60%. Studying '
            'Mining Engineering, Metallurgy, Mechanical/Electrical '
            'Engineering, Geology or Mine Surveying. Includes vacation '
            'work and a service obligation.'
        ),
    },
    'Implats Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'SA citizen, with preference for communities near Implats '
            'operations (Rustenburg, Marula, Springs). Maths and Physical '
            'Sciences ≥60% in Grade 12. Studying Engineering, Metallurgy, '
            'Mining, or Geology.'
        ),
    },
    'Exxaro Resources Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen, Maths ≥65%, Physical Sciences ≥65%. Studying '
            'Mining / Mechanical / Electrical / Industrial / Chemical / '
            'Civil Engineering or Metallurgy.'
        ),
    },
    'Harmony Gold Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Maths and Physical Sciences ≥60%. Studying '
            'Mining / Metallurgical Engineering, Geology, or Mine Surveying.'
        ),
    },
    'Northam Platinum Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen, with preference for Limpopo / North West '
            'community members. Maths and Physical Sciences ≥60%. '
            'Studying Engineering, Metallurgy, or Mining-related.'
        ),
    },
    # ── Industrial ─────────────────────────────────────────────────────
    'Sappi Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen, Maths and Physical Sciences ≥60%. Studying '
            'Chemical / Mechanical / Electrical / Industrial Engineering, '
            'Forestry, Pulp and Paper Technology, Wood Science, Chemistry.'
        ),
    },
    'Mondi Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. Maths and Physical Sciences ≥60%. Studying '
            'Chemical / Mechanical / Electrical / Industrial Engineering, '
            'Forestry, or Pulp & Paper Technology.'
        ),
    },
    'Transnet Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. Maths ≥60%, Physical Sciences ≥55%. Studying '
            'Civil / Mechanical / Electrical / Industrial Engineering, '
            'Logistics, Supply Chain, or related fields.'
        ),
    },
    # ── Finance / Banking ──────────────────────────────────────────────
    'Investec Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'SA citizen. Grade 12 ≥70% Maths and ≥65% English. Intending '
            'to study BCom Accounting (CA stream), BCom Actuarial Science, '
            'BSc Mathematical Sciences, or BCom Finance/Investments. '
            'Strong leadership and extramural record valued.'
        ),
    },
    'Standard Bank Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. Grade 12 ≥65% average with Maths ≥65%. Studying '
            'BCom (Accounting, Finance, Economics), Actuarial Science, '
            'Quantitative Risk Management, IT, Computer Science or '
            'Mathematical Sciences. Financial need considered.'
        ),
    },
    'ABSA Bursary Programme 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. Grade 12 ≥70% Maths. Studying BCom Accounting '
            '(CA stream), Actuarial Science, Finance, Statistics, IT, '
            'or Mathematical Sciences. Demonstrate financial need.'
        ),
    },
    'FirstRand / RMB Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. Grade 12 ≥75% Maths and ≥70% English. Studying '
            'Actuarial Science, BSc Mathematical Sciences, BCom Finance, '
            'Quantitative Risk Management, or Computer Science.'
        ),
    },
    'Nedbank External Bursary 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen, household income ≤ R600 000. ≥65% average in '
            'undergrad / Grade 12 with ≥65% Maths. Studying BCom '
            'Accounting / Finance / IT / Risk Management.'
        ),
    },
    'Sanlam Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. Grade 12 ≥75% Maths. Studying BCom Actuarial '
            'Science, BSc Mathematical Sciences, BCom Finance, or '
            'Quantitative Risk Management.'
        ),
    },
    'Liberty Group Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. ≥70% Maths in Grade 12. Studying Actuarial '
            'Science, BCom Finance / Investments, or IT.'
        ),
    },
    'Momentum Metropolitan Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. ≥70% Maths. Studying Actuarial Science, '
            'Finance, IT, Data Science, Statistics, or Computer Science.'
        ),
    },
    'Capitec Bank Bursary 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen. ≥65% average in Grade 12 with Maths ≥65%. '
            'Studying BCom, BSc IT, Computer Science, or Data Science. '
            'Financial need preferred.'
        ),
    },
    'KPMG Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Grade 12 ≥70% Maths and ≥65% English. Studying '
            'BCom Accounting on the CA(SA) pathway at a SAICA-accredited '
            'university.'
        ),
    },
    'EY (Ernst & Young) Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. ≥70% Maths in Grade 12. Studying BCom Accounting '
            '(CA stream) or BCom Honours in Accounting.'
        ),
    },
    'BDO South Africa Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. ≥65% Maths in Grade 12. Studying BCom Accounting '
            'on the CA(SA) pathway.'
        ),
    },
    'PricewaterhouseCoopers (PwC) Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Grade 12 ≥70% Maths and ≥60% English. Studying '
            'BCom Accounting on the CA(SA) stream at a SAICA-accredited '
            'university. Demonstrate financial need.'
        ),
    },
    'Deloitte Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. ≥70% in matric Maths and ≥65% English. Studying '
            'BCom Accounting / Actuarial Science / Computer Science at '
            'an accredited university.'
        ),
    },
    # ── Accounting / professional bodies ──────────────────────────────
    'SAICA Thuthuka Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'African or Coloured SA citizen. Grade 12 with Maths ≥60% '
            '(NSC) or ≥70% (IEB). English HL or FAL ≥60%. Household '
            'income ≤ R600 000/year. Accepted into a SAICA-accredited '
            'BCom Accounting (CA stream) programme. Includes mentorship, '
            'leadership development and laptop allowance.'
        ),
    },
    # ── SETAs ─────────────────────────────────────────────────────────
    'MerSETA Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'SA citizen, unemployed youth (18-35). Studying / intending '
            'to study Engineering, Manufacturing or Trade qualifications '
            'at public TVET or university.'
        ),
    },
    'ETDP SETA Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen. Studying education, training, or development '
            'practices qualification at undergraduate or postgrad level.'
        ),
    },
    'HWSETA Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen, unemployed. Studying Nursing, Social Work, '
            'Pharmacy, Occupational Therapy, Physiotherapy or other '
            'health/welfare disciplines at NQF 5+.'
        ),
    },
    'AgriSETA Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen. Studying Agricultural Sciences / Agribusiness / '
            'Veterinary or related qualification at NQF 5+.'
        ),
    },
    'FoodBev SETA Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen. Studying Food Science, Food Technology, Beverage '
            'Technology, or Consumer Sciences (Food).'
        ),
    },
    'CHIETA Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen. Studying Chemical Engineering, Chemistry, '
            'Chemical Technology, Pharmacy, or related disciplines.'
        ),
    },
    'BankSETA Postgraduate Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'SA citizen with completed BCom/BSc (Finance/Accounting/'
            'Economics/Risk/Maths/Statistics). Accepted into Honours / '
            'Masters in a banking-relevant discipline.'
        ),
    },
    # ── Tech / ICT ────────────────────────────────────────────────────
    'Vodacom Discover Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. ≥65% Maths in Grade 12. Studying BSc Computer '
            'Science, IT, Software Engineering, Data Science, Electrical '
            'Engineering or Telecommunications.'
        ),
    },
    'MTN Foundation Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen from previously-disadvantaged background. '
            '≥60% Maths and English. Studying ICT, Engineering, Business, '
            'or Finance.'
        ),
    },
    'Telkom Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. Grade 12 with Maths ≥60% and Physical Sciences '
            '≥60%. Studying Electrical / Computer / Telecommunications '
            'Engineering, IT, or Computer Science.'
        ),
    },
    'Microsoft 4Afrika Scholarship 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'African student studying STEM at an accredited African '
            'university. Strong academic record (≥65%), demonstrated '
            'leadership and community engagement.'
        ),
    },
    'IBM Scholarship Programme 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. ≥65% in Maths and IT subjects. Studying Computer '
            'Science, Data Science, or AI at NQF 7+.'
        ),
    },
    'Naspers Labs Scholarship 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen, household income ≤ R600 000. ≥65% average in '
            'Grade 12 or undergrad. Studying IT, Data Science, Software '
            'Engineering, or Computer Science.'
        ),
    },
    'MultiChoice Talent Factory Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen aged 18-25. Passion and proven interest in film, '
            'television, journalism, or media production. Studying or '
            'intending to study media-related qualification.'
        ),
    },
    # ── Health ────────────────────────────────────────────────────────
    'Department of Health Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'SA citizen. Accepted into Medicine, Dentistry, Pharmacy, '
            'Nursing, OT, Physio, Speech Therapy, Radiography or other '
            'health science programme at a SA university. Service '
            'obligation in the public health system after graduation '
            '(1 year per year funded).'
        ),
    },
    'Discovery Foundation Award 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen, qualified medical doctor or postgraduate medical '
            'student. Strong academic record and research/clinical '
            'specialty interest. Funding for specialist training and '
            'medical research.'
        ),
    },
    # ── Science / research ────────────────────────────────────────────
    'DST-NRF Innovation Scholarship 2026': {
        'application_deadline': date(2026, 6, 15),
        'eligibility': (
            'SA citizen or permanent resident. Completed Honours/Masters '
            'with ≥65% average. Accepted into a Masters/PhD at a SA '
            'university in DST/NRF priority STEM areas.'
        ),
    },
    'SAB Foundation Maths & Science Bursary 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen. Grade 12 ≥70% Maths and ≥70% Physical Sciences. '
            'Studying Engineering, Computer Science, BSc (Pure Sciences), '
            'or Maths/Statistics.'
        ),
    },
    # ── Foundations / scholarships ────────────────────────────────────
    'Allan Gray Orbis Foundation 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen, in Grade 11 or 12, or 1st-year university. '
            '≥70% Grade 11 / 12 average. Demonstrated entrepreneurial '
            'spirit, leadership and resilience. Selected through '
            'multi-stage assessment.'
        ),
    },
    'Mandela Rhodes Scholarship 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'African citizen aged 19-30. Completed (or completing) '
            'undergraduate with strong distinction. Demonstrated '
            'leadership, reconciliation, education and entrepreneurship '
            'values. Accepted into postgraduate study at a SA university.'
        ),
    },
    'Oppenheimer Memorial Trust Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen with completed undergraduate degree (≥70% '
            'average). Accepted into postgraduate study at a reputable '
            'university abroad. Application via the host university.'
        ),
    },
    'Klaus-Jürgen Bathe Leadership Programme 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen with Grade 12 ≥80% average. Demonstrated '
            'leadership and community engagement. Accepted into a UCT '
            'undergraduate programme. Selection via interview.'
        ),
    },
    'DG Murray Trust Pathways for Excellence 2026': {
        'application_deadline': date(2026, 8, 31),
        'eligibility': (
            'SA citizen. Enrolled in an innovative SA programme '
            'partnered with DGMT. Application via the partner programme.'
        ),
    },
    'Canon Collins Scholarship 2026': {
        'application_deadline': date(2026, 1, 31),
        'eligibility': (
            'Southern African citizen (SA, Botswana, Lesotho, Eswatini, '
            'Namibia, Malawi, Mozambique, Zambia, Zimbabwe). Completed '
            'undergrad ≥65% average. Strong social justice commitment. '
            'Accepted into Masters / Honours at SA or UK university.'
        ),
    },
    'Albertina Sisulu Executive Leadership Programme 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen working in health care (clinical, administrative, '
            'or operational role) with minimum 5 years experience. '
            'Postgraduate leadership programme — not for undergraduate '
            'study.'
        ),
    },
    # ── Provincial bursaries — spread out ─────────────────────────────
    'Gauteng City Region Academy Bursary 2026': {
        'application_deadline': date(2026, 1, 31),
        'eligibility': (
            'Gauteng resident (proof required). SA citizen. ≥60% Grade 12 '
            'average. Household income ≤ R350 000. Studying scarce-skills '
            'qualification at SA public institution.'
        ),
    },
    "KZN Premier's Bursary 2026": {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'KwaZulu-Natal resident (proof required). SA citizen. ≥60% '
            'Grade 12 average. Household income ≤ R350 000. Studying '
            'scarce-skills field.'
        ),
    },
    'Western Cape Government Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'Western Cape resident. SA citizen. ≥60% Grade 12 average. '
            'Studying medicine, nursing, pharmacy, social work, '
            'agriculture or other priority field.'
        ),
    },
    "Eastern Cape Premier's Bursary 2026": {
        'application_deadline': date(2026, 1, 31),
        'eligibility': (
            'Eastern Cape resident. SA citizen. ≥60% Grade 12 average. '
            'Household income ≤ R350 000. Studying scarce-skills field.'
        ),
    },
    'Limpopo Provincial Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'Limpopo resident. SA citizen. ≥60% Grade 12 average. '
            'Studying scarce-skills field at SA public institution.'
        ),
    },
    'Mpumalanga Provincial Bursary 2026': {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'Mpumalanga resident. SA citizen. ≥60% average. Studying '
            'scarce-skills qualification.'
        ),
    },
    "Northern Cape Premier's Bursary 2026": {
        'application_deadline': date(2026, 1, 31),
        'eligibility': (
            'Northern Cape resident. SA citizen. ≥60% average. Studying '
            'scarce-skills field.'
        ),
    },
    'Free State Provincial Bursary 2026': {
        'application_deadline': date(2026, 2, 28),
        'eligibility': (
            'Free State resident. SA citizen. ≥60% Grade 12 average. '
            'Studying scarce-skills field.'
        ),
    },
    "North West Premier's Bursary 2026": {
        'application_deadline': date(2026, 3, 31),
        'eligibility': (
            'North West resident. SA citizen. ≥60% average. Studying '
            'scarce-skills qualification.'
        ),
    },
    # ── Engineering consultancies ─────────────────────────────────────
    'AECOM Bursary 2026': {
        'application_deadline': date(2026, 8, 31),
        'eligibility': (
            'SA citizen. ≥60% Maths and Physical Sciences. Studying '
            'Civil / Structural / Mechanical / Electrical / Environmental '
            'Engineering at an ECSA-accredited university.'
        ),
    },
    'WSP Bursary 2026': {
        'application_deadline': date(2026, 8, 31),
        'eligibility': (
            'SA citizen. ≥60% Maths and Physical Sciences. Studying '
            'Civil / Structural / Mechanical / Electrical / Environmental '
            'Engineering.'
        ),
    },
    'GIBB Bursary 2026': {
        'application_deadline': date(2026, 9, 30),
        'eligibility': (
            'SA citizen. ≥60% Maths and Physical Sciences. Studying '
            'Civil / Structural / Transportation / Mechanical / '
            'Electrical Engineering.'
        ),
    },
    'Aurecon Bursary 2026': {
        'application_deadline': date(2026, 9, 30),
        'eligibility': (
            'SA citizen. ≥60% Maths and Physical Sciences. Studying '
            'Engineering (Civil, Mechanical, Electrical, Environmental).'
        ),
    },
    'South32 Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen. Maths ≥65%, Physical Sciences ≥65%. Studying '
            'Mining / Metallurgical / Mechanical / Electrical / Chemical '
            'Engineering at SA university.'
        ),
    },
    'ARM Broad-Based Trust Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA citizen from historically-disadvantaged background. '
            'Maths and Physical Sciences ≥60%. Studying Mining, '
            'Engineering or related disciplines.'
        ),
    },
    'Old Mutual Education Trust Bursary 2026': {
        'application_deadline': date(2026, 4, 30),
        'eligibility': (
            'SA citizen. ≥70% Maths. Demonstrate financial need. '
            'Studying BCom Actuarial Science, Finance, Accounting or '
            'related disciplines.'
        ),
    },
    # ── Law firms ─────────────────────────────────────────────────────
    'Webber Wentzel Bursary 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen. ≥65% in 1st year LLB or undergraduate average. '
            'Demonstrated leadership, financial need, and commitment to '
            'practicing law. Includes mentorship and articles.'
        ),
    },
    'ENS Africa Bursary 2026': {
        'application_deadline': date(2026, 8, 31),
        'eligibility': (
            'SA citizen, ≥65% in undergrad. On LLB pathway with '
            'commitment to commercial law practice.'
        ),
    },
    'Cliffe Dekker Hofmeyr Bursary 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'SA citizen. Top-quartile academic results in LLB / BCom '
            'Law / BA Law. Demonstrated leadership.'
        ),
    },
    'Bowmans Bursary 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'SA citizen. Strong undergrad record (≥65%). LLB students '
            'with interest in commercial / corporate law.'
        ),
    },
    'Murray & Roberts Engineering Bursary 2026': {
        'application_deadline': date(2026, 9, 30),
        'eligibility': (
            'SA citizen. ≥65% Maths and Physical Sciences in Grade 12. '
            'Studying Civil / Mechanical / Electrical / Mining '
            'Engineering at an ECSA-accredited university.'
        ),
    },
    # ── Women / under-represented ─────────────────────────────────────
    'Women in Engineering Bursary 2026': {
        'application_deadline': date(2026, 5, 31),
        'eligibility': (
            'SA female citizen studying any Engineering discipline at '
            'a SA university. ≥60% average required. Includes '
            'mentorship programme.'
        ),
    },
    'Mastercard Foundation Scholars at UCT 2026': {
        'application_deadline': date(2026, 6, 30),
        'eligibility': (
            'African citizen with strong academic record (≥70% Grade 12 '
            'or undergrad average). Demonstrated financial need '
            '(household income ≤ R350 000 typically). Leadership and '
            'community engagement. Accepted into UCT undergrad programme.'
        ),
    },
    'Mastercard Foundation Scholars at Wits 2026': {
        'application_deadline': date(2026, 7, 31),
        'eligibility': (
            'African citizen with ≥70% Grade 12 or undergrad average. '
            'Demonstrated financial need. Leadership track record. '
            'Accepted into Wits undergraduate degree.'
        ),
    },
}


updated = 0
not_found = []
for name, fields in UPDATES.items():
    qs = Bursary.objects.filter(name=name)
    if not qs.exists():
        not_found.append(name)
        continue
    qs.update(**fields)
    updated += 1

print(f'Updated: {updated}')
if not_found:
    print(f'\nNot found in DB (may have different names): {len(not_found)}')
    for n in not_found:
        print(f'  - {n}')

from collections import Counter
print('\nDeadline distribution after update:')
for d, n in sorted(Counter(
    str(b.application_deadline)
    for b in Bursary.objects.filter(is_active=True)
).items()):
    print(f'  {d}: {n}')
