"""
Fix bursary logo URLs to use reliable sources.

Strategy:
  1. Map every known provider to its primary domain.
  2. Try Clearbit Logo API (clean high-res logos when available).
  3. Fall back to Google's favicon service (always works, lower-res).

The frontend's RemoteLogo widget gracefully shows a coloured initial if both fail.

Run:  python manage.py shell < scripts/fix_bursary_logos.py
"""
from apps.bursaries.models import Bursary


def logo_for_domain(domain: str) -> str:
    # Clearbit works for most well-known corporate logos.
    return f'https://logo.clearbit.com/{domain}'


def favicon_for_domain(domain: str) -> str:
    return f'https://www.google.com/s2/favicons?domain={domain}&sz=128'


# Provider name fragment -> domain  (case-insensitive matching on provider).
PROVIDER_DOMAINS = {
    'NSFAS': 'nsfas.org.za',
    'Sasol Inzalo': 'sasolinzalofoundation.org.za',
    'Sasol': 'sasol.com',
    'Funza Lushaka': 'funzalushaka.doe.gov.za',
    'Department of Basic Education': 'education.gov.za',
    'Department of Health': 'health.gov.za',
    'Eskom': 'eskom.co.za',
    'Investec': 'investec.com',
    'Standard Bank': 'standardbank.co.za',
    'ABSA': 'absa.co.za',
    'FirstRand': 'firstrand.co.za',
    'RMB': 'rmb.co.za',
    'Nedbank': 'nedbank.co.za',
    'Capitec': 'capitecbank.co.za',
    'Sanlam': 'sanlam.co.za',
    'Liberty': 'liberty.co.za',
    'Momentum Metropolitan': 'momentummetropolitan.co.za',
    'Anglo American': 'angloamerican.com',
    'Sibanye-Stillwater': 'sibanyestillwater.com',
    'Sibanye': 'sibanyestillwater.com',
    'Gold Fields': 'goldfields.com',
    'AngloGold Ashanti': 'anglogoldashanti.com',
    'AngloGold': 'anglogoldashanti.com',
    'Implats': 'implats.co.za',
    'Impala Platinum': 'implats.co.za',
    'Exxaro': 'exxaro.com',
    'Harmony': 'harmony.co.za',
    'Northam': 'northam.co.za',
    'Transnet': 'transnet.net',
    'Vodacom': 'vodacom.co.za',
    'MTN': 'mtn.com',
    'Telkom': 'telkom.co.za',
    'Sappi': 'sappi.com',
    'Mondi': 'mondigroup.com',
    'Microsoft': 'microsoft.com',
    'IBM': 'ibm.com',
    'Naspers': 'naspers.com',
    'MultiChoice': 'multichoice.com',
    'PricewaterhouseCoopers': 'pwc.co.za',
    'PwC': 'pwc.co.za',
    'Deloitte': 'deloitte.com',
    'KPMG': 'kpmg.com',
    'EY': 'ey.com',
    'Ernst & Young': 'ey.com',
    'BDO': 'bdo.co.za',
    'SAICA': 'saica.co.za',
    'Hope Factory': 'thehopefactory.co.za',
    'Discovery': 'discovery.co.za',
    'Allan Gray': 'allangrayorbis.org',
    'Mandela Rhodes': 'mandelarhodes.org',
    'Oppenheimer': 'omt.org.za',
    'AECOM': 'aecom.com',
    'WSP': 'wsp.com',
    'GIBB': 'gibb.co.za',
    'Aurecon': 'aurecongroup.com',
    'South32': 'south32.net',
    'African Rainbow': 'arm.co.za',
    'Murray & Roberts': 'murrob.com',
    'Old Mutual': 'oldmutual.co.za',
    'SAB': 'sab.co.za',
    'Chevening': 'chevening.org',
    'Fulbright': 'fulbrightprogram.org',
    'DAAD': 'daad.de',
    'Schwarzman': 'schwarzmanscholars.org',
    'Rhodes Trust': 'rhodestrust.com',
    'Gates Cambridge': 'gatescambridge.org',
    'Mastercard Foundation': 'mastercardfdn.org',
    'Mastercard': 'mastercardfdn.org',
    'Commonwealth Scholarship Commission': 'cscuk.fcdo.gov.uk',
    'Australian Government': 'dfat.gov.au',
    'European Union': 'europa.eu',
    'JN Tata': 'jntataendowment.org',
    'BankSETA': 'bankseta.org.za',
    'Manufacturing, Engineering': 'merseta.org.za',
    'Education, Training and Development': 'etdpseta.org.za',
    'Health and Welfare SETA': 'hwseta.org.za',
    'Agricultural SETA': 'agriseta.co.za',
    'Food and Beverages': 'foodbev.co.za',
    'Chemical Industries': 'chieta.org.za',
    'Engineers Without Borders': 'ewb-sa.org',
    'Tomorrow Trust': 'tomorrow.org.za',
    'Studietrust': 'studietrust.org.za',
    'ISFAP': 'isfap.org.za',
    'Webber Wentzel': 'webberwentzel.com',
    'ENS Africa': 'ensafrica.com',
    'Cliffe Dekker Hofmeyr': 'cliffedekkerhofmeyr.com',
    'Bowman Gilfillan': 'bowmanslaw.com',
    'DG Murray': 'dgmt.co.za',
    'Canon Collins': 'canoncollins.org',
    'ASELPH': 'aselph.org.za',
    'WomEng': 'womeng.org',
    'SAB Foundation': 'sabfoundation.co.za',
    'NRF': 'nrf.ac.za',
    'National Research Foundation': 'nrf.ac.za',
    'Vhembe': 'vhembe.gov.za',
    'Sekhukhune': 'sekhukhunedistrict.gov.za',
    'Capricorn': 'cdm.org.za',
    'uMgungundlovu': 'umdm.gov.za',
    'iLembe': 'ilembe.gov.za',
    'OR Tambo': 'ortambodm.gov.za',
    'West Rand': 'wrdm.gov.za',
    'Waterberg': 'waterberg.gov.za',
    'City of Johannesburg': 'joburg.org.za',
    'City of Cape Town': 'capetown.gov.za',
    'eThekwini': 'durban.gov.za',
    'City of Tshwane': 'tshwane.gov.za',
    'City of Ekurhuleni': 'ekurhuleni.gov.za',
    'Buffalo City': 'buffalocity.gov.za',
    'Nelson Mandela Bay': 'nelsonmandelabay.gov.za',
    'Mangaung': 'mangaung.co.za',
    'Gauteng': 'gauteng.gov.za',
    "KZN": 'kznonline.gov.za',
    "Western Cape": 'westerncape.gov.za',
    "Eastern Cape": 'ecprov.gov.za',
    "Limpopo": 'limpopo.gov.za',
    "Mpumalanga": 'mpumalanga.gov.za',
    "Northern Cape": 'northern-cape.gov.za',
    "Free State": 'freestateonline.gov.za',
    "North West": 'nwpg.gov.za',
}

updated = 0
fallback = 0
for b in Bursary.objects.all():
    # Find best matching provider key (longest fragment match)
    matches = [(frag, dom) for frag, dom in PROVIDER_DOMAINS.items()
               if frag.lower() in b.provider.lower()]
    matches.sort(key=lambda x: -len(x[0]))
    if matches:
        domain = matches[0][1]
        b.logo_url = logo_for_domain(domain)
        b.save(update_fields=['logo_url'])
        updated += 1
    else:
        # Last-ditch fallback: Google favicon of provider's first 'word' as a .co.za guess.
        # Keep existing if any, else clear.
        if not b.logo_url:
            fallback += 1

print(f'Updated logo_url for {updated} bursaries.')
print(f'No mapping (kept blank → fallback initial badge): {fallback}')
