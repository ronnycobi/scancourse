# Scancourse 📚

> **Scan your results. Plan your future.**

South Africa's student guidance platform — helping Grade 11, Grade 12, and gap-year learners find courses, bursaries, and accommodation based on their APS score.

---

## Stack

| Layer | Technology |
|---|---|
| Mobile/Web Frontend | Flutter 3.x (Android, iOS, Web) |
| Backend API | Django 4.2 + Django REST Framework |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 |
| Background Jobs | Celery + Celery Beat |
| OCR | Tesseract + OpenCV |
| AI Assistant | OpenAI GPT-4o-mini |
| Scrapers | Python + BeautifulSoup + APScheduler |
| Web Server | Nginx |
| Containerisation | Docker + Docker Compose |

---

## Features

- **Report Card Scanner** — Upload PDF/image or use camera. OCR extracts subjects and marks automatically.
- **APS Calculator** — South African APS calculation (NSC standard), excludes Life Orientation.
- **Course Matching** — Matches courses to your APS with Eligible / Stretch / Alternative categories.
- **Institution Finder** — All 26 public universities + TVET + private colleges.
- **Bursary Discovery** — NSFAS, Sasol, Investec, government, and more with deadlines.
- **Accommodation Listings** — NSFAS-accredited student accommodation near institutions.
- **AI Assistant (Scan AI)** — GPT-powered chat with full platform context injection.
- **Push Notifications** — Deadline alerts via Firebase Cloud Messaging.
- **Automated Scrapers** — Scheduled scraping of institutions, courses, and bursaries.

---

## Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Flutter SDK 3.x

### 1. Clone and configure
```bash
git clone <repo>
cd scancourse
cp backend/.env.example backend/.env
# Edit backend/.env with your OpenAI API key
```

### 2. Start all services
```bash
docker-compose up --build
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- Django API on port 8000
- Celery worker + beat
- Scraper service

### 3. Seed initial data
```bash
docker-compose exec backend python scripts/seed_data.py
```

### 4. Access the API
- API: http://localhost:8000/api/v1/
- Swagger UI: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/

Default admin: `info@scancourse.co.za` / `changeme123`

### 5. Run Flutter app
```bash
cd frontend
flutter pub get
flutter run
```

---

## Project Structure

```
scancourse/
├── backend/                    # Django API
│   ├── apps/
│   │   ├── users/              # Auth, profiles, saved items
│   │   ├── institutions/       # Universities, TVET, private colleges
│   │   ├── courses/            # Courses + offerings + APS matching
│   │   ├── bursaries/          # Bursary listings
│   │   ├── accommodation/      # Student accommodation
│   │   ├── deadlines/          # Application deadlines
│   │   ├── ocr/                # Report OCR + APS calculation
│   │   ├── ai_assistant/       # GPT chat sessions
│   │   └── notifications/      # Push notifications
│   ├── scancourse/             # Django project settings
│   └── scripts/                # Seed data scripts
├── frontend/                   # Flutter app
│   └── lib/
│       ├── core/               # Theme, routes, constants
│       ├── data/               # Models, repositories, API client
│       ├── presentation/       # Screens + widgets
│       └── providers/          # Riverpod state
├── scrapers/                   # Python scrapers
│   ├── universities/           # SA institution scraper
│   ├── bursaries/              # Bursary scraper
│   └── scheduler.py            # APScheduler cron runner
├── nginx/                      # Nginx config
├── docker-compose.yml          # Development stack
├── docker-compose.prod.yml     # Production stack
└── .env.prod.example           # Production env template
```

---

## API Overview

| Endpoint | Description |
|---|---|
| `POST /api/v1/auth/register/` | Register new student |
| `POST /api/v1/auth/login/` | Login, get JWT |
| `POST /api/v1/auth/google/` | Google OAuth login |
| `PATCH /api/v1/auth/onboarding/` | Complete onboarding |
| `POST /api/v1/ocr/upload/` | Upload report card (async OCR) |
| `POST /api/v1/ocr/manual/` | Submit marks manually |
| `GET /api/v1/ocr/aps/` | Get latest APS score |
| `GET /api/v1/courses/match/` | Get APS-matched courses |
| `GET /api/v1/bursaries/` | List bursaries with filters |
| `GET /api/v1/institutions/` | List institutions |
| `GET /api/v1/accommodation/` | List accommodation |
| `POST /api/v1/ai/chat/` | Chat with Scan AI |

---

## APS Calculation

South African National Senior Certificate (NSC) APS table:

| Mark % | APS Points |
|---|---|
| 80–100 | 7 |
| 70–79 | 6 |
| 60–69 | 5 |
| 50–59 | 4 |
| 40–49 | 3 |
| 30–39 | 2 |
| 0–29 | 1 |

Life Orientation is excluded from APS totals (as per NSC standards).

---

## Production Deployment

```bash
cp .env.prod.example .env.prod
# Fill in all production values

docker-compose -f docker-compose.prod.yml up --build -d
```

Ensure:
- SSL certificates in `nginx/ssl/`
- Firebase credentials JSON file
- AWS S3 bucket for media
- Sentry project for error tracking

---

## Environment Variables

See `.env.prod.example` for all required environment variables.

---

## Licence

Private. All rights reserved — Scancourse (Pty) Ltd.
