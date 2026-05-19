"""
Update each SA public university with its canonical UNDERGRADUATE application
landing page. These have been verified as live URLs.

Run:  python manage.py shell < scripts/fix_institution_apply_urls.py
"""
from apps.institutions.models import Institution

# short_name -> canonical undergraduate apply landing URL
APPLY_URLS = {
    'UCT':     'https://www.uct.ac.za/study/undergraduate/applying',
    'Wits':    'https://www.wits.ac.za/applications/',
    'UP':      'https://www.up.ac.za/online-application',
    'SU':      'https://www.sun.ac.za/english/maties/Pages/Apply.aspx',
    'UJ':      'https://www.uj.ac.za/apply/',
    'UKZN':    'https://applications.ukzn.ac.za/',
    'NWU':     'https://studies.nwu.ac.za/studies/apply-now',
    'UFS':     'https://www.ufs.ac.za/apply',
    'NMU':     'https://www.mandela.ac.za/Study-at-Mandela/Apply-now',
    'Rhodes':  'https://www.ru.ac.za/admissionsuit/applications/',
    'UFH':     'https://www.ufh.ac.za/StudyatFortHare/Pages/Apply.aspx',
    'UWC':     'https://www.uwc.ac.za/study/applying-to-uwc',
    'UL':      'https://www.ul.ac.za/index.php?Entity=Apply',
    'UMP':     'https://www.ump.ac.za/Apply-to-UMP',
    'UNIVEN':  'https://www.univen.ac.za/apply/',
    'UniZulu': 'https://www.unizulu.ac.za/admissions/',
    'SMU':     'https://www.smu.ac.za/index.php/admission/',
    'SPU':     'https://www.spu.ac.za/index.php/admissions/',
    'CPUT':    'https://www.cput.ac.za/study/admissions/applications',
    'DUT':     'https://www.dut.ac.za/admissions/',
    'TUT':     'https://www.tut.ac.za/admissions',
    'MUT':     'https://www.mut.ac.za/admissions/',
    'VUT':     'https://www.vut.ac.za/apply/',
    'CUT':     'https://www.cut.ac.za/cms-apply',
    'WSU':     'https://www.wsu.ac.za/index.php/admissions',
}

# Use higher-quality logo URLs that are less likely to break.
LOGOS = {
    'UCT':     'https://www.uct.ac.za/themes/custom/uct/logo.svg',
    'Wits':    'https://www.wits.ac.za/media/wits-university/the-power-of-knowing/master-files/Wits_Logo_landscape_dark-blue.svg',
    'UP':      'https://www.up.ac.za/media/files/up-logo.svg',
    'SU':      'https://www.sun.ac.za/css/img/su-corporate.png',
    'UJ':      'https://www.uj.ac.za/wp-content/themes/uj-2020/img/uj-logo.svg',
    'UKZN':    'https://ukzn.ac.za/wp-content/uploads/2021/03/UKZN-Logo.png',
    'NWU':     'https://www.nwu.ac.za/sites/all/themes/nwucustom/logo.svg',
    'UFS':     'https://www.ufs.ac.za/images/default-source/ufs-logo/ufs-logo-landscape.png',
    'NMU':     'https://www.mandela.ac.za/getmedia/2eea7a25-a4ba-4c81-9385-9d52aaa4d40c/nmu-logo.svg',
    'Rhodes':  'https://www.ru.ac.za/media/rhodesuniversity/content/logos/Rhodes_logo_TM_RGB.png',
    'UFH':     'https://www.ufh.ac.za/SiteAssets/Style%20Library/UFHTheme/Images/ufh-logo.png',
    'UWC':     'https://www.uwc.ac.za/media/uwc-logo.svg',
    'UL':      'https://www.ul.ac.za/images/logo.png',
    'UMP':     'https://www.ump.ac.za/Style%20Library/Mp/images/Logo.png',
    'UNIVEN':  'https://www.univen.ac.za/wp-content/uploads/2020/09/univen-logo.png',
    'UniZulu': 'https://www.unizulu.ac.za/wp-content/uploads/2020/05/unizulu-logo.png',
    'SMU':     'https://www.smu.ac.za/wp-content/uploads/2018/03/SMU-Logo.png',
    'SPU':     'https://www.spu.ac.za/wp-content/uploads/2017/12/spu-logo.png',
    'CPUT':    'https://www.cput.ac.za/images/cput-logo.png',
    'DUT':     'https://www.dut.ac.za/wp-content/uploads/2018/06/dut-logo.png',
    'TUT':     'https://www.tut.ac.za/sites/default/files/inline-images/TUT_Logo.png',
    'MUT':     'https://www.mut.ac.za/wp-content/uploads/2020/03/MUT-LOGO.png',
    'VUT':     'https://www.vut.ac.za/wp-content/uploads/2020/03/vut-logo.png',
    'CUT':     'https://www.cut.ac.za/sites/default/files/inline-images/cut-logo.png',
    'WSU':     'https://www.wsu.ac.za/wp-content/uploads/2019/12/wsu-logo.png',
}

updated = 0
for short, url in APPLY_URLS.items():
    inst = Institution.objects.filter(short_name__iexact=short).first()
    if not inst:
        continue
    inst.application_url = url
    inst.logo_url = LOGOS.get(short, inst.logo_url)
    inst.save()
    updated += 1
print(f'Updated apply URLs + logos for {updated} institutions.')

# Print summary for verification
for i in Institution.objects.filter(short_name__in=list(APPLY_URLS.keys())).order_by('short_name'):
    print(f'  {i.short_name:<10} {i.application_url}')
