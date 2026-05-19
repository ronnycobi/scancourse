# Getting Course Data Into Scancourse

You have **3 working tools** for populating courses from any SA university. Pick the one that matches your situation.

---

## Tool 1: CSV Bulk Import (fastest, most reliable)

**Best for:** When you can copy course info from a prospectus / spreadsheet / website into a CSV.

### Steps

1. Copy `backend/scripts/sample_courses.csv` and edit it — one row per course
2. Required columns: `course_name, field, level`
3. Optional but recommended: `duration_years, fees_per_year, description, career_opportunities, salary_min, salary_max, institution_short_name, min_aps, application_deadline`

### Run

```bash
cd backend
DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py import_courses_csv path/to/your.csv

# Preview first without saving:
DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py import_courses_csv path/to/your.csv --dry-run
```

### Field reference

| field code | meaning |
|---|---|
| `engineering` | Engineering & Tech |
| `health` | Health Sciences |
| `business` | Business & Commerce |
| `law` | Law |
| `humanities` | Humanities & Social Sciences |
| `science` | Natural Sciences |
| `education` | Education |
| `arts` | Arts & Design |
| `agriculture` | Agriculture |
| `ict` | Information Technology |
| `built_environment` | Built Environment |

| level code | meaning |
|---|---|
| `certificate` | Higher Certificate |
| `diploma` | Diploma |
| `advanced_diploma` | Advanced Diploma |
| `degree` | Bachelor's degree |
| `honours` | Honours |
| `masters` | Masters |
| `phd` | Doctorate |
| `n1_n6` | N1–N6 (TVET) |
| `nc_v` | NC(V) (TVET) |

| institution_short_name | Currently in DB |
|---|---|
| UCT, Wits, UP, SU, UKZN, UJ, NMU, TUT, CPUT | Yes |
| Add more via Django admin → Institutions |

### Realistic time investment

| Source | Time |
|---|---|
| Manually typing into CSV | ~3 min per course |
| Copy from spreadsheet | ~30 sec per course |
| Top 50 UJ courses | ~2.5 hours |
| Top 50 courses × 5 unis | ~12 hours |

---

## Tool 2: AI Extractor (most flexible)

**Best for:** When the university has a public URL or PDF prospectus, and you don't want to manually type. Uses Gemini.

### Prerequisites

- Set `GEMINI_API_KEY` env var (free key from https://aistudio.google.com/apikey)

### Run from a URL

```bash
cd backend

# UJ programme finder
GEMINI_API_KEY="AIza..." \
  DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py extract_courses \
  --url https://www.uj.ac.za/study-at-uj/find-a-programme/ \
  --institution UJ \
  --dry-run

# Wits undergrad page
GEMINI_API_KEY="AIza..." \
  DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py extract_courses \
  --url https://www.wits.ac.za/undergraduate/ \
  --institution Wits

# UCT programme listing
GEMINI_API_KEY="AIza..." \
  DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py extract_courses \
  --url https://students.uct.ac.za/students/study/undergraduate \
  --institution UCT
```

### Run from a PDF prospectus

```bash
# Download the prospectus first, then:
.venv/bin/pip install PyPDF2

GEMINI_API_KEY="AIza..." \
  DJANGO_SETTINGS_MODULE=scancourse.settings.local \
  .venv/bin/python manage.py extract_courses \
  --pdf ~/Downloads/uct_prospectus_2025.pdf \
  --institution UCT
```

### How it works

1. Fetches URL or reads PDF text
2. Sends to Gemini with a structured extraction prompt
3. Gemini returns JSON: `[{name, field, level, min_aps, ...}, ...]`
4. Saves Course + CourseOffering records

### Tips

- **Always run `--dry-run` first** to preview what Gemini extracted
- **Use specific URLs** — programme listings work better than homepage
- **Cost:** ~R0.05–R0.30 per page extracted (with `gemini-1.5-flash`)
- **Quality:** ~85–95% accurate. You'll need to manually fix some

### Top URLs to extract from

| University | URL |
|---|---|
| UJ | https://www.uj.ac.za/study-at-uj/find-a-programme/ |
| Wits | https://www.wits.ac.za/undergraduate/ |
| UCT | https://students.uct.ac.za/students/study/undergraduate |
| UP | https://www.up.ac.za/programmes |
| SU | https://www.sun.ac.za/english/maties/programmes |
| UKZN | https://www.ukzn.ac.za/college-and-schools/ |
| TUT | https://www.tut.ac.za/student/qualification/all-faculties |

---

## Tool 3: Custom Scraper (most accurate per-uni)

**Best for:** When you want to scrape a specific university's site systematically.

I built one for **UJ** as the template. Path: `scrapers/universities/uj_scraper.py`.

### Run

```bash
cd scrapers
.venv/bin/pip install requests beautifulsoup4 lxml

# Test scrape (limit to 10 programmes)
python universities/uj_scraper.py --limit 10 --output uj_test.json

# Full scrape (~280 UJ programmes, ~10 min)
python universities/uj_scraper.py --output uj_all.json

# Push directly to API after scrape
python universities/uj_scraper.py \
  --import \
  --token "JWT_FROM_LOGIN" \
  --api-url http://localhost:8000/api/v1
```

### To build a scraper for another university

Use `uj_scraper.py` as a template. Each uni's HTML structure is different — you'll need to:

1. Find the programme index URL
2. Identify the link pattern for programme detail pages
3. Adjust the regex for APS, duration, faculty extraction

Realistic build time per uni: **~2–4 hours** if their site is well-structured, **~1 day** if it's JavaScript-heavy (then you need Selenium/Playwright).

---

## Recommended workflow for getting to 1,000 courses

### Week 1: Top 5 universities × manual CSV

- Pick UCT, Wits, UP, UJ, Stellenbosch (covers ~70% of demand)
- Get their **2025 prospectus PDFs** from each website
- For each: run `extract_courses --pdf` with Gemini
- Review output → fix obvious errors → import
- **Result:** ~250–400 courses

### Week 2: Next 10 universities × Gemini extraction

- UKZN, NMU, NWU, Rhodes, UFS, TUT, CPUT, DUT, VUT, UWC
- Run `extract_courses --url` on each programme page
- ~30–40 min per uni
- **Result:** another ~400 courses

### Week 3: Verification + corrections

- Open Django admin → review every course
- Fix APS numbers, deadlines, fees
- This is the **slow but mandatory** step — bad data kills user trust

### Month 2+: TVET colleges & private colleges

- ~50 TVETs, mostly use NQF level codes (n1_n6, nc_v)
- Private colleges: Boston, Damelin, Rosebank, Eduvos, etc.

---

## Realistic data acquisition cost

| Approach | Up-front time | Per-update time | Quality |
|---|---|---|---|
| Manual CSV | 2 weeks | 4 hrs/year | Highest — you control everything |
| Gemini extraction | 2 days | 1 hr/year | High — small AI errors creep in |
| Custom scrapers | 1 week setup | 1 day/year | Highest, but breaks when sites change |
| Buy data (Eduvitae) | 1 hr | R30k/year | Stale, often wrong |
| University partnerships | 6 months | Free | Authoritative |

**Recommended:** Start with manual + Gemini. Build university partnerships in parallel — they take time but eventually replace scraping entirely.

---

## What about non-course data?

The same approach works for:

- **Bursaries** → use `extract_courses` with the bursary website URL (you'd need a similar script for the bursary model)
- **Accommodation** → manual entry via admin or scrape from Spareroom / Property24
- **Institutions** → 26 SA universities, manual entry takes ~1 hr total

Want me to build:

1. A bursary scraper (for bursaries.co.za, ZABursaries)?
2. An accommodation scraper (Property24 student listings)?
3. A "Course data quality" admin dashboard showing missing fields?
4. A weekly Celery job to refresh course data automatically?

Just say which.
