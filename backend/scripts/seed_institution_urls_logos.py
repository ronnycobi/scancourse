"""
Populate each public SA university's official **undergraduate application URL**
and a publicly-hosted logo URL. Run idempotently.

Logos are CDN-served from each university's own site or Wikipedia commons —
they don't need to be downloaded; the app loads them at runtime.

Run:  python manage.py shell < scripts/seed_institution_urls_logos.py
"""
from apps.institutions.models import Institution

# short_name -> (apply URL, logo URL)
INSTITUTIONS: dict[str, tuple[str, str]] = {
    'UCT': (
        'https://applyonline.uct.ac.za/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/8/8c/UCT_logo.svg/1200px-UCT_logo.svg.png',
    ),
    'Wits': (
        'https://www.wits.ac.za/applications/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/c/c2/University_of_the_Witwatersrand_Logo.svg/1200px-University_of_the_Witwatersrand_Logo.svg.png',
    ),
    'UP': (
        'https://www.up.ac.za/online-application',
        'https://upload.wikimedia.org/wikipedia/en/thumb/d/d4/Universityofpretorialogo.png/220px-Universityofpretorialogo.png',
    ),
    'SU': (
        'https://www.sun.ac.za/english/maties/Pages/Apply.aspx',
        'https://upload.wikimedia.org/wikipedia/en/thumb/0/02/Stellenbosch_University_logo.png/180px-Stellenbosch_University_logo.png',
    ),
    'UJ': (
        'https://student.uj.ac.za/applyonline.aspx',
        'https://upload.wikimedia.org/wikipedia/en/thumb/0/0a/University_of_Johannesburg_logo.svg/1200px-University_of_Johannesburg_logo.svg.png',
    ),
    'UKZN': (
        'https://applications.ukzn.ac.za/Account/Login',
        'https://upload.wikimedia.org/wikipedia/en/thumb/3/35/UKZN_Logo.svg/1200px-UKZN_Logo.svg.png',
    ),
    'NWU': (
        'https://studies.nwu.ac.za/apply',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/NWU_-_North-West_University_logo.svg/1200px-NWU_-_North-West_University_logo.svg.png',
    ),
    'UFS': (
        'https://www.ufs.ac.za/apply',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/University_of_the_Free_State_logo.svg/1200px-University_of_the_Free_State_logo.svg.png',
    ),
    'NMU': (
        'https://www.mandela.ac.za/Apply',
        'https://upload.wikimedia.org/wikipedia/en/thumb/e/e2/Nelson_Mandela_University_logo.png/220px-Nelson_Mandela_University_logo.png',
    ),
    'Rhodes': (
        'https://www.ru.ac.za/admissionsuit/applications/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/d/d8/Rhodes_University_logo.svg/1200px-Rhodes_University_logo.svg.png',
    ),
    'UFH': (
        'https://www.ufh.ac.za/StudyatFortHare/Pages/Apply.aspx',
        'https://upload.wikimedia.org/wikipedia/en/thumb/4/4d/University_of_Fort_Hare_seal.png/220px-University_of_Fort_Hare_seal.png',
    ),
    'UWC': (
        'https://www.uwc.ac.za/study/applying-to-uwc',
        'https://upload.wikimedia.org/wikipedia/en/thumb/2/28/UWC_Logo.png/220px-UWC_Logo.png',
    ),
    'UL': (
        'https://www.ul.ac.za/index.php?Entity=Apply',
        'https://upload.wikimedia.org/wikipedia/en/thumb/c/c3/University_of_Limpopo_logo.png/220px-University_of_Limpopo_logo.png',
    ),
    'UMP': (
        'https://www.ump.ac.za/Apply',
        'https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/University_of_Mpumalanga_logo.png/220px-University_of_Mpumalanga_logo.png',
    ),
    'UNIVEN': (
        'https://www.univen.ac.za/apply/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/b/b1/University_of_Venda_logo.png/220px-University_of_Venda_logo.png',
    ),
    'UniZulu': (
        'https://www.unizulu.ac.za/admissions/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/c/c5/University_of_Zululand_Logo.png/220px-University_of_Zululand_Logo.png',
    ),
    'SMU': (
        'https://www.smu.ac.za/index.php/admission/',
        'https://www.smu.ac.za/wp-content/uploads/2018/03/SMU-Logo.png',
    ),
    'SPU': (
        'https://www.spu.ac.za/index.php/admissions/',
        'https://www.spu.ac.za/wp-content/uploads/2017/12/spu-logo.png',
    ),
    'CPUT': (
        'https://www.cput.ac.za/study/admissions/applications',
        'https://upload.wikimedia.org/wikipedia/en/thumb/2/25/CPUT_logo.png/220px-CPUT_logo.png',
    ),
    'DUT': (
        'https://www.dut.ac.za/admissions/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/4/4d/DUT_logo.png/220px-DUT_logo.png',
    ),
    'TUT': (
        'https://www.tut.ac.za/admissions',
        'https://upload.wikimedia.org/wikipedia/en/thumb/4/4f/TUT_logo.png/220px-TUT_logo.png',
    ),
    'MUT': (
        'https://www.mut.ac.za/admissions/',
        'https://www.mut.ac.za/wp-content/uploads/2020/03/MUT-LOGO.png',
    ),
    'VUT': (
        'https://www.vut.ac.za/apply/',
        'https://upload.wikimedia.org/wikipedia/en/thumb/3/3d/Vaal_University_of_Technology_logo.png/220px-Vaal_University_of_Technology_logo.png',
    ),
    'CUT': (
        'https://www.cut.ac.za/cms-apply',
        'https://www.cut.ac.za/sites/default/files/inline-images/cut-logo.png',
    ),
    'WSU': (
        'https://www.wsu.ac.za/index.php/admissions',
        'https://upload.wikimedia.org/wikipedia/en/thumb/3/31/Walter_Sisulu_University_logo.png/220px-Walter_Sisulu_University_logo.png',
    ),
}


updated = 0
not_found = []
for short, (url, logo) in INSTITUTIONS.items():
    inst = Institution.objects.filter(short_name__iexact=short).first()
    if not inst:
        not_found.append(short)
        continue
    inst.application_url = url
    inst.logo_url = logo
    inst.save()
    updated += 1

print(f'Updated apply URLs for {updated} institutions.')
if not_found:
    print(f'Not found: {not_found}')

# Verify by listing
for i in Institution.objects.all()[:5]:
    print(f'  {i.short_name}: {i.application_url}')
