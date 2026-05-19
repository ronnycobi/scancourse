"""
Plain-text legal policies served via API.
These are POPIA-aware drafts. Have a SA attorney review before going live.
"""

PRIVACY_POLICY = {
    'version': '1.0',
    'effective_date': '2025-01-01',
    'content': """
# Privacy Policy

**Effective: 1 January 2025 · Version 1.0**

Scancourse (Pty) Ltd ("we", "us", "Scancourse") is committed to protecting your personal information in accordance with the Protection of Personal Information Act, 2013 ("POPIA").

## 1. What we collect

- **Account information** — email, name, phone number, password (hashed)
- **Educational information** — grade, province, subjects, marks, APS score, school name
- **Profile information** — preferred field, dream career, study province
- **Documents you upload** — report cards, ID copies, proof of residence (encrypted at rest)
- **Usage data** — pages viewed, courses saved, AI chat history, application progress
- **Device data** — IP address, browser type, OS, device identifiers
- **Communications** — WhatsApp messages to and from our bot

## 2. Why we collect it

- To calculate your APS score and match you with eligible courses
- To recommend bursaries and accommodation relevant to you
- To support your university applications via our tracker
- To provide personalised AI guidance through Scan AI
- To send deadline reminders and important notifications
- To improve our service through anonymised analytics
- To comply with legal obligations

## 3. Lawful basis (POPIA s. 11)

We process your personal information based on:
- **Your consent** (which you can withdraw at any time)
- **Contract performance** — to deliver the service you signed up for
- **Legal obligations** — tax records, audit requirements
- **Legitimate interests** — fraud prevention, service improvement

## 4. Who we share it with

- **Bursary providers and institutions** — only with your explicit consent, when you apply
- **Service providers** — Twilio (WhatsApp), Google (Gemini AI), AWS (storage), all under data processing agreements
- **Authorities** — when legally compelled (court order, subpoena)

We do **NOT** sell your personal information.

## 5. International transfers

Some of our service providers (Google, AWS) may process data outside South Africa. We use providers with adequate data protection (EU adequacy / standard contractual clauses).

## 6. How long we keep it

- **Active accounts** — for as long as you use Scancourse
- **Deleted accounts** — purged within 30 days of confirmed deletion request
- **Anonymised analytics** — kept indefinitely
- **Legal records** — kept for 5 years (tax, audit)

## 7. Your rights under POPIA

- **Access** — get a copy of all your data (request via app or email)
- **Correction** — fix inaccurate data
- **Deletion** — close your account and erase your data
- **Objection** — opt out of marketing or specific processing
- **Withdraw consent** — at any time, without affecting prior processing
- **Data portability** — export your data in a machine-readable format
- **Lodge a complaint** — with the Information Regulator (https://inforegulator.org.za)

To exercise any right, email **privacy@scancourse.co.za** or use the in-app settings.

## 8. Security

- Documents encrypted at rest with AES-128 (Fernet)
- All connections use TLS 1.2+
- Passwords hashed with PBKDF2
- Access logs maintained for sensitive operations
- Regular security audits

## 9. Children

Scancourse is intended for learners aged 16+. If you are under 18, we require a parent or guardian's consent for processing of your personal information.

## 10. Updates to this policy

We will notify you of material changes via email or in-app notification at least 30 days before they take effect.

## 11. Contact us

**Information Officer:** info-officer@scancourse.co.za
**Privacy queries:** privacy@scancourse.co.za
**Postal address:** [Registered office address]
""",
}


TERMS_OF_SERVICE = {
    'version': '1.0',
    'effective_date': '2025-01-01',
    'content': """
# Terms of Service

**Effective: 1 January 2025 · Version 1.0**

By using Scancourse, you agree to these terms.

## 1. Who we are

Scancourse (Pty) Ltd is a South African company providing educational guidance services to learners.

## 2. Your account

- You must provide accurate information
- You are responsible for keeping your password secure
- One person, one account
- Minimum age: 16 (under-18s need parental consent)

## 3. What we do

We provide:
- APS calculation from report cards (manual or OCR)
- Course and institution matching
- Bursary discovery
- Accommodation listings
- AI-powered career guidance via Gemini

## 4. What we don't do

- We are **not** a university or educational institution
- We **don't** guarantee admission to any course
- Course requirements and bursary deadlines are sourced from public information and may be outdated — always verify with the institution directly
- We **don't** provide legal, medical, or financial advice

## 5. Acceptable use

You agree NOT to:
- Misrepresent your identity or marks
- Upload fraudulent documents
- Scrape or copy our content for commercial use
- Attempt to break our security
- Harass other users (e.g. via Roommate Finder messaging)

## 6. AI disclaimer

Scan AI uses Google Gemini. Replies are AI-generated and may be inaccurate. Always verify important information with primary sources (institution websites, NSFAS, SAQA).

## 7. Liability

We provide Scancourse "as is". To the extent permitted by law:
- We are not liable for indirect, consequential, or special damages
- Our total liability is capped at fees you've paid to us in the past 12 months (currently R0 for free users)
- We are not liable for third-party content (institution info, bursary listings)

## 8. Termination

You may close your account at any time. We may suspend or close accounts that violate these terms.

## 9. Governing law

These terms are governed by the laws of the Republic of South Africa. Disputes go to courts in [Gauteng/Western Cape].

## 10. Changes

We may update these terms; we'll notify you 30 days in advance for material changes.

## 11. Contact

**legal@scancourse.co.za**
""",
}


COOKIE_POLICY = {
    'version': '1.0',
    'effective_date': '2025-01-01',
    'content': """
# Cookie Policy

**Effective: 1 January 2025 · Version 1.0**

Scancourse uses cookies and similar technologies to make our service work and to improve it.

## What we use

| Cookie | Purpose | Duration |
|---|---|---|
| `sessionid` | Keeps you signed in | Session |
| `csrftoken` | Security (prevents cross-site attacks) | 1 year |
| `_ga` | Google Analytics (anonymous usage stats) | 2 years |

## Your choices

You can disable analytics cookies in **Settings → Privacy** at any time. Essential cookies (login, security) cannot be disabled because the app won't work without them.

Most browsers also let you block cookies entirely — though this may break functionality.

## Contact

Questions? **privacy@scancourse.co.za**
""",
}
