import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../core/theme/app_theme.dart';

/// Generic legal-document viewer. Accepts a doc key (terms/privacy/about/
/// acceptable-use) and renders the corresponding static text.
class LegalScreen extends StatelessWidget {
  final String docKey;

  const LegalScreen({super.key, required this.docKey});

  String get _title {
    switch (docKey) {
      case 'terms':
        return 'Terms & Conditions';
      case 'privacy':
        return 'Privacy Policy';
      case 'acceptable-use':
        return 'Acceptable Use Policy';
      case 'about':
        return 'About Scancourse';
      case 'disclaimer':
        return 'Disclaimer';
      default:
        return 'Legal';
    }
  }

  String get _body {
    switch (docKey) {
      case 'terms':
        return _terms;
      case 'privacy':
        return _privacy;
      case 'acceptable-use':
        return _acceptableUse;
      case 'about':
        return _about;
      case 'disclaimer':
        return _disclaimer;
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_title),
        leading: BackButton(onPressed: () => context.pop()),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 32),
        child: _RichLegalText(text: _body),
      ),
    );
  }
}

class _RichLegalText extends StatelessWidget {
  final String text;
  const _RichLegalText({required this.text});

  @override
  Widget build(BuildContext context) {
    final lines = text.split('\n');
    final spans = <Widget>[];
    for (final line in lines) {
      final trimmed = line.trim();
      if (trimmed.isEmpty) {
        spans.add(const SizedBox(height: 10));
      } else if (trimmed.startsWith('# ')) {
        spans.add(Padding(
          padding: const EdgeInsets.only(top: 4, bottom: 10),
          child: Text(trimmed.substring(2),
              style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppColors.textPrimary)),
        ));
      } else if (trimmed.startsWith('## ')) {
        spans.add(Padding(
          padding: const EdgeInsets.only(top: 14, bottom: 6),
          child: Text(trimmed.substring(3),
              style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w700,
                  color: AppColors.primary)),
        ));
      } else if (trimmed.startsWith('- ')) {
        spans.add(Padding(
          padding: const EdgeInsets.only(left: 8, bottom: 4),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('•  ',
                  style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary)),
              Expanded(
                child: Text(trimmed.substring(2),
                    style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textPrimary,
                        height: 1.5)),
              ),
            ],
          ),
        ));
      } else if (trimmed.startsWith('_') && trimmed.endsWith('_')) {
        spans.add(Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(trimmed.substring(1, trimmed.length - 1),
              style: const TextStyle(
                  fontSize: 12,
                  fontStyle: FontStyle.italic,
                  color: AppColors.textSecondary)),
        ));
      } else {
        spans.add(Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: Text(trimmed,
              style: const TextStyle(
                  fontSize: 13,
                  color: AppColors.textPrimary,
                  height: 1.55)),
        ));
      }
    }
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: spans);
  }
}

// ── Documents ───────────────────────────────────────────────────────────────

const String _lastUpdated = '_Last updated: 18 May 2026_';

const _terms = '''
# Terms & Conditions

$_lastUpdated

Welcome to Scancourse. By creating an account or using this app you agree to these Terms.

## 1. Who We Are
Scancourse is a South African study-pathways platform that helps prospective students discover courses, bursaries and student accommodation. We are not affiliated with NSFAS, any university, or any bursary provider unless we explicitly say so.

## 2. Your Account
- You must be 13 years or older to create an account.
- Information you provide (name, email, marks, dream career) must be accurate.
- You are responsible for keeping your password safe. We cannot access it on your behalf.
- One account per person. Don't share accounts.

## 3. How the App Works
- The APS calculator gives an estimate. Universities calculate their own APS — always check directly with the institution.
- Course recommendations are guidance, not a guarantee of admission.
- Bursary listings, deadlines and eligibility text are best-effort summaries. Always verify on the official bursary provider's site before applying.

## 4. What You Can Do
- Use Scancourse for personal study research.
- Apply to courses and bursaries via the official links we provide.
- Save items for your own reference.

## 5. What You Can't Do
- Scrape, copy or republish our data.
- Pretend to be someone else, or submit false marks.
- Use the app to harass other users or providers.
- Try to break our systems.

## 6. Third-Party Links
We link to university and bursary application sites. We don't control those sites, and we're not responsible for what happens once you leave Scancourse.

## 7. Changes to These Terms
We may update these Terms. We'll show a notice in the app when we do. Continued use after a change means you accept the new Terms.

## 8. Termination
We can suspend or close accounts that violate these Terms. You can delete your own account any time from the Profile screen.

## 9. Limitation of Liability
Scancourse is provided "as is". We can't guarantee that the information is complete, current or error-free. Use the app to inform your choices, not to replace official advice from universities, bursary providers or career counsellors.

## 10. Governing Law
These Terms are governed by South African law. Disputes will be resolved in South African courts.

## 11. Contact
For questions about these Terms: legal@scancourse.co.za
''';

const _privacy = '''
# Privacy Policy

$_lastUpdated

This policy explains what personal information Scancourse collects, why we collect it, and what we do with it. We aim to comply with the Protection of Personal Information Act, 2013 (POPIA).

## Information We Collect
- **Account info**: name, email, password (hashed), phone number, grade, province.
- **Academic info**: subjects, marks, calculated APS — you can delete these any time.
- **Profile preferences**: preferred field, dream career, preferred study province.
- **Profile photo**: stored on your device only — never uploaded to our servers.
- **Saved items + applications**: courses, bursaries, accommodation you save or track.
- **Usage signals**: course views (used to power "Similar students also viewed").

## Why We Collect It
- Personalised course and bursary recommendations
- Save your progress between sessions
- Improve the app over time
- Send important notifications (deadline reminders, application status)

## What We Do NOT Do
- We do not sell your personal information to anyone.
- We do not share your marks with universities or bursary providers without your consent.
- We do not use your data for advertising profiling.

## Who Sees Your Data
- You — always, via the Profile screen.
- Scancourse staff — only when troubleshooting an issue you've reported.
- Service providers we use to run the app (hosting, email, error monitoring) under strict confidentiality.

## Your Rights Under POPIA
You can at any time:
- Access the personal information we hold about you.
- Correct or update it via Edit Profile.
- Delete your account and all associated data.
- Object to processing (we'll explain the consequences).
- Lodge a complaint with the Information Regulator (inforegulator.org.za).

## Data Retention
- Active accounts: we keep your data while your account is open.
- Deleted accounts: we erase personal data within 30 days. Aggregated, anonymised statistics may be retained.

## Security
- Passwords are stored hashed (we never see them in plain text).
- Tokens are stored in your device's secure storage.
- API traffic uses HTTPS in production.

## Children's Privacy
Scancourse is intended for students 13 and older. If we learn that we have collected data on a child under 13 without verifiable parental consent, we will delete it.

## Changes to This Policy
If we make a material change, we'll notify you in-app before it takes effect.

## Contact
- Privacy questions: privacy@scancourse.co.za
- Information Officer: privacy-officer@scancourse.co.za
- Information Regulator of South Africa: inforegulator.org.za
''';

const _acceptableUse = '''
# Acceptable Use Policy

$_lastUpdated

To keep Scancourse a useful, respectful space for everyone, please follow these rules.

## Do
- Use Scancourse to research your study options.
- Provide accurate information about your marks and preferences.
- Report bugs or wrong data (e.g. wrong bursary deadline) so we can fix them.
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
If you notice another user breaking these rules, email abuse@scancourse.co.za. Include screenshots and the user's email/username if you have it.

## Consequences
Violations may result in your account being suspended or permanently closed. Serious violations (fraud, identity theft, computer-misuse offences) will be reported to law-enforcement.
''';

const _about = '''
# About Scancourse

Scancourse helps Grade 11 and 12 learners in South Africa figure out:
- Which APS they currently have
- Which courses they qualify for
- Which bursaries they should apply to
- Where to live near their chosen university

We built Scancourse because applying for university in South Africa is stressful, fragmented across dozens of websites, and full of jargon. We pull it all into one place.

## What's in the App
- **APS Calculator** — scan your report card or type marks in
- **Courses** — all 1,600+ active programmes across all 25 SA public universities
- **Bursaries** — 110+ NSFAS, government, corporate, foundation and international scholarships
- **Accommodation** — NSFAS-accredited residences near each university
- **Applications tracker** — manage where you've applied and the deadlines
- **AI Assistant** — help with motivation letters and study questions

## What Scancourse Is Not
- We are not a university. We don't admit students.
- We are not NSFAS, the Department of Education, or any bursary provider.
- We don't guarantee admission — only the institution can do that.

## Who Built This
Scancourse is built by a small team in South Africa. If you find a bug or want to suggest something, email hello@scancourse.co.za.

## Open About Limitations
- Bursary deadlines move every year. We update them, but always verify with the provider.
- Course data is scraped from public university sites. Some entries may be incomplete.
- The APS calculator gives an estimate — each university computes its own.
''';

const _disclaimer = '''
# Disclaimer

$_lastUpdated

## Information Accuracy
Scancourse aggregates publicly-available information about universities, courses, bursaries and student accommodation in South Africa. While we work hard to keep it accurate and current, we make **no guarantees** about completeness, currency or fitness for any specific purpose.

## Always Verify Before You Apply
- **Course details, fees and entry requirements**: confirm with the university directly.
- **Bursary deadlines and eligibility**: confirm with the bursary provider before applying.
- **Accommodation listings and prices**: confirm with the residence operator.

## Not Financial or Legal Advice
Nothing in Scancourse is financial, legal, or career advice. For loans, contracts, or major decisions, consult a qualified advisor.

## Third-Party Sites
We link to external university and bursary application portals. We don't control those sites. We're not responsible for content, accuracy, security or any consequences of using them.

## Match Quality
- "Qualify" badges are based on the structured data we have (your APS, subject marks, preferred field). We can't verify household income, race-based eligibility, citizenship requirements, or special clauses — always read the full T&Cs on the provider's site.

## Liability
To the maximum extent permitted by South African law, Scancourse and its operators are not liable for any loss, damage or missed opportunity arising from your use of the app.

## Reporting Errors
Found a wrong deadline, missing bursary, or out-of-date course? Email corrections@scancourse.co.za and we'll fix it.
''';
