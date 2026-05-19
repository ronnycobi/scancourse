"""Set logo_url for the major bursary providers. Idempotent."""
from apps.bursaries.models import Bursary

# Provider name fragment → logo URL (publicly hosted)
LOGOS = {
    'NSFAS':       'https://www.nsfas.org.za/content/images/nsfas_logo.png',
    'Funza Lushaka': 'https://www.funzalushaka.doe.gov.za/images/logo.png',
    'Sasol':       'https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Sasol_logo.svg/2560px-Sasol_logo.svg.png',
    'Eskom':       'https://upload.wikimedia.org/wikipedia/commons/thumb/9/95/Eskom_logo.svg/2560px-Eskom_logo.svg.png',
    'Investec':    'https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Investec_logo.svg/2560px-Investec_logo.svg.png',
    'Standard Bank': 'https://upload.wikimedia.org/wikipedia/commons/thumb/c/c0/Standard_Bank_logo.svg/2560px-Standard_Bank_logo.svg.png',
    'ABSA':        'https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Absa_Group_Limited_logo.svg/2560px-Absa_Group_Limited_logo.svg.png',
    'FirstRand':   'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3b/Firstrand-logo.png/1200px-Firstrand-logo.png',
    'Nedbank':     'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Nedbank_logo.svg/2560px-Nedbank_logo.svg.png',
    'Capitec':     'https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Capitec_Bank_logo.svg/2560px-Capitec_Bank_logo.svg.png',
    'Sanlam':      'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Sanlam_logo.svg/2560px-Sanlam_logo.svg.png',
    'Liberty':     'https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Liberty_Holdings_logo.svg/1200px-Liberty_Holdings_logo.svg.png',
    'Momentum':    'https://upload.wikimedia.org/wikipedia/commons/thumb/c/cb/Momentum_Metropolitan_logo.png/220px-Momentum_Metropolitan_logo.png',
    'Anglo American': 'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Anglo_American_plc_logo.svg/2560px-Anglo_American_plc_logo.svg.png',
    'Sibanye':     'https://upload.wikimedia.org/wikipedia/en/thumb/c/c4/Sibanye-Stillwater_logo.svg/220px-Sibanye-Stillwater_logo.svg.png',
    'Gold Fields': 'https://upload.wikimedia.org/wikipedia/en/thumb/d/dd/Gold_Fields_logo.svg/220px-Gold_Fields_logo.svg.png',
    'AngloGold':   'https://upload.wikimedia.org/wikipedia/en/thumb/d/da/AngloGold_Ashanti_logo.svg/220px-AngloGold_Ashanti_logo.svg.png',
    'Implats':     'https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/Impala_Platinum_logo.svg/220px-Impala_Platinum_logo.svg.png',
    'Exxaro':      'https://upload.wikimedia.org/wikipedia/en/thumb/9/93/Exxaro_logo.svg/220px-Exxaro_logo.svg.png',
    'Harmony':     'https://upload.wikimedia.org/wikipedia/en/thumb/2/2e/Harmony_Gold_logo.png/220px-Harmony_Gold_logo.png',
    'Northam':     'https://www.northam.co.za/images/logo.png',
    'Transnet':    'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Transnet_logo.svg/2560px-Transnet_logo.svg.png',
    'Vodacom':     'https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Vodacom_2017_logo.svg/2560px-Vodacom_2017_logo.svg.png',
    'MTN':         'https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/MTN_Logo.svg/2560px-MTN_Logo.svg.png',
    'Telkom':      'https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/Telkom_logo.svg/2560px-Telkom_logo.svg.png',
    'Sappi':       'https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Sappi_logo.svg/2560px-Sappi_logo.svg.png',
    'Mondi':       'https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Mondi_logo.svg/2560px-Mondi_logo.svg.png',
    'Microsoft':   'https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Microsoft_logo.svg/2560px-Microsoft_logo.svg.png',
    'IBM':         'https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/IBM_logo.svg/2560px-IBM_logo.svg.png',
    'Naspers':     'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Naspers_logo.svg/2560px-Naspers_logo.svg.png',
    'MultiChoice': 'https://upload.wikimedia.org/wikipedia/en/thumb/0/0c/MultiChoice_logo.png/220px-MultiChoice_logo.png',
    'PricewaterhouseCoopers': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/PricewaterhouseCoopers_Logo.svg/1200px-PricewaterhouseCoopers_Logo.svg.png',
    'Deloitte':    'https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Deloitte.svg/2560px-Deloitte.svg.png',
    'KPMG':        'https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/KPMG_logo.svg/2560px-KPMG_logo.svg.png',
    'EY':          'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/EY_logo_2019.svg/2560px-EY_logo_2019.svg.png',
    'Ernst & Young': 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/EY_logo_2019.svg/2560px-EY_logo_2019.svg.png',
    'BDO':         'https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/BDO_logo.svg/2560px-BDO_logo.svg.png',
    'SAICA':       'https://www.saica.org.za/Portals/0/_default/SAICA_Logo.png',
    'Discovery':   'https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Discovery_Limited_logo.svg/220px-Discovery_Limited_logo.svg.png',
    'Allan Gray':  'https://upload.wikimedia.org/wikipedia/en/thumb/1/1a/Allan_Gray_logo.svg/220px-Allan_Gray_logo.svg.png',
    'Mandela Rhodes': 'https://www.mandelarhodes.org/img/logo.svg',
    'Oppenheimer': 'https://www.omt.org.za/wp-content/uploads/2020/06/OMT-LOGO.png',
    'AECOM':       'https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/AECOM_logo.svg/2560px-AECOM_logo.svg.png',
    'WSP':         'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/WSP_Global_logo.svg/2560px-WSP_Global_logo.svg.png',
    'GIBB':        'https://www.gibb.co.za/images/logo.png',
    'Aurecon':     'https://upload.wikimedia.org/wikipedia/en/thumb/d/d9/Aurecon_logo.png/220px-Aurecon_logo.png',
    'South32':     'https://upload.wikimedia.org/wikipedia/en/thumb/4/4b/South32_logo.svg/220px-South32_logo.svg.png',
    'Murray & Roberts': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/5d/Murray_%26_Roberts_logo.png/220px-Murray_%26_Roberts_logo.png',
    'Old Mutual':  'https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Old_Mutual_logo.svg/2560px-Old_Mutual_logo.svg.png',
    'SAB':         'https://upload.wikimedia.org/wikipedia/en/thumb/0/0a/South_African_Breweries_logo.svg/220px-South_African_Breweries_logo.svg.png',
    'ARM':         'https://upload.wikimedia.org/wikipedia/en/thumb/9/9c/African_Rainbow_Minerals_logo.svg/220px-African_Rainbow_Minerals_logo.svg.png',
    'Chevening':   'https://www.chevening.org/wp-content/themes/chevening/img/chevening-logo.svg',
    'Fulbright':   'https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Fulbright_Program_logo.svg/220px-Fulbright_Program_logo.svg.png',
    'DAAD':        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/DAAD_Logo.svg/1200px-DAAD_Logo.svg.png',
    'Schwarzman':  'https://www.schwarzmanscholars.org/wp-content/themes/schwarzman/dist/img/logo.svg',
    'Rhodes Trust': 'https://www.rhodestrust.com/img/logo.png',
    'Gates Cambridge': 'https://upload.wikimedia.org/wikipedia/en/thumb/2/24/Gates_Cambridge_Trust_logo.png/220px-Gates_Cambridge_Trust_logo.png',
    'Mastercard':  'https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Mastercard-logo.png/640px-Mastercard-logo.png',
    'City of Johannesburg': 'https://upload.wikimedia.org/wikipedia/en/thumb/c/c9/City_of_Johannesburg_logo.png/220px-City_of_Johannesburg_logo.png',
    'City of Cape Town':    'https://upload.wikimedia.org/wikipedia/en/thumb/3/3f/City_of_Cape_Town_logo.png/220px-City_of_Cape_Town_logo.png',
    'eThekwini':   'https://upload.wikimedia.org/wikipedia/en/thumb/1/15/EThekwini_Metropolitan_Municipality_logo.png/220px-EThekwini_Metropolitan_Municipality_logo.png',
    'Tshwane':     'https://upload.wikimedia.org/wikipedia/en/thumb/9/9b/City_of_Tshwane_logo.png/220px-City_of_Tshwane_logo.png',
    'Ekurhuleni':  'https://upload.wikimedia.org/wikipedia/en/thumb/9/99/City_of_Ekurhuleni_logo.png/220px-City_of_Ekurhuleni_logo.png',
    'Nelson Mandela Bay': 'https://upload.wikimedia.org/wikipedia/en/thumb/5/5c/Nelson_Mandela_Bay_Municipality_logo.png/220px-Nelson_Mandela_Bay_Municipality_logo.png',
    'Vhembe':      'https://www.vhembe.gov.za/wp-content/uploads/logo.png',
    'Sekhukhune':  'https://www.sekhukhunedistrict.gov.za/images/logo.png',
}


updated = 0
for fragment, url in LOGOS.items():
    qs = Bursary.objects.filter(provider__icontains=fragment).filter(logo_url='')
    n = qs.update(logo_url=url)
    if n:
        updated += n

# Government / Department defaults
gov_logo = 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Coat_of_arms_of_South_Africa.svg/2560px-Coat_of_arms_of_South_Africa.svg.png'
n = Bursary.objects.filter(logo_url='').filter(
    provider__iregex=r'(department|government|provincial|premier|municipality|district|seta)',
).update(logo_url=gov_logo)
updated += n

print(f'Set logo_url for {updated} bursaries.')
print(f'Bursaries without logos: {Bursary.objects.filter(logo_url="").count()}')
