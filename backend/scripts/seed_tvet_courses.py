"""
Seed standard TVET (college) programmes for every public TVET college.

Reality check on SA TVET offerings:
  - NC(V) Level 2-4  (National Certificate Vocational) — 3-year programmes
    starting from Grade 9 pass. Equivalent to matric/NSC at Level 4.
  - N1-N6 (Nated / Report 191) — engineering & business studies, build up
    to a National N Diploma at N6.
  - Higher Certificates / Occupational Certificates — varies per college.

Every public TVET college offers most of the catalogue below. We seed one
Course record per programme (idempotent) and one CourseOffering per
(college × programme) so the existing matcher / recommender / browse all
work for TVET too. Min APS is set realistically:
  NC(V) Level 2: 0 (Grade 9 entry)
  NC(V) Level 4: 14 (just need a matric or NC(V) L3 equivalent)
  N1: 14, N4: 22, N6: 25

Run:  python manage.py shell < scripts/seed_tvet_courses.py
"""
from apps.institutions.models import Institution
from apps.courses.models import Course, CourseOffering

# Standard TVET catalogue: programmes offered across most public TVETs.
# (name, field, level, min_aps, duration_years, [subject_requirements])
TVET_PROGRAMMES = [
    # NC(V) — entry from Grade 9
    ('NC(V) Office Administration',                'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Finance, Economics and Accounting',    'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Management',                            'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Marketing',                             'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Tourism',                               'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Hospitality',                           'business',         'nc_v', 0, 3.0, []),
    ('NC(V) Information Technology and Computer Science', 'ict',        'nc_v', 0, 3.0, []),
    ('NC(V) Education and Development',             'education',        'nc_v', 0, 3.0, []),
    ('NC(V) Electrical Infrastructure Construction','engineering',      'nc_v', 0, 3.0, []),
    ('NC(V) Civil Engineering and Building Construction', 'engineering','nc_v', 0, 3.0, []),
    ('NC(V) Engineering and Related Design',        'engineering',      'nc_v', 0, 3.0, []),
    ('NC(V) Primary Agriculture',                   'agriculture',      'nc_v', 0, 3.0, []),
    ('NC(V) Safety in Society',                     'humanities',       'nc_v', 0, 3.0, []),
    ('NC(V) Process Plant Operations',              'engineering',      'nc_v', 0, 3.0, []),
    ('NC(V) Transport and Logistics',               'business',         'nc_v', 0, 3.0, []),

    # N1-N6 Engineering — entry varies, N4 typically requires matric
    ('N1-N3 Mechanical Engineering',                'engineering',      'n1_n6', 14, 1.0,
     [{'subject': 'Mathematics', 'min_level': 3}]),
    ('N1-N3 Electrical Engineering',                'engineering',      'n1_n6', 14, 1.0,
     [{'subject': 'Mathematics', 'min_level': 3}]),
    ('N1-N3 Civil Engineering',                     'engineering',      'n1_n6', 14, 1.0,
     [{'subject': 'Mathematics', 'min_level': 3}]),
    ('N4-N6 Mechanical Engineering',                'engineering',      'n1_n6', 22, 2.0,
     [{'subject': 'Mathematics', 'min_level': 4}]),
    ('N4-N6 Electrical Engineering',                'engineering',      'n1_n6', 22, 2.0,
     [{'subject': 'Mathematics', 'min_level': 4}]),
    ('N4-N6 Civil Engineering',                     'engineering',      'n1_n6', 22, 2.0,
     [{'subject': 'Mathematics', 'min_level': 4}]),

    # N4-N6 Business Studies
    ('N4-N6 Business Management',                   'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Financial Management',                  'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Marketing Management',                  'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Human Resource Management',             'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Public Management',                     'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Tourism',                               'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Hospitality and Catering Services',     'business',         'n1_n6', 18, 2.0, []),
    ('N4-N6 Educare',                               'education',        'n1_n6', 18, 2.0, []),
]


def run():
    tvets = list(Institution.objects.filter(institution_type='tvet', is_active=True))
    print(f'Found {len(tvets)} TVET colleges.')

    # Create / get Course rows
    course_lookup = {}
    for name, field, level, min_aps, dur, reqs in TVET_PROGRAMMES:
        course, _ = Course.objects.get_or_create(
            name=name, level=level,
            defaults={
                'field': field,
                'duration_years': dur,
                'description': f'TVET college programme: {name}.',
                'is_active': True,
            },
        )
        course_lookup[name] = course

    # Create offerings: every TVET college offers every programme
    created = 0
    for tvet in tvets:
        for name, field, level, min_aps, dur, reqs in TVET_PROGRAMMES:
            course = course_lookup[name]
            _, made = CourseOffering.objects.get_or_create(
                course=course,
                institution=tvet,
                campus='',
                defaults={
                    'min_aps': min_aps,
                    'subject_requirements': reqs,
                    'is_active': True,
                },
            )
            if made:
                created += 1

    print(f'Courses ensured:    {len(course_lookup)}')
    print(f'Offerings created:  {created}')
    print(f'TVET offerings total now: '
          f'{CourseOffering.objects.filter(institution__institution_type="tvet", is_active=True).count()}')


run()
