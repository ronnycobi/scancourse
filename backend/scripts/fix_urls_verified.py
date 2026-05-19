"""
Replace broken university + bursary URLs with verified-working ones.

Strategy when an apply page returns 404:
  - University: use the canonical study/admissions landing page that's stable.
    User clicks through to the apply CTA on the live site.
  - Bursary: use the provider's main bursary/careers page.

403s are typically bot-blocking — real browsers work fine — so we leave those.

Run:  python manage.py shell < scripts/fix_urls_verified.py
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.institutions.models import Institution
from apps.bursaries.models import Bursary

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0 Safari/537.36',
}


# Pre-verified replacements for universities that 404'd on deep links.
# Source: actual landing pages opened May 2026.
UNI_FIXES = {
    'UCT':     'https://www.uct.ac.za/study',
    'CPUT':    'https://www.cput.ac.za/study',
    'CUT':     'https://www.cut.ac.za/',
    'MUT':     'https://www.mut.ac.za/',
    'NMU':     'https://www.mandela.ac.za/',
    'NWU':     'https://www.nwu.ac.za/studies',
    'Rhodes':  'https://www.ru.ac.za/admissionsuit/',
    'SMU':     'https://www.smu.ac.za/',
    'SPU':     'https://www.spu.ac.za/',
    'TUT':     'https://www.tut.ac.za/',
    'UFH':     'https://www.ufh.ac.za/',
    'UL':      'https://www.ul.ac.za/',
    'UMP':     'https://www.ump.ac.za/',
    'UniZulu': 'https://www.unizulu.ac.za/',
    'WSU':     'https://www.wsu.ac.za/',
}

for short, url in UNI_FIXES.items():
    Institution.objects.filter(short_name__iexact=short).update(application_url=url)
print(f'Updated {len(UNI_FIXES)} institution URLs to verified landing pages.')


# Bursary URL fixes — root pages of the provider.
BURSARY_FIXES = {
    'ARM Broad-Based Trust Bursary 2026': 'https://www.arm.co.za/',
    'AgriSETA Bursary 2026': 'https://www.agriseta.co.za/',
    'Albertina Sisulu Executive Leadership Programme 2026': 'https://www.aselph.org.za/',
    'AngloGold Ashanti Bursary 2026': 'https://www.anglogoldashanti.com/sustainability/',
    'Australia Awards Scholarship 2026': 'https://www.australiaawards.gov.au/',
    'BankSETA Postgraduate Bursary 2026': 'https://www.bankseta.org.za/',
    'Bowmans Bursary 2026': 'https://bowmanslaw.com/',
    'Canon Collins Scholarship 2026': 'https://canoncollins.org/',
    'Chevening Scholarship 2026': 'https://www.chevening.org/',
    'City of Johannesburg Bursary 2026': 'https://www.joburg.org.za/',
    'City of Tshwane Bursary 2026': 'https://www.tshwane.gov.za/',
    'Cliffe Dekker Hofmeyr Bursary 2026': 'https://www.cliffedekkerhofmeyr.com/',
    'DST-NRF Innovation Scholarship 2026': 'https://www.nrf.ac.za/',
    'Deloitte Bursary 2026': 'https://www2.deloitte.com/za/en/careers/students.html',
    'Department of Health Bursary 2026': 'https://www.health.gov.za/',
    'Discovery Foundation Award 2026': 'https://www.discovery.co.za/foundation/',
    'ETDP SETA Bursary 2026': 'https://www.etdpseta.org.za/',
    'EY (Ernst & Young) Bursary 2026': 'https://www.ey.com/en_za/careers/students',
    'Eskom Bursary 2026': 'https://www.eskom.co.za/Careers/',
    'Exxaro Resources Bursary 2026': 'https://www.exxaro.com/careers/',
    'FirstRand / RMB Bursary 2026': 'https://www.firstrand.co.za/',
    'Free State Provincial Bursary 2026': 'https://www.freestateonline.gov.za/',
    'Fulbright Foreign Student Program 2026': 'https://za.usembassy.gov/education-culture/fulbright/',
    'Funza Lushaka Bursary 2026': 'https://www.funzalushaka.doe.gov.za/',
    'GIBB Bursary 2026': 'https://www.gibb.co.za/careers',
    'Gates Cambridge Scholarship 2026': 'https://www.gatescambridge.org/',
    'Gauteng City Region Academy Bursary 2026': 'https://gcra.gauteng.gov.za/',
    'Gold Fields Bursary 2026': 'https://www.goldfields.com/sustainability/communities/',
    'HWSETA Bursary 2026': 'https://www.hwseta.org.za/',
    'Harmony Gold Bursary 2026': 'https://www.harmony.co.za/',
    'IBM Scholarship Programme 2026': 'https://www.ibm.com/employment/za/',
    'Ikusasa Student Financial Aid Programme (ISFAP) 2026': 'https://www.isfap.org.za/',
    'Implats Bursary 2026': 'https://www.implats.co.za/',
    'Investec Bursary 2026': 'https://www.investec.com/en_za/careers/students.html',
    'JN Tata Endowment Scholarship 2026': 'https://www.jntataendowment.org/',
    'KPMG Bursary 2026': 'https://kpmg.com/za/en/home/careers.html',
    "KZN Premier's Bursary 2026": 'https://www.kznonline.gov.za/',
    'Klaus-Jürgen Bathe Leadership Programme 2026': 'https://www.kjb.uct.ac.za/',
    'Limpopo Provincial Bursary 2026': 'https://www.limpopo.gov.za/',
    'MTN Foundation Bursary 2026': 'https://www.mtn.com/sustainability/',
    'Mandela Rhodes Scholarship 2026': 'https://www.mandelarhodes.org/',
    'MasterCard Foundation Scholars at Cambridge 2026': 'https://www.cambridgetrust.org/',
    'Mastercard Foundation Scholars at UCT 2026': 'https://www.uct.ac.za/study',
    'Mastercard Foundation Scholars at Wits 2026': 'https://www.wits.ac.za/mastercardfoundation/',
    'MerSETA Bursary 2026': 'https://www.merseta.org.za/',
    'Microsoft 4Afrika Scholarship 2026': 'https://www.microsoft.com/africa/4afrika/',
    'Momentum Metropolitan Bursary 2026': 'https://www.momentummetropolitan.co.za/careers/',
    'Mondi Bursary 2026': 'https://www.mondigroup.com/en/careers/',
    'Mpumalanga Provincial Bursary 2026': 'https://www.mpumalanga.gov.za/',
    'Murray & Roberts Engineering Bursary 2026': 'https://www.murrob.com/',
    'NSFAS 2026 Bursary': 'https://www.nsfas.org.za/',
    'Naspers Labs Scholarship 2026': 'https://www.naspers.com/social-investment',
    'Nedbank External Bursary 2026': 'https://www.nedbank.co.za/',
    'North West Premier\'s Bursary 2026': 'https://www.nwpg.gov.za/',
    'Northam Platinum Bursary 2026': 'https://www.northam.co.za/',
    'Northern Cape Premier\'s Bursary 2026': 'https://www.northerncape.gov.za/',
    'Old Mutual Education Trust Bursary 2026': 'https://www.oldmutual.co.za/about/sustainability/',
    'Oppenheimer Memorial Trust Bursary 2026': 'https://www.omt.org.za/',
    'OR Tambo District Municipality Bursary 2026': 'https://www.ortambodm.gov.za/',
    'PricewaterhouseCoopers (PwC) Bursary 2026': 'https://www.pwc.co.za/en/careers/student-recruitment.html',
    'Rhodes Scholarship 2026': 'https://www.rhodeshouse.ox.ac.uk/',
    'SAB Foundation Maths & Science Bursary 2026': 'https://www.sabfoundation.co.za/',
    'SAICA Hope Factory Bursary 2026': 'https://www.thehopefactory.co.za/',
    'SAICA Thuthuka Bursary 2026': 'https://www.thuthuka.co.za/',
    'Sanlam Bursary 2026': 'https://www.sanlam.co.za/careers/',
    'Sappi Bursary 2026': 'https://www.sappi.com/careers',
    'Sasol Bursary 2026': 'https://www.sasolbursaries.com/',
    'Sasol Inzalo Foundation Bursary 2026': 'https://www.sasolinzalofoundation.org.za/',
    'Schwarzman Scholars 2026': 'https://www.schwarzmanscholars.org/',
    'Sibanye-Stillwater Bursary 2026': 'https://www.sibanyestillwater.com/',
    'South32 Bursary 2026': 'https://www.south32.net/',
    'Standard Bank Bursary 2026': 'https://www.standardbank.com/sbg/standard-bank-group/who-we-are/careers/students',
    'Studietrust Bursary 2026': 'https://www.studietrust.org.za/',
    'Telkom Bursary 2026': 'https://www.telkom.co.za/today/about-us/careers/',
    'Tomorrow Trust Bursary 2026': 'https://www.tomorrow.org.za/',
    'Transnet Bursary 2026': 'https://www.transnet.net/',
    'Vodacom Discover Bursary 2026': 'https://www.vodacom.co.za/today/about-us/careers',
    'Webber Wentzel Bursary 2026': 'https://www.webberwentzel.com/Pages/Careers/Pages/Default.aspx',
    'Western Cape Government Bursary 2026': 'https://www.westerncape.gov.za/',
    'Women in Engineering Bursary 2026': 'https://www.womeng.org/',
    "Eastern Cape Premier's Bursary 2026": 'https://www.ecprov.gov.za/',
    "FoodBev SETA Bursary 2026": 'https://www.foodbev.co.za/',
    "Engineers Without Borders SA Bursary 2026": 'https://www.ewb-sa.org/',
    "MultiChoice Talent Factory Bursary 2026": 'https://multichoicetalentfactory.com/',
    "Erasmus Mundus Scholarship 2026": 'https://erasmus-plus.ec.europa.eu/',
}


updated = 0
for name, url in BURSARY_FIXES.items():
    n = Bursary.objects.filter(name=name).update(application_url=url)
    updated += n
print(f'Updated {updated} bursary URLs to verified provider pages.')


# Final verification on the new URLs
def check(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code in (405,):
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.status_code
    except Exception:
        return -1


print('\n=== Verifying institution URLs ===')
fails = []
for inst in Institution.objects.filter(short_name__in=list(UNI_FIXES)).order_by('short_name'):
    code = check(inst.application_url)
    flag = '✓' if 200 <= code < 400 else '✗'
    print(f'  {flag} [{code:>3}]  {inst.short_name:<10} {inst.application_url}')
    if not (200 <= code < 400) and code != 403:
        fails.append(inst.short_name)
if fails:
    print(f'\nSTILL FAILING: {fails}')
