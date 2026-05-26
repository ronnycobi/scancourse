"""
Canonical legal text for Scancourse.

This file is the single source of truth for legal copy. The same content
is mirrored into frontend/lib/presentation/screens/legal/legal_screen.dart
so it renders identically inside the mobile app and on the public website
(/legal/<slug>/).

Bump VERSION + EFFECTIVE_DATE whenever you change wording.
"""

VERSION = '1.0'
EFFECTIVE_DATE = '2026-05-26'
EFFECTIVE_DATE_HUMAN = '26 May 2026'


_HEADER = f'**Effective: {EFFECTIVE_DATE_HUMAN} · Version {VERSION}**'


PRIVACY_POLICY = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Privacy Policy

{_HEADER}

This policy explains what personal information Scancourse collects, why we
collect it, and what we do with it. We aim to comply with the Protection
of Personal Information Act, 2013 (POPIA).

## Information We Collect

- **Account info**: name, email, password (hashed), phone number, grade,
  province.
- **Academic info**: subjects, marks, calculated APS — you can delete
  these any time.
- **Profile preferences**: preferred field, dream career, preferred
  study province.
- **Profile photo**: stored on your device only — never uploaded to our
  servers.
- **Saved items + applications**: courses, bursaries, accommodation you
  save or track.
- **Usage signals**: course views (used to power "Similar students also
  viewed").

## Why We Collect It

- Personalised course and bursary recommendations
- Save your progress between sessions
- Improve the app over time
- Send important notifications (deadline reminders, application status)

## What We Do NOT Do

- We do not sell your personal information to anyone.
- We do not share your marks with universities or bursary providers
  without your consent.
- We do not use your data for advertising profiling.

## Who Sees Your Data

- You — always, via the Profile screen.
- Scancourse staff — only when troubleshooting an issue you've reported.
- Service providers we use to run the app (hosting, email, error
  monitoring) under strict confidentiality.

## Your Rights Under POPIA

You can at any time:

- Access the personal information we hold about you.
- Correct or update it via Edit Profile.
- Delete your account and all associated data (30-day grace period).
- Object to processing (we'll explain the consequences).
- Lodge a complaint with the Information Regulator
  (https://inforegulator.org.za).

To exercise any right, email **info@scancourse.co.za** or use the in-app
Settings → Privacy & Data section.

## Data Retention

- Active accounts: we keep your data while your account is open.
- Deleted accounts: we erase personal data within 30 days. Aggregated,
  anonymised statistics may be retained.

## Security

- Passwords are stored hashed (we never see them in plain text).
- Tokens are stored in your device's secure storage.
- API traffic uses HTTPS in production.
- Access logs maintained for sensitive operations.

## Children's Privacy

Scancourse is intended for students 13 and older. If we learn that we
have collected data on a child under 13 without verifiable parental
consent, we will delete it.

## Changes to This Policy

If we make a material change, we'll notify you in-app before it takes
effect.

## Contact

- Privacy questions: info@scancourse.co.za
- Information Officer: info@scancourse.co.za
- Website: https://scancourse.co.za
- Information Regulator of South Africa: https://inforegulator.org.za
""",
}


TERMS_OF_SERVICE = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Terms & Conditions

{_HEADER}

By using Scancourse you agree to these terms. If you don't agree, please
don't use the app.

## 1. Who We Are

Scancourse is a South African app helping Grade 11 and 12 learners find
courses, bursaries and accommodation, calculate their APS, and plan their
post-school journey.

## 2. Your Account

- You must provide accurate information about yourself.
- You're responsible for keeping your password secure.
- One person, one account.
- Minimum age: 13 (under-18s should have a parent or guardian's
  permission).

## 3. What We Do

We provide:

- APS calculation from report cards (OCR or manual entry).
- Course and institution matching.
- Bursary discovery.
- Accommodation listings.
- AI-powered career guidance.

## 4. What We Don't Do

- We are **not** a university or educational institution.
- We **don't** guarantee admission to any course.
- Course requirements and bursary deadlines come from public sources and
  may be outdated — always verify with the institution directly.
- We **don't** provide legal, medical, or financial advice.

## 5. Acceptable Use

You agree NOT to:

- Misrepresent your identity or marks.
- Upload fraudulent documents.
- Scrape or copy our content for commercial use.
- Try to break our security.
- Pretend to be a different person, or create multiple accounts.

## 6. AI Features

Our AI assistant and AI-powered "Why didn't I qualify?" / improvement
plans use third-party language models. Replies are AI-generated and
**may be inaccurate**. Always verify important information with primary
sources (institution websites, NSFAS, SAQA).

## 7. Third-Party Links

We link to university and bursary application sites. We don't control
those sites, and we're not responsible for what happens once you leave
Scancourse.

## 8. Changes to These Terms

We may update these Terms. We'll show a notice in the app when we do.
Continued use after a change means you accept the new Terms.

## 9. Termination

We can suspend or close accounts that violate these Terms. You can
delete your own account at any time from Settings → Privacy & Data.

## 10. Limitation of Liability

Scancourse is provided "as is". We can't guarantee that the information
is complete, current or error-free. Use the app to inform your choices,
not to replace official advice from universities, bursary providers or
career counsellors.

## 11. Governing Law

These Terms are governed by South African law. Disputes will be
resolved in South African courts.

## 12. Contact

For questions about these Terms:

- **info@scancourse.co.za**
- Website: https://scancourse.co.za
""",
}


COOKIE_POLICY = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Cookie Policy

{_HEADER}

Scancourse uses cookies and similar technologies to make our service
work and to improve it.

## What We Use

| Cookie | Purpose | Duration |
|---|---|---|
| `sessionid` | Keeps you signed in on the website | Session |
| `csrftoken` | Security (prevents cross-site attacks) | 1 year |
| `_ga` | Anonymous usage stats (if analytics is enabled) | 2 years |

## Your Choices

You can disable analytics cookies in **Settings → Privacy** at any time.
Essential cookies (login, security) cannot be disabled because the app
won't work without them.

Most browsers also let you block cookies entirely — though this may
break functionality.

## Mobile App

The Scancourse mobile app does **not** use cookies. It uses secure
device storage to keep you signed in.

## Contact

Questions? **info@scancourse.co.za**
""",
}


ACCEPTABLE_USE = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Acceptable Use Policy

{_HEADER}

To keep Scancourse a useful, respectful space for everyone, please
follow these rules.

## Do

- Use Scancourse to research your study options.
- Provide accurate information about your marks and preferences.
- Report bugs or wrong data (e.g. wrong bursary deadline) so we can fix
  them.
- Keep your account credentials private.

## Don't

- Scrape, mass-download or republish our data.
- Submit false marks to game course matching.
- Pretend to be a different person, or create multiple accounts.
- Use bots, scripts or automation against the app or API.
- Try to access other users' accounts or data.
- Reverse-engineer the app to bypass features.
- Use Scancourse for any unlawful purpose under South African law.

## Reporting Violations

If you notice another user breaking these rules, email
**info@scancourse.co.za**. Include screenshots and the user's email or
username if you have it.

## Consequences

Violations may result in your account being suspended or permanently
closed. Serious violations (fraud, identity theft, computer-misuse
offences) will be reported to law-enforcement.
""",
}


ABOUT = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# About Scancourse

{_HEADER}

Scancourse helps Grade 11 and 12 learners in South Africa figure out:

- Which APS they currently have.
- Which courses they qualify for.
- Which bursaries they should apply to.
- Where to live near their chosen university.

We built Scancourse because applying for university in South Africa is
stressful, fragmented across dozens of websites, and full of jargon.
We pull it all into one place.

## What's in the App

- **APS Calculator** — scan your report card or type marks in.
- **Courses** — 1,600+ active programmes across all 25 SA public
  universities.
- **Bursaries** — 110+ NSFAS, government, corporate, foundation and
  international scholarships.
- **Accommodation** — NSFAS-accredited residences near each university.
- **Applications tracker** — manage where you've applied and the
  deadlines.
- **AI Assistant** — help with motivation letters and study questions.

## What Scancourse Is Not

- We are not a university. We don't admit students.
- We are not NSFAS, the Department of Education, or any bursary provider.
- We don't guarantee admission — only the institution can do that.

## Who Built This

Scancourse is built by a small team in South Africa. If you find a bug
or want to suggest something, email **info@scancourse.co.za** or visit
https://scancourse.co.za.

## Open About Limitations

- Bursary deadlines move every year. We update them, but always verify
  with the provider.
- Course data is scraped from public university sites. Some entries may
  be incomplete.
- The APS calculator gives an estimate — each university computes its
  own.
""",
}


DISCLAIMER = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Disclaimer

{_HEADER}

## Information Accuracy

Scancourse aggregates publicly-available information about universities,
courses, bursaries and student accommodation in South Africa. While we
work hard to keep it accurate and current, we make **no guarantees**
about completeness, currency or fitness for any specific purpose.

## Always Verify Before You Apply

- **Course details, fees and entry requirements**: confirm with the
  university directly.
- **Bursary deadlines and eligibility**: confirm with the bursary
  provider before applying.
- **Accommodation listings and prices**: confirm with the residence
  operator.

## Not Financial or Legal Advice

Nothing in Scancourse is financial, legal, or career advice. For loans,
contracts, or major decisions, consult a qualified advisor.

## Third-Party Sites

We link to external university and bursary application portals. We
don't control those sites. We're not responsible for content, accuracy,
security or any consequences of using them.

## Match Quality

"Qualify" badges are based on the structured data we have (your APS,
subject marks, preferred field). We can't verify household income,
race-based eligibility, citizenship requirements, or special clauses —
always read the full T&Cs on the provider's site.

## AI-Generated Content

Insights generated by our AI features (improvement plan, course gap
explainer, motivation letter helper) are estimates based on language
models. They may be inaccurate. Always verify with the institution.

## Liability

To the maximum extent permitted by South African law, Scancourse and
its operators are not liable for any loss, damage or missed opportunity
arising from your use of the app.

## Reporting Errors

Found a wrong deadline, missing bursary, or out-of-date course? Email
**info@scancourse.co.za** and we'll fix it.
""",
}


CONTACT = {
    'version': VERSION,
    'effective_date': EFFECTIVE_DATE,
    'content': f"""
# Contact Us

{_HEADER}

We'd love to hear from you — whether it's a bug report, a feature
request, a question about your APS, or feedback on the app.

## General Enquiries

- **Email:** info@scancourse.co.za
- **Website:** https://scancourse.co.za

## What to Email Us About

- Account or login issues
- Wrong course or bursary information you've spotted
- Bug reports (please include your phone model + what happened)
- Feedback or feature requests
- Privacy or data-protection questions (POPIA)
- Reporting another user who's breaking the rules

## Response Time

We're a small team. We try to reply within 2 business days. For urgent
admissions questions, please contact the relevant university directly —
we can't process applications on their behalf.

## Looking for Something Else?

- **About the app:** see the *About Scancourse* page.
- **How we handle your data:** see the *Privacy Policy*.
- **What the app can and can't promise:** see the *Disclaimer*.
""",
}


# Used by views.py for HTML rendering
ALL_DOCS = {
    'privacy': ('Privacy Policy', PRIVACY_POLICY),
    'terms': ('Terms & Conditions', TERMS_OF_SERVICE),
    'cookies': ('Cookie Policy', COOKIE_POLICY),
    'acceptable-use': ('Acceptable Use Policy', ACCEPTABLE_USE),
    'about': ('About Scancourse', ABOUT),
    'disclaimer': ('Disclaimer', DISCLAIMER),
    'contact': ('Contact Us', CONTACT),
}
