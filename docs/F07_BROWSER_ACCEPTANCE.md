# F07/F08 — Historical real-browser acceptance

## Supported scope

The repository includes the nine-page NEXUS fraud report and a secondary
Decision Studio. The Decision Studio previously had static files but no
FastAPI route. This patch registers a working `GET /studio` route and links to
it from the main dashboard's header.

`.github/workflows/browser-acceptance.yml` creates a real local FastAPI server
with the committed historical IEEE-CIS snapshot, installs pinned Playwright
1.56.1 and Chromium, Firefox and WebKit, and runs **all three** opt-in
browser test modules:

- `tests/browser/test_fraud_dashboard.py`: interactive nine-page
  dashboard, filters, mobile, keyboard, threshold and error-retry behavior.
- `tests/browser/test_fraud_release_acceptance.py`: three-browser,
  desktop and mobile matrix, CSV/PDF and injection handling.
- `tests/browser/test_f07_studio.py`: actual Decision Studio route,
  source disclosure, bounded read-only historical case review via keyboard,
  375px source rail and no uncaught JavaScript errors.

A separate HTTP source contract smoke check rejects dashboard data
substituted for current/verified or live fraud traffic.

## CI reproduction

```bash
python -m pip install -r webapp/requirements.txt playwright==1.56.1
python -m playwright install --with-deps chromium firefox webkit
python -m uvicorn webapp.main:app --host 127.0.0.1 --port 8000
# In a second shell:
FRAUD_E2E_BASE_URL=http://127.0.0.1:8000 \
  python -m unittest discover -s tests/browser -p 'test_*.py' -v
```

The independent CI workflow triggers on `main` pushes touching the
browser workflow, tests or webapp, and supports opt-in manual reruns.
The browser CI does **not** access BigQuery, write historical data, train
ML models, store secrets, deploy Vercel or change authorization policies.

Passing browser tests on GitHub's Linux runner establishes *only* acceptance
for the exact tested snapshot-backed Git commit and test viewport scope.
Deployment SHA parity, protected preview auth, live BigQuery source
revalidation and full-model scientific acceptance remain separate.
