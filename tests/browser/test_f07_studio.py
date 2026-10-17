"""Opt-in real Chromium acceptance for the NEXUS Decision Studio route.

Requires a real local FastAPI instance serving committed historical snapshots.
Not run in normal unit CI; browser workflow provisions Playwright explicitly.
"""
from __future__ import annotations

import os
import unittest

BASE_URL = os.getenv("FRAUD_E2E_BASE_URL", "").rstrip("/")


@unittest.skipUnless(BASE_URL, "Real local FRAUD_E2E_BASE_URL is required")
class HistoricalDecisionStudioBrowserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from playwright.sync_api import sync_playwright

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()

    def test_studio_route_and_historical_case_review_with_keyboard(self) -> None:
        context = self.browser.new_context(viewport={"width": 1440, "height": 900})
        self.addCleanup(context.close)
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(BASE_URL + "/studio?view=overview", wait_until="domcontentloaded")
        self.assertEqual(response.status, 200)
        page.wait_for_function(
            "() => document.getElementById('hero-title')?.textContent !== 'Loading analysis'",
            timeout=30000,
        )
        self.assertIn("Historical IEEE-CIS", page.locator("#studio-evidence-source").inner_text())
        page.locator("#tab-governance").click()
        page.locator("#historical-review-queue .studio-review-item").first.wait_for(timeout=30000)
        first = page.locator("#historical-review-queue .studio-review-item").first
        first.focus()
        page.keyboard.press("Enter")
        self.assertEqual(first.get_attribute("aria-pressed"), "true")
        detail = page.locator("#historical-review-detail").inner_text()
        self.assertIn("Uncalibrated model score", detail)
        self.assertIn("No individual action", detail)
        self.assertNotIn("is_fraud", detail)
        self.assertEqual(errors, [])

    def test_mobile_has_source_trust_and_direct_navigation(self) -> None:
        context = self.browser.new_context(viewport={"width": 375, "height": 812})
        self.addCleanup(context.close)
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(BASE_URL + "/", wait_until="domcontentloaded")
        self.assertEqual(response.status, 200)
        page.wait_for_function(
            "() => document.querySelector('#backend-pill')?.dataset.state === 'connected'",
            timeout=30000,
        )
        self.assertTrue(page.locator("#nexus-evidence-context").is_visible())
        self.assertIn("Historical", page.locator("#nexus-evidence-context").inner_text())
        link = page.get_by_role("link", name="Open historical Risk Decision Studio")
        self.assertEqual(link.get_attribute("href"), "/studio?view=overview")
        self.assertEqual(errors, [])
