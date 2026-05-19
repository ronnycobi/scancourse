"""
HEAD/GET each institution + bursary URL and report status codes.

Run:  python manage.py shell < scripts/verify_urls.py
"""
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from apps.institutions.models import Institution
from apps.bursaries.models import Bursary

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) Scancourse URL verifier',
    'Accept': 'text/html,application/xhtml+xml,*/*',
}


def check(url: str) -> int:
    try:
        # Some sites reject HEAD — fall back to GET.
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if r.status_code in (405, 403) or r.status_code >= 500:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.status_code
    except requests.RequestException:
        return -1


def verify(rows):
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(check, url): (label, url) for label, url in rows}
        for f in as_completed(futures):
            label, url = futures[f]
            code = f.result()
            results.append((label, url, code))
    return results


print('=== UNIVERSITIES ===')
rows = [(i.short_name, i.application_url) for i in Institution.objects.exclude(application_url='').order_by('short_name')]
for label, url, code in sorted(verify(rows)):
    flag = '✓' if 200 <= code < 400 else '✗'
    print(f'  {flag} [{code:>3}]  {label:<10}  {url}')

print()
print('=== BURSARIES (top 30 by name) ===')
rows = [(b.name[:40], b.application_url) for b in Bursary.objects.filter(is_active=True).order_by('name')[:30]]
for label, url, code in sorted(verify(rows)):
    flag = '✓' if 200 <= code < 400 else '✗'
    print(f'  {flag} [{code:>3}]  {label:<40}  {url}')
