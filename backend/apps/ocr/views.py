import os
import tempfile
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Report, Subject, APSResult
from .serializers import (
    ReportUploadSerializer, ReportSerializer, SubjectUpdateSerializer,
    APSResultSerializer, ManualEntrySerializer,
)
from .tasks import process_report
from .aps_calculator import calculate_aps
from . import gemini_vision


class ReportUploadView(generics.CreateAPIView):
    serializer_class = ReportUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    throttle_scope = 'ocr_upload'

    def perform_create(self, serializer):
        report = serializer.save(user=self.request.user)
        process_report.delay(report.id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        report = Report.objects.get(id=serializer.instance.id)
        return Response(ReportSerializer(report).data, status=status.HTTP_202_ACCEPTED)


class ReportListView(generics.ListAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user).prefetch_related('subjects', 'aps_result')


class ReportDetailView(generics.RetrieveAPIView):
    serializer_class = ReportSerializer

    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)


class SubjectVerifyView(APIView):
    def patch(self, request, report_id):
        try:
            report = Report.objects.get(id=report_id, user=request.user)
        except Report.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

        subjects_data = request.data.get('subjects', [])
        for item in subjects_data:
            try:
                subj = report.subjects.get(id=item['id'])
                subj.name = item.get('name', subj.name)
                subj.mark = item.get('mark', subj.mark)
                subj.is_verified = True
                subj.save()
            except Subject.DoesNotExist:
                continue

        # Recalculate APS after verification
        all_subjects = [{'name': s.name, 'mark': s.mark} for s in report.subjects.all()]
        aps_data = calculate_aps(all_subjects)
        APSResult.objects.update_or_create(
            report=report,
            defaults={
                'user': request.user,
                'total_aps': aps_data['total_aps'],
                'subjects_data': aps_data['subjects'],
            }
        )

        report.status = 'verified'
        report.save(update_fields=['status'])

        return Response(ReportSerializer(report).data)


class ManualEntryView(APIView):
    def post(self, request):
        serializer = ManualEntrySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subjects = serializer.validated_data['subjects']
        aps_data = calculate_aps(subjects)

        # "Edit Marks" / manual entry is the user's single authoritative
        # hand-entered record. Replace any prior manual entry (report is
        # null) so repeated edits don't pile up — and so an edit that
        # LOWERS a mark actually takes effect instead of an old, higher
        # manual row winning the best-mark merge.
        APSResult.objects.filter(
            user=request.user, report__isnull=True
        ).delete()
        aps_result = APSResult.objects.create(
            user=request.user,
            total_aps=aps_data['total_aps'],
            subjects_data=aps_data['subjects'],
        )

        return Response(APSResultSerializer(aps_result).data, status=status.HTTP_201_CREATED)


class APSHistoryView(generics.ListAPIView):
    serializer_class = APSResultSerializer

    def get_queryset(self):
        return APSResult.objects.filter(user=self.request.user)


class LatestAPSView(APIView):
    """
    Returns the user's BEST-MARKS-ACROSS-ALL-REPORTS snapshot.

    SA universities calculate APS from the highest mark for each subject
    across every sitting (NSC + supp + upgrades). This endpoint does the
    same so the app always reflects the strongest possible profile.
    """
    def get(self, request):
        from .aggregator import best_aps_for_user
        merged = best_aps_for_user(request.user)
        return Response({
            'id': None,
            'total_aps': merged['total_aps'],
            'subjects_data': merged['subjects'],
            'report_count': merged['report_count'],
            'source_reports': merged['source_reports'],
            'is_merged': merged['report_count'] > 1,
            'created_at': None,
        })


class APSJourneyView(APIView):
    """
    GET /api/v1/ocr/aps/journey/

    Returns the user's APS progression over time, plus growth metrics
    and an "unlocked courses" count comparing their first APS to their
    latest. Used by the APS Journey screen.

    Response shape:
      {
        "current_aps": 34,
        "growth": {
          "first_aps": 28,
          "latest_aps": 34,
          "delta": 6,
          "delta_label": "+6 APS",
          "since": "2026-02-12T...",
        },
        "timeline": [
          {"date": "...", "total_aps": 28, "source_id": 1},
          {"date": "...", "total_aps": 31, "source_id": 2},
          ...
        ],
        "subject_movers": [
          {"subject": "Mathematics", "old_mark": 55, "new_mark": 70, "delta": 15},
          ...top 3
        ],
        "courses_unlocked": {
          "first_count": 312,
          "latest_count": 487,
          "delta": 175,
        }
      }
    """
    def get(self, request):
        # Only real APS results — a total_aps of 0 means OCR couldn't read
        # marks, not an actual score. Including them would start the line
        # chart at a misleading 0 and inflate the growth delta.
        results = list(
            APSResult.objects.filter(user=request.user, total_aps__gt=0)
            .order_by('created_at')
        )
        if not results:
            return Response({
                'current_aps': 0,
                'timeline': [],
                'growth': None,
                'subject_movers': [],
                'courses_unlocked': None,
            })

        first = results[0]
        latest = results[-1]

        # Timeline
        timeline = [
            {
                'date': r.created_at.isoformat(),
                'total_aps': r.total_aps,
                'source_id': r.id,
            }
            for r in results
        ]

        # Growth
        growth = {
            'first_aps': first.total_aps,
            'latest_aps': latest.total_aps,
            'delta': latest.total_aps - first.total_aps,
            'delta_label': self._delta_label(latest.total_aps - first.total_aps),
            'since': first.created_at.isoformat(),
        }

        # Subject movers — compare first report's subjects to latest's
        subject_movers = self._compute_subject_movers(first, latest)

        # Courses unlocked — how many more they qualify for now
        from apps.courses.models import CourseOffering
        first_count = CourseOffering.objects.filter(
            min_aps__lte=first.total_aps).count()
        latest_count = CourseOffering.objects.filter(
            min_aps__lte=latest.total_aps).count()
        unlocked = {
            'first_count': first_count,
            'latest_count': latest_count,
            'delta': latest_count - first_count,
        }

        return Response({
            'current_aps': latest.total_aps,
            'growth': growth if len(results) > 1 else None,
            'timeline': timeline,
            'subject_movers': subject_movers,
            'courses_unlocked': unlocked if len(results) > 1 else None,
        })

    @staticmethod
    def _delta_label(delta: int) -> str:
        if delta > 0:
            return f'+{delta} APS'
        if delta < 0:
            return f'{delta} APS'
        return 'No change'

    @staticmethod
    def _compute_subject_movers(first, latest):
        """Top 3 subjects with the biggest mark improvement between the
        first and latest APS result."""
        def name_to_mark(result):
            out = {}
            for s in (result.subjects_data or []):
                if not isinstance(s, dict):
                    continue
                name = (s.get('normalized_name') or s.get('name') or '').strip()
                mark = s.get('mark')
                try:
                    mark = int(mark)
                except (TypeError, ValueError):
                    continue
                if name and 0 <= mark <= 100:
                    out[name] = mark
            return out

        first_subjects = name_to_mark(first)
        latest_subjects = name_to_mark(latest)
        movers = []
        for name, latest_mark in latest_subjects.items():
            old = first_subjects.get(name)
            if old is None:
                continue
            delta = latest_mark - old
            if delta > 0:
                movers.append({
                    'subject': name,
                    'old_mark': old,
                    'new_mark': latest_mark,
                    'delta': delta,
                })
        movers.sort(key=lambda m: m['delta'], reverse=True)
        return movers[:3]


class ImagePrecheckView(APIView):
    """
    Fast Gemini quality check BEFORE the user commits to an upload.
    Saves users from waiting 20s for OCR only to be told the photo was unusable.
    """
    parser_classes = (MultiPartParser, FormParser)
    throttle_scope = 'ocr_precheck'

    def post(self, request):
        f = request.FILES.get('file')
        if not f:
            return Response({'detail': 'file is required'}, status=400)
        if f.size > 20 * 1024 * 1024:
            return Response({'detail': 'File too large.'}, status=400)
        ext = (f.name.rsplit('.', 1)[-1] or '').lower()
        if ext not in ('pdf', 'jpg', 'jpeg', 'png', 'heic', 'webp'):
            return Response({'detail': 'Unsupported file type.'}, status=400)

        # Save to a temp file so Gemini can read it.
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
            for chunk in f.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name
        try:
            result = gemini_vision.precheck_image(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        # Derive a single "should upload" verdict for the client.
        result['should_upload'] = (
            result['is_report'] and result['marks_readable']
            and result['quality'] in ('good', 'glare')  # glare alone we still try
        )
        return Response(result)


class ImprovementPlanView(APIView):
    """
    Rules-first 3-action plan grounded in the user's actual subject marks
    and saved/recommended courses. Gemini optionally polishes the wording
    but the plan ALWAYS ships even when AI is unavailable — that way the
    user sees something concrete and useful even if the LLM is down.
    """
    throttle_scope = 'ai_plan'

    def get(self, request):
        from .aggregator import best_aps_for_user
        from apps.courses.models import Course

        merged = best_aps_for_user(request.user)
        if merged['total_aps'] == 0:
            return Response(
                {'detail': 'Upload a report or enter marks first.'},
                status=400,
            )

        # Look at the top APS-gap courses the user has shown interest in
        # (saved or interacted with), capped to keep the prompt small.
        # min_aps lives on CourseOffering (a course can be offered at many
        # institutions with different APS requirements) — annotate with
        # the cheapest entry to get a single number per course.
        from apps.users.models import SavedItem
        from django.db.models import Min
        saved_ids = list(
            SavedItem.objects
            .filter(user=request.user, item_type='course')
            .values_list('item_id', flat=True)[:8]
        )
        saved_courses = list(
            Course.objects.filter(id__in=saved_ids)
            .annotate(min_aps=Min('offerings__min_aps'))
            .values('name', 'min_aps', 'field')[:8]
        )

        # If the user hasn't saved anything yet, fall back to the lowest-
        # APS courses in their preferred field so the plan still has real
        # programmes to talk about instead of generic advice.
        user = request.user
        if not saved_courses:
            field = (getattr(user, 'preferred_field', '') or '').strip()
            qs = (
                Course.objects
                .annotate(min_aps=Min('offerings__min_aps'))
                .exclude(min_aps__isnull=True)
                .exclude(min_aps=0)
            )
            if field:
                qs = qs.filter(field__icontains=field.split(',')[0])
            saved_courses = list(
                qs.order_by('min_aps').values('name', 'min_aps', 'field')[:5]
            )

        grade = getattr(user, 'grade', '') or ''
        dream_career = getattr(user, 'dream_career', '') or ''
        preferred_field = getattr(user, 'preferred_field', '') or ''

        # Step 1 — deterministic plan from real data. Should ALWAYS
        # succeed, but if some unexpected shape blows it up we still
        # ship a safe minimal plan rather than 500ing the request.
        import logging
        logger = logging.getLogger(__name__)
        try:
            plan = _deterministic_plan(
                subjects=merged['subjects'],
                total_aps=merged['total_aps'],
                saved_courses=saved_courses,
                grade=grade,
                dream_career=dream_career,
                preferred_field=preferred_field,
            )
        except Exception as e:
            logger.exception('Deterministic plan failed: %s', e)
            plan = {
                'summary': f'You have {merged["total_aps"]} APS. '
                           'Save a few courses to get tailored next steps.',
                'actions': [{
                    'title': 'Browse courses',
                    'description':
                        'Open the courses tab and save 3-5 programmes that '
                        'match your interests so we can build a real plan.',
                    'impact': 'Save courses to start',
                }],
            }

        # Step 2 — optional Gemini polish. If it fails, return the rules-
        # based plan untouched so the user still sees something useful.
        try:
            polished = _polish_plan_with_ai(
                plan,
                subjects=merged['subjects'],
                total_aps=merged['total_aps'],
                grade=grade,
                dream_career=dream_career,
            )
            if polished is not None:
                plan = polished
        except Exception as e:
            logger.warning('Plan polish wrapper failed: %s', e)

        return Response({
            'total_aps': merged['total_aps'],
            'grade': grade,
            'plan': plan,
        })


# ── Deterministic plan builder ──────────────────────────────────────────
#
# The improvement plan used to be 100% Gemini-generated. When the LLM
# rate-limited, timed out, or returned malformed JSON, the user saw "AI
# coach is offline" with no real plan. The functions below build a
# concrete 3-action plan from the user's actual marks + saved courses
# WITHOUT calling any AI. _polish_plan_with_ai then optionally rewrites
# the descriptions in a warmer voice, but the rules-based plan is the
# floor that ships if the LLM is unavailable.


# APS band thresholds — same as APS_TABLE in aps_calculator.
_APS_THRESHOLDS = [30, 40, 50, 60, 70, 80]


def _next_aps_threshold(mark: int) -> int | None:
    """Lowest band threshold strictly above `mark`. None if at 80%+."""
    for t in _APS_THRESHOLDS:
        if mark < t:
            return t
    return None


def _scorable_subjects(subjects: list[dict]) -> list[dict]:
    """Subjects that actually contribute to APS — drops LO/AP rows."""
    from .aps_calculator import is_life_orientation, is_advanced_programme
    out = []
    for s in subjects or []:
        name = (s.get('name') or '').strip()
        mark = s.get('mark')
        if not name or not isinstance(mark, (int, float)):
            continue
        if is_life_orientation(name) or is_advanced_programme(name):
            continue
        out.append({
            'name': name,
            'mark': int(mark),
            'aps_points': int(s.get('aps_points') or 0),
        })
    return out


def _easiest_aps_gain(subjects: list[dict]) -> dict | None:
    """The subject closest to the next APS band threshold. Concrete
    payoff: improving by `gap` percentage points yields +1 APS."""
    best = None
    for s in subjects:
        next_t = _next_aps_threshold(s['mark'])
        if next_t is None:
            continue
        gap = next_t - s['mark']
        if best is None or gap < best['gap']:
            best = {
                'subject': s['name'],
                'current': s['mark'],
                'target': next_t,
                'gap': gap,
            }
    return best


def _qualifying_courses(saved_courses, total_aps) -> list[dict]:
    qualify = []
    for c in saved_courses:
        min_aps = c.get('min_aps')
        if isinstance(min_aps, (int, float)) and total_aps >= min_aps:
            qualify.append(c)
    return qualify


def _closest_stretch_course(saved_courses, total_aps) -> dict | None:
    """The saved course just out of reach — smallest positive APS gap."""
    best = None
    for c in saved_courses:
        min_aps = c.get('min_aps')
        if not isinstance(min_aps, (int, float)):
            continue
        gap = min_aps - total_aps
        if gap > 0 and (best is None or gap < best['gap']):
            best = {**c, 'gap': int(gap)}
    return best


def _deterministic_plan(
    *, subjects, total_aps, saved_courses, grade, dream_career,
    preferred_field,
):
    """Returns {'summary': str, 'actions': [{title, description, impact}, ...]}.

    Always succeeds — no network calls. The actions reference real subject
    names, real marks, real saved-course names so the advice is grounded."""
    marks_locked = grade in ('grade_12', 'gap_year', 'other')
    scorable = _scorable_subjects(subjects)
    qualify = _qualifying_courses(saved_courses, total_aps)
    stretch = _closest_stretch_course(saved_courses, total_aps)
    actions: list[dict] = []

    if marks_locked:
        # Action 1 — Apply now: focus on courses they already qualify for.
        if qualify:
            top = qualify[:3]
            names = ', '.join(c['name'] for c in top)
            actions.append({
                'title': 'Apply now',
                'description': (
                    f"You qualify for {len(qualify)} of your saved courses. "
                    f"Start with: {names}. Submit before deadlines close."
                ),
                'impact': f'{len(qualify)} match{"" if len(qualify) == 1 else "es"}',
            })
        elif stretch:
            actions.append({
                'title': 'Apply where you can',
                'description': (
                    f"None of your saved courses match your {total_aps} APS yet. "
                    f"{stretch['name']} is closest (needs {int(stretch['min_aps'])} APS). "
                    'Look for diploma equivalents at the same institution.'
                ),
                'impact': f"{stretch['gap']} APS short",
            })
        else:
            actions.append({
                'title': 'Find your matches',
                'description': (
                    f"Browse courses by your {total_aps} APS and save 3-5 you'd consider. "
                    'Once you save courses we can give targeted advice.'
                ),
                'impact': 'Save courses to start',
            })

        # Action 2 — Bursaries (NSFAS-first).
        nsfas_msg = (
            'NSFAS funds tuition + residence for SA citizens with household income below R350k. '
            'Apply at nsfas.org.za as soon as your matric results are out.'
        )
        actions.append({
            'title': 'Bursaries to chase',
            'description': nsfas_msg + (
                f' Also search private bursaries in {preferred_field.split(",")[0].strip()}.'
                if preferred_field else ''
            ),
            'impact': 'Funding first',
        })

        # Action 3 — Backup pathway (diploma / TVET / supplementary).
        if total_aps < 23:
            actions.append({
                'title': 'Backup pathway',
                'description': (
                    f"With {total_aps} APS, a TVET NC(V) Level 4 or a Higher Certificate "
                    'is a strong route in — finish it and bridge into a diploma or degree.'
                ),
                'impact': 'TVET → diploma → degree',
            })
        else:
            actions.append({
                'title': 'Backup pathway',
                'description': (
                    'If your top choice rejects you, take a diploma at the same university — '
                    'most universities allow bridging into a degree after one year of solid marks.'
                ),
                'impact': 'Diploma → degree in 4-5 yrs',
            })

        # Summary
        if qualify:
            summary = (
                f'You have {total_aps} APS and qualify for {len(qualify)} of your saved courses — '
                'time to apply.'
            )
        elif stretch:
            summary = (
                f"You have {total_aps} APS. {stretch['name']} is "
                f"{stretch['gap']} APS away — let's plan around that."
            )
        else:
            summary = (
                f'You have {total_aps} APS. Save a few courses you like so we can '
                'tailor your next steps.'
            )
    else:
        # Pre-matric — mark improvement is real leverage.
        easiest = _easiest_aps_gain(scorable)
        if easiest:
            actions.append({
                'title': 'Easiest APS gain',
                'description': (
                    f"Push {easiest['subject']} from {easiest['current']}% "
                    f"to {easiest['target']}% — only {easiest['gap']} percentage "
                    'points and you earn +1 APS in your weakest band.'
                ),
                'impact': '+1 APS',
            })

        if stretch and easiest:
            actions.append({
                'title': 'Biggest impact',
                'description': (
                    f"{stretch['name']} needs {int(stretch['min_aps'])} APS — "
                    f"you're {stretch['gap']} away. Lifting 2-3 subjects by one band each "
                    'should close the gap.'
                ),
                'impact': f"+{stretch['gap']} APS unlocks it",
            })
        elif scorable:
            # No saved course gap — pick the subject with highest *potential*
            # upside (lowest current mark, biggest room to grow).
            lowest = min(scorable, key=lambda s: s['mark'])
            actions.append({
                'title': 'Biggest impact',
                'description': (
                    f"{lowest['name']} is your lowest at {lowest['mark']}% — "
                    'every band you climb here is worth more APS than improving '
                    'a subject already in the 70s.'
                ),
                'impact': 'Highest ceiling',
            })

        # Backup pathway
        if dream_career:
            actions.append({
                'title': 'Backup pathway',
                'description': (
                    f"If {dream_career} stays out of reach, a TVET NC(V) Level 4 or "
                    'a Higher Certificate gets you in — finish strong and bridge into '
                    'your dream programme in year 2.'
                ),
                'impact': 'Plan B in place',
            })
        else:
            actions.append({
                'title': 'Backup pathway',
                'description': (
                    'A Higher Certificate (1 year) or TVET NC(V) Level 4 is a solid '
                    'alternative — both bridge into diplomas and degrees later.'
                ),
                'impact': 'Plan B in place',
            })

        summary = (
            f'You have {total_aps} APS with marks still moving. '
            'Two well-targeted subjects could change everything.'
        )

    return {
        'summary': summary[:280],
        'actions': [
            {
                'title': a['title'][:60],
                'description': a['description'][:280],
                'impact': a['impact'][:80],
            }
            for a in actions[:3]
        ],
    }


def _polish_plan_with_ai(
    plan, *, subjects, total_aps, grade, dream_career,
):
    """Optional pass — asks Gemini to rewrite description text in a
    warmer, more personalised voice while keeping the structure + facts.

    Returns the polished plan, or None on any error (caller keeps the
    deterministic plan). Never raises.
    """
    import json as _json
    import logging
    logger = logging.getLogger(__name__)

    if not gemini_vision.is_available():
        return None
    try:
        import google.generativeai as genai
        from django.conf import settings
        genai.configure(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "You are a warm South African student advisor. Rewrite ONLY the "
            "'description' field of each action below so it sounds personal "
            "and motivating. Keep all facts, numbers, course names, and "
            "subject names EXACTLY as given. Keep each description under "
            "240 chars. Return the SAME JSON shape.\n\n"
            f"Student context: {total_aps} APS, grade={grade}, "
            f"dream_career={dream_career!r}.\n\n"
            f"Plan:\n{_json.dumps(plan, ensure_ascii=False, indent=2)}\n\n"
            "Output ONLY the JSON object, no markdown fences."
        )
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            generation_config={'response_mime_type': 'application/json'},
        )
        resp = model.generate_content(prompt)
        import re as _re
        raw = _re.sub(r'^```(?:json)?\s*|\s*```$', '',
                      (resp.text or '').strip(), flags=_re.IGNORECASE)
        data = _json.loads(raw)
        polished_actions = []
        original_actions = plan['actions']
        for i, a in enumerate((data.get('actions') or [])[:len(original_actions)]):
            orig = original_actions[i]
            polished_actions.append({
                # Keep titles + impact verbatim — those are facts.
                'title': orig['title'],
                'description': str(a.get('description') or orig['description'])[:280],
                'impact': orig['impact'],
            })
        # If the LLM dropped actions, top them up from the original.
        for j in range(len(polished_actions), len(original_actions)):
            polished_actions.append(original_actions[j])
        return {
            'summary': str(data.get('summary') or plan['summary'])[:280],
            'actions': polished_actions,
        }
    except Exception as e:
        logger.warning('Plan polish failed (using rules-based plan): %s', e)
        return None
