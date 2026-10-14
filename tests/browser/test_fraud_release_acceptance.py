"""Opt-in cross-engine release acceptance for the actual FastAPI Fraud app.

Start the app and set FRAUD_E2E_BASE_URL, e.g.:
    python -m unittest discover -s tests/browser -p test_fraud_release_acceptance.py -v

No mocked production metrics are used for the ordinary browser matrix.
One separate, explicitly marked CSV-injection test uses a malicious test-only
label intercepted in the browser; it never changes source data.
"""

from __future__ import annotations

import csv
import io
import json
import os
import unittest
from pathlib import Path
from urllib.request import urlopen

BASE_URL = os.environ.get("FRAUD_E2E_BASE_URL", "").rstrip("/")


@unittest.skipUnless(BASE_URL, "set FRAUD_E2E_BASE_URL to a running fraud app")
class FraudReleaseAcceptance(unittest.TestCase):
    def test_three_browser_engines_and_exports(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            for engine in ("chromium", "firefox", "webkit"):
                browser = getattr(playwright, engine).launch(headless=True)
                try:
                    for width, height in ((1440, 900), (375, 812)):
                        with self.subTest(browser=engine, viewport=width):
                            context = browser.new_context(
                                viewport={"width": width, "height": height},
                                accept_downloads=True,
                            )
                            try:
                                page = context.new_page()
                                errors = []
                                page.on("pageerror", lambda exc: errors.append(str(exc)))
                                page.goto(
                                    BASE_URL + "/",
                                    wait_until="domcontentloaded",
                                    timeout=35000,
                                )
                                page.wait_for_function(
                                    "() => document.querySelector('#backend-pill')?.dataset.state === 'connected'",
                                    timeout=30000,
                                )
                                self.assertTrue(
                                    page.locator("#freshness-pill").inner_text().strip()
                                )

                                for name in (
                                    "overview", "trend", "amount", "customer", "geo",
                                    "behavior", "features", "model", "insights",
                                ):
                                    page.locator(f'[data-page="{name}"]').first.click()
                                    self.assertEqual(
                                        page.locator("#report-body .studio-screen").count(), 1
                                    )
                                    for mode in ("main", "support"):
                                        switch = page.locator(f'[data-visual-mode="{mode}"]')
                                        if switch.count():
                                            switch.click()
                                        self.assertEqual(
                                            page.locator("#report-body .visual-body").evaluate_all(
                                                "(xs)=>xs.filter(x=>!x.innerHTML.trim()).length"
                                            ), 0,
                                        )
                                        self.assertLessEqual(
                                            page.evaluate(
                                                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                                            ), 1,
                                        )

                                page.locator('[data-page="overview"]').first.click()
                                inspect = page.locator(".chart-inspect-btn").first
                                inspect.focus()
                                page.keyboard.press("Enter")
                                modal = page.locator("#detail-drawer")
                                self.assertTrue(modal.is_visible())
                                self.assertEqual(modal.get_attribute("aria-modal"), "true")
                                self.assertEqual(
                                    page.evaluate("document.activeElement.id"),
                                    "drawer-close",
                                )
                                page.keyboard.press("Tab")
                                self.assertEqual(
                                    page.evaluate("document.activeElement.id"),
                                    "drawer-close",
                                )
                                page.keyboard.press("Escape")
                                self.assertFalse(modal.is_visible())
                                self.assertTrue(
                                    page.evaluate(
                                        "document.activeElement.hasAttribute('data-chart-inspect')"
                                    )
                                )

                                page.locator('[data-page="amount"]').first.click()
                                with page.expect_download(timeout=15000) as download:
                                    page.locator("#csv-btn").click()
                                file = download.value
                                data = Path(file.path()).read_bytes()
                                self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
                                rows = list(csv.reader(io.StringIO(data.decode("utf-8-sig"))))
                                self.assertGreater(len(rows), 1)
                                self.assertIn("amount_band", rows[0])

                                page.locator('[data-page="model"]').first.click()
                                page.locator('[data-visual-mode="support"]').click()
                                self.assertTrue(
                                    page.locator(".model-calibration-warning").is_visible()
                                )
                                self.assertIn(
                                    "16 published validation thresholds",
                                    page.locator(".model-evidence-disclosure").inner_text(),
                                )
                                page.evaluate(
                                    "window.__printCount=0;window.print=()=>{window.__printCount++}"
                                )
                                page.locator("#pdf-btn").click()
                                self.assertGreater(
                                    page.evaluate("window.__printCount"), 0
                                )
                                if engine == "chromium" and width == 1440:
                                    pdf_bytes = page.pdf(format="A4", print_background=True)
                                    self.assertTrue(pdf_bytes.startswith(b"%PDF"))
                                    self.assertGreater(len(pdf_bytes), 10000)
                                self.assertEqual(errors, [])
                            finally:
                                context.close()
                finally:
                    browser.close()

    def test_csv_blocks_spreadsheet_formula_injection(self):
        from playwright.sync_api import sync_playwright

        with urlopen(BASE_URL + "/api/dashboard", timeout=20) as response:
            payload = json.load(response)
        # Deliberate security test fixture; not synthetic presentation data.
        payload["amount_bands"][0]["amount_band"] = "=2+3"

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                accept_downloads=True,
            )
            try:
                page = context.new_page()
                page.route(
                    "**/api/dashboard",
                    lambda route: route.fulfill(status=200, json=payload),
                )
                page.goto(BASE_URL + "/", wait_until="domcontentloaded")
                page.wait_for_function(
                    "() => document.querySelector('#backend-pill')?.dataset.state === 'connected'",
                    timeout=30000,
                )
                page.locator('[data-page="amount"]').first.click()
                with page.expect_download(timeout=15000) as download:
                    page.locator("#csv-btn").click()
                csv_text = Path(download.value.path()).read_bytes().decode("utf-8-sig")
                rows = list(csv.DictReader(io.StringIO(csv_text)))
                self.assertTrue(
                    any(row["amount_band"] == "'=2+3" for row in rows),
                    "Formula-prefixed text must be escaped before spreadsheet import",
                )
            finally:
                context.close()
                browser.close()
