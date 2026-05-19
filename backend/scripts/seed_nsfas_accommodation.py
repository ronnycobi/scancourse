"""
Seed NSFAS-accredited accommodation for every SA public university.

Each university gets a mix of:
  • on-campus university-owned residences (all NSFAS-accredited by default)
  • NSFAS-accredited private residences nearby

Real residence names where known; generic "On-Campus Residence" placeholder
otherwise. Prices reflect 2024–2025 NSFAS caps (≤R55k/year ≈ R4 583/month
for off-campus; on-campus is usually R30–45k/year).

Run:  python manage.py shell < scripts/seed_nsfas_accommodation.py
"""
from apps.institutions.models import Institution
from apps.accommodation.models import Accommodation

DATA: dict[str, list[dict]] = {
    'UCT': [
        {'name': 'UCT Smuts Hall', 'distance_km': 0.1, 'room_type': 'single', 'price_per_month': 4200,
         'address': 'Main Campus, Rondebosch', 'province': 'WC', 'city': 'Cape Town',
         'description': 'Historic UCT men\'s residence on Main Campus. NSFAS-accredited.'},
        {'name': 'UCT Fuller Hall', 'distance_km': 0.1, 'room_type': 'single', 'price_per_month': 4200,
         'address': 'Main Campus, Rondebosch', 'province': 'WC', 'city': 'Cape Town',
         'description': 'Women\'s residence in the Jameson Hall complex.'},
        {'name': 'UCT Leo Marquard Hall', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 4200,
         'address': 'Upper Campus, Rondebosch', 'province': 'WC', 'city': 'Cape Town',
         'description': 'Mixed residence near upper campus library.'},
        {'name': 'CampusKey Rondebosch', 'distance_km': 0.6, 'room_type': 'single', 'price_per_month': 5500,
         'address': 'Main Road, Rondebosch', 'province': 'WC', 'city': 'Cape Town',
         'description': 'Private NSFAS-accredited res. En-suite rooms, gym, study pods.'},
    ],
    'Wits': [
        {'name': 'Wits Sunnyside Residence', 'distance_km': 0.4, 'room_type': 'single', 'price_per_month': 4500,
         'address': 'Yale Road, Braamfontein', 'province': 'GP', 'city': 'Johannesburg',
         'description': 'Women-only Wits residence with strong academic focus.'},
        {'name': 'Wits David Webster Hall', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 4500,
         'address': 'Yale Road, Braamfontein', 'province': 'GP', 'city': 'Johannesburg',
         'description': 'Mixed senior residence near East Campus.'},
        {'name': 'Wits Knockando Residence', 'distance_km': 0.5, 'room_type': 'sharing', 'price_per_month': 3700,
         'address': 'Empire Road, Parktown', 'province': 'GP', 'city': 'Johannesburg',
         'description': 'Mixed residence with sharing rooms, shuttle to campus.'},
        {'name': 'South Point Braamfontein', 'distance_km': 0.8, 'room_type': 'single', 'price_per_month': 4400,
         'address': 'De Korte Street, Braamfontein', 'province': 'GP', 'city': 'Johannesburg',
         'description': 'NSFAS-accredited private res across from Wits East Campus.'},
    ],
    'UP': [
        {'name': 'TuksRes Curlitzia', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 4300,
         'address': 'Hatfield Campus, Pretoria', 'province': 'GP', 'city': 'Pretoria',
         'description': 'UP women\'s residence on Hatfield campus.'},
        {'name': 'TuksRes Sonop', 'distance_km': 0.4, 'room_type': 'single', 'price_per_month': 4300,
         'address': 'Hatfield Campus, Pretoria', 'province': 'GP', 'city': 'Pretoria',
         'description': 'UP men\'s residence with strong tradition.'},
        {'name': 'CampusKey Hatfield', 'distance_km': 0.5, 'room_type': 'single', 'price_per_month': 5400,
         'address': 'Burnett Street, Hatfield', 'province': 'GP', 'city': 'Pretoria',
         'description': 'NSFAS-accredited private res next to UP main campus.'},
        {'name': 'South Point Hatfield', 'distance_km': 0.7, 'room_type': 'sharing', 'price_per_month': 3900,
         'address': 'Park Street, Hatfield', 'province': 'GP', 'city': 'Pretoria',
         'description': 'NSFAS sharing rooms with meals, shuttle, study lounge.'},
    ],
    'SU': [
        {'name': 'SU Wilgenhof', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4400,
         'address': 'Victoria Street, Stellenbosch', 'province': 'WC', 'city': 'Stellenbosch',
         'description': 'Stellenbosch men\'s residence with long history.'},
        {'name': 'SU Dagbreek', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 4400,
         'address': 'Merriman Avenue, Stellenbosch', 'province': 'WC', 'city': 'Stellenbosch',
         'description': 'Mixed Stellenbosch residence.'},
        {'name': 'Stellenbosch Student Living', 'distance_km': 0.8, 'room_type': 'sharing', 'price_per_month': 3800,
         'address': 'Bird Street, Stellenbosch', 'province': 'WC', 'city': 'Stellenbosch',
         'description': 'NSFAS-accredited private res.'},
    ],
    'UWC': [
        {'name': 'UWC Hector Petersen Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3600,
         'address': 'Robert Sobukwe Road, Bellville', 'province': 'WC', 'city': 'Cape Town',
         'description': 'On-campus UWC residence. NSFAS-accredited.'},
        {'name': 'UWC Coline Williams Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4100,
         'address': 'Robert Sobukwe Road, Bellville', 'province': 'WC', 'city': 'Cape Town',
         'description': 'UWC residence for senior students.'},
        {'name': 'UWC Disa Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3500,
         'address': 'Modderdam Road, Bellville', 'province': 'WC', 'city': 'Cape Town',
         'description': 'Mixed UWC residence with study facilities.'},
    ],
    'UKZN': [
        {'name': 'UKZN Mabel Palmer Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3900,
         'address': 'Howard College, Glenwood', 'province': 'KZN', 'city': 'Durban',
         'description': 'UKZN Howard College residence.'},
        {'name': 'UKZN Townhill Residence', 'distance_km': 0.4, 'room_type': 'sharing', 'price_per_month': 3500,
         'address': 'Pietermaritzburg Campus', 'province': 'KZN', 'city': 'Pietermaritzburg',
         'description': 'PMB campus residence.'},
        {'name': 'Respublica Durban', 'distance_km': 1.2, 'room_type': 'single', 'price_per_month': 4400,
         'address': 'Glenwood, Durban', 'province': 'KZN', 'city': 'Durban',
         'description': 'NSFAS-accredited private res near UKZN Howard College.'},
    ],
    'NWU': [
        {'name': 'NWU Heimat Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4200,
         'address': 'Hoffman Street, Potchefstroom', 'province': 'NW', 'city': 'Potchefstroom',
         'description': 'NWU Potchefstroom men\'s residence.'},
        {'name': 'NWU Karlien Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 4200,
         'address': 'Hoffman Street, Potchefstroom', 'province': 'NW', 'city': 'Potchefstroom',
         'description': 'NWU women\'s residence.'},
        {'name': 'NWU Mafikeng Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3600,
         'address': 'Mafikeng Campus', 'province': 'NW', 'city': 'Mafikeng',
         'description': 'On-campus residence at NWU Mafikeng.'},
    ],
    'UFS': [
        {'name': 'UFS Welwitschia Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4100,
         'address': 'Bloemfontein Campus', 'province': 'FS', 'city': 'Bloemfontein',
         'description': 'UFS women\'s residence on main campus.'},
        {'name': 'UFS Karee Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4100,
         'address': 'Bloemfontein Campus', 'province': 'FS', 'city': 'Bloemfontein',
         'description': 'UFS men\'s residence.'},
        {'name': 'South Point Bloemfontein', 'distance_km': 0.9, 'room_type': 'sharing', 'price_per_month': 3700,
         'address': 'Maitland Street, Bloemfontein', 'province': 'FS', 'city': 'Bloemfontein',
         'description': 'NSFAS-accredited private res.'},
    ],
    'NMU': [
        {'name': 'NMU Veritas Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4000,
         'address': 'South Campus, Port Elizabeth', 'province': 'EC', 'city': 'Gqeberha',
         'description': 'NMU South Campus residence.'},
        {'name': 'NMU Indwe Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3500,
         'address': 'North Campus, Port Elizabeth', 'province': 'EC', 'city': 'Gqeberha',
         'description': 'Mixed NMU residence.'},
        {'name': 'CampusKey Gqeberha', 'distance_km': 1.0, 'room_type': 'single', 'price_per_month': 5200,
         'address': 'Summerstrand, Gqeberha', 'province': 'EC', 'city': 'Gqeberha',
         'description': 'NSFAS-accredited private res near NMU.'},
    ],
    'Rhodes': [
        {'name': 'Rhodes Allan Webb Hall', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4500,
         'address': 'Prince Alfred Street, Makhanda', 'province': 'EC', 'city': 'Makhanda',
         'description': 'Rhodes mixed residence with dining hall.'},
        {'name': 'Rhodes Drostdy Hall', 'distance_km': 0.1, 'room_type': 'single', 'price_per_month': 4500,
         'address': 'High Street, Makhanda', 'province': 'EC', 'city': 'Makhanda',
         'description': 'Historic Rhodes residence.'},
    ],
    'UFH': [
        {'name': 'UFH Wesley Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3400,
         'address': 'Alice Campus', 'province': 'EC', 'city': 'Alice',
         'description': 'University of Fort Hare on-campus residence.'},
        {'name': 'UFH Beda Hall', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3800,
         'address': 'Alice Campus', 'province': 'EC', 'city': 'Alice',
         'description': 'UFH senior residence.'},
    ],
    'WSU': [
        {'name': 'WSU Sisa Dukashe Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Mthatha Campus', 'province': 'EC', 'city': 'Mthatha',
         'description': 'Walter Sisulu University on-campus residence.'},
        {'name': 'WSU Buffalo City Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Buffalo City Campus, East London', 'province': 'EC', 'city': 'East London',
         'description': 'NSFAS-accredited campus residence.'},
    ],
    'UL': [
        {'name': 'UL Onverwacht Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Turfloop Campus, Mankweng', 'province': 'LP', 'city': 'Polokwane',
         'description': 'University of Limpopo on-campus residence.'},
        {'name': 'UL New Block Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'Turfloop Campus, Mankweng', 'province': 'LP', 'city': 'Polokwane',
         'description': 'UL senior single rooms.'},
    ],
    'UNIVEN': [
        {'name': 'UNIVEN F1 Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Thohoyandou', 'province': 'LP', 'city': 'Thohoyandou',
         'description': 'University of Venda on-campus residence.'},
        {'name': 'UNIVEN F4 Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'Thohoyandou', 'province': 'LP', 'city': 'Thohoyandou',
         'description': 'Senior single rooms with study lounge.'},
    ],
    'UniZulu': [
        {'name': 'UniZulu Hall of Residence A', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'KwaDlangezwa', 'province': 'KZN', 'city': 'Richards Bay',
         'description': 'University of Zululand on-campus residence.'},
        {'name': 'UniZulu Hall of Residence B', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'KwaDlangezwa', 'province': 'KZN', 'city': 'Richards Bay',
         'description': 'Senior single rooms.'},
    ],
    'CPUT': [
        {'name': 'CPUT Catsville Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3500,
         'address': 'Bellville Campus', 'province': 'WC', 'city': 'Cape Town',
         'description': 'CPUT Bellville campus residence.'},
        {'name': 'CPUT District Six Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 4000,
         'address': 'District Six Campus', 'province': 'WC', 'city': 'Cape Town',
         'description': 'CPUT main campus residence in District Six.'},
        {'name': 'South Point CBD', 'distance_km': 1.5, 'room_type': 'sharing', 'price_per_month': 4000,
         'address': 'Bree Street, Cape Town CBD', 'province': 'WC', 'city': 'Cape Town',
         'description': 'NSFAS-accredited private res near CPUT District Six.'},
    ],
    'DUT': [
        {'name': 'DUT Steve Biko Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3500,
         'address': 'Steve Biko Campus, Durban', 'province': 'KZN', 'city': 'Durban',
         'description': 'DUT main campus residence.'},
        {'name': 'DUT Ritson Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 3900,
         'address': 'Ritson Campus, Durban', 'province': 'KZN', 'city': 'Durban',
         'description': 'DUT senior residence.'},
        {'name': 'Respublica Durban Point', 'distance_km': 1.0, 'room_type': 'single', 'price_per_month': 4300,
         'address': 'Point Road, Durban', 'province': 'KZN', 'city': 'Durban',
         'description': 'NSFAS-accredited private res.'},
    ],
    'TUT': [
        {'name': 'TUT Soshanguve Residence', 'distance_km': 0.3, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Soshanguve South Campus', 'province': 'GP', 'city': 'Pretoria',
         'description': 'TUT on-campus residence.'},
        {'name': 'TUT Pretoria Campus Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3800,
         'address': 'Staatsartillerie Road, Pretoria West', 'province': 'GP', 'city': 'Pretoria',
         'description': 'TUT Pretoria main campus residence.'},
        {'name': 'CampusKey Pretoria', 'distance_km': 1.5, 'room_type': 'single', 'price_per_month': 5000,
         'address': 'Sunnyside, Pretoria', 'province': 'GP', 'city': 'Pretoria',
         'description': 'NSFAS-accredited private res near TUT.'},
    ],
    'VUT': [
        {'name': 'VUT Andries Potgieter Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Andries Potgieter Boulevard, Vanderbijlpark', 'province': 'GP', 'city': 'Vanderbijlpark',
         'description': 'VUT main campus residence.'},
        {'name': 'VUT Sebokeng Residence', 'distance_km': 0.4, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'Sebokeng', 'province': 'GP', 'city': 'Vanderbijlpark',
         'description': 'NSFAS-accredited residence.'},
    ],
    'CUT': [
        {'name': 'CUT Excellentia Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3400,
         'address': 'President Brand Street, Bloemfontein', 'province': 'FS', 'city': 'Bloemfontein',
         'description': 'Central University of Technology residence.'},
        {'name': 'CUT Tia Nostra Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 3800,
         'address': 'Bloemfontein Campus', 'province': 'FS', 'city': 'Bloemfontein',
         'description': 'CUT senior residence.'},
    ],
    'MUT': [
        {'name': 'MUT Block A Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3200,
         'address': 'Umlazi V', 'province': 'KZN', 'city': 'Durban',
         'description': 'Mangosuthu University of Technology on-campus residence.'},
        {'name': 'MUT Block B Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3600,
         'address': 'Umlazi V', 'province': 'KZN', 'city': 'Durban',
         'description': 'MUT senior residence.'},
    ],
    'SMU': [
        {'name': 'SMU Dr Reddy Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3400,
         'address': 'Molotlegi Street, Ga-Rankuwa', 'province': 'GP', 'city': 'Pretoria',
         'description': 'Sefako Makgatho on-campus residence.'},
        {'name': 'SMU Senior Residence', 'distance_km': 0.2, 'room_type': 'single', 'price_per_month': 3800,
         'address': 'Molotlegi Street, Ga-Rankuwa', 'province': 'GP', 'city': 'Pretoria',
         'description': 'Single rooms for senior students.'},
    ],
    'SPU': [
        {'name': 'SPU Central Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3300,
         'address': 'Kimberley Campus', 'province': 'NC', 'city': 'Kimberley',
         'description': 'Sol Plaatje University on-campus residence.'},
        {'name': 'SPU City Campus Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'Kimberley CBD', 'province': 'NC', 'city': 'Kimberley',
         'description': 'NSFAS-accredited residence.'},
    ],
    'UMP': [
        {'name': 'UMP Mbombela Residence', 'distance_km': 0.2, 'room_type': 'sharing', 'price_per_month': 3400,
         'address': 'Mbombela Campus', 'province': 'MP', 'city': 'Mbombela',
         'description': 'University of Mpumalanga on-campus residence.'},
        {'name': 'UMP Siyabuswa Residence', 'distance_km': 0.3, 'room_type': 'single', 'price_per_month': 3700,
         'address': 'Siyabuswa Campus', 'province': 'MP', 'city': 'Siyabuswa',
         'description': 'NSFAS-accredited residence.'},
    ],
}


def run():
    summary = []
    for short, residences in DATA.items():
        uni = (
            Institution.objects.filter(short_name__iexact=short).first()
            or Institution.objects.filter(name__icontains=short).first()
        )
        if not uni:
            summary.append((short, 0, 0, 'NOT FOUND'))
            continue
        created = 0
        for r in residences:
            _, made = Accommodation.objects.get_or_create(
                name=r['name'],
                defaults={
                    **r,
                    'nearby_institution': uni,
                    'nsfas_accredited': True,
                    'is_active': True,
                },
            )
            if made:
                created += 1
        total = Accommodation.objects.filter(nearby_institution=uni, nsfas_accredited=True).count()
        summary.append((short, created, total, uni.name))
    return summary


results = run()
print(f"{'Code':<10} {'Added':>6} {'Total':>6}  Institution")
print('-' * 70)
for short, made, total, name in results:
    print(f'{short:<10} {made:>6} {total:>6}  {name}')
total_acc = Accommodation.objects.filter(nsfas_accredited=True).count()
print('-' * 70)
print(f'Grand total NSFAS-accredited residences: {total_acc}')
