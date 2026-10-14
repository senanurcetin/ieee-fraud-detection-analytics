"""Opt-in real-browser acceptance of the nine-page NEXUS fraud dashboard.

This suite does not run in default pytest/CI. Start the *real* FastAPI app with
a working reporting backend, then set FRAUD_E2E_BASE_URL. Missing report data
is a failure, not a synthetic success. Optional screenshots are never
automatically published to the project portfolio.
"""

import os
import unittest
from pathlib import Path

BASE_URL = os.environ.get("FRAUD_E2E_BASE_URL", "").rstrip("/")


@unittest.skipUnless(BASE_URL, "set FRAUD_E2E_BASE_URL to a running fraud dashboard")
class FraudNexusBrowserAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright

        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()

    def open_report(self, viewport, **options):
        context = self.browser.new_context(viewport=viewport, **options)
        self.addCleanup(context.close)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda exception: errors.append(str(exception)))
        page.goto(BASE_URL + "/", wait_until="domcontentloaded", timeout=30000)
        return page, errors

    def wait_for_report(self, page):
        page.wait_for_function(
            "() => document.querySelector('#backend-pill')?.dataset.state === 'connected'",
            timeout=30000,
        )
        page.locator("#report-body .kpi-card").first.wait_for(timeout=15000)

    def screenshot(self, page, filename):
        target = os.environ.get("E2E_SCREENSHOT_DIR")
        if target:
            output = Path(target)
            output.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output / filename), full_page=True, animations="disabled")

    def test_nine_pages_theme_and_desktop_capture(self):
        page, errors = self.open_report({"width": 1440, "height": 900})
        self.wait_for_report(page)
        self.assertEqual(page.locator("#page-nav .nav-btn").count(), 9)
        self.assertTrue(page.locator(".report-canvas").is_visible())
        self.assertEqual(page.locator('[data-page="overview"]').get_attribute("aria-current"), "page")

        for name in ("trend", "amount", "customer", "geo", "behavior", "features", "model", "insights"):
            page.locator(f'[data-page="{name}"]').click()
            self.assertEqual(page.locator(f'[data-page="{name}"]').get_attribute("aria-current"), "page")
            self.assertTrue(page.locator("#page-title").inner_text().strip())

        page.locator('[data-page="overview"]').click()
        page.locator("#theme-btn").click()
        self.assertTrue(page.locator("body").evaluate("node => node.classList.contains('light')"))
        self.assertEqual(page.locator("#theme-btn").inner_text(), "Dark Mode")
        page.locator("#theme-btn").click()
        self.assertFalse(page.locator("body").evaluate("node => node.classList.contains('light')"))
        self.screenshot(page, "fraud-nexus-desktop-1440.png")
        self.assertEqual(errors, [])

    def test_mobile_navigation_without_document_overflow(self):
        page, errors = self.open_report(
            {"width": 375, "height": 812}, is_mobile=True, has_touch=True
        )
        self.wait_for_report(page)
        self.assertLessEqual(
            page.evaluate("document.documentElement.scrollWidth"),
            page.evaluate("document.documentElement.clientWidth") + 1,
        )
        page.locator('[data-page="model"]').scroll_into_view_if_needed()
        page.locator('[data-page="model"]').click()
        self.assertEqual(page.locator('[data-page="model"]').get_attribute("aria-current"), "page")
        self.assertEqual(page.locator("#page-title").inner_text(), "Model Performance Analysis")
        self.assertTrue(page.locator("#report-body").is_visible())
        self.screenshot(page, "fraud-nexus-mobile-375.png")
        self.assertEqual(errors, [])

    def test_global_product_filter_and_reset_use_real_report_data(self):
        page, errors = self.open_report({"width": 1440, "height": 900})
        self.wait_for_report(page)
        product = page.locator("#product-filter")
        self.assertGreater(product.locator("option").count(), 1)
        self.assertEqual(product.input_value(), "All")
        product.select_option("C")
        self.assertEqual(product.input_value(), "C")
        self.assertIn("Product: C", page.locator("#active-filters").inner_text())

        page.locator("#clear-btn").click()
        self.assertEqual(product.input_value(), "All")
        self.assertIn("No filters", page.locator("#active-filters").inner_text())
        self.assertEqual(errors, [])

    def test_failed_dashboard_load_has_explicit_retry(self):
        page, errors = self.open_report({"width": 1280, "height": 800})
        # Reload with a deliberately unavailable dashboard endpoint. We only
        # assert the failure UI, not successful access to an unverified backend.
        page.route("**/api/dashboard", lambda route: route.fulfill(status=503, body="Unavailable"))
        page.reload(wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.querySelector('#backend-pill')?.dataset.state === 'unavailable'",
            timeout=15000,
        )
        self.assertEqual(page.locator("#state").get_attribute("data-state"), "error")
        self.assertTrue(page.locator("#retry-data-btn").is_visible())
        page.locator("#retry-data-btn").click()
        page.wait_for_function(
            "() => document.querySelector('#backend-pill')?.dataset.state === 'unavailable'",
            timeout=15000,
        )
        self.assertTrue(page.locator("#retry-data-btn").is_visible())
        self.assertEqual(errors, [])


    def test_nine_distinct_studios_and_supporting_charts(self):
        """Every studio must render genuine data at desktop and mobile widths."""
        for width, height in ((1440, 900), (375, 812)):
            with self.subTest(viewport=width):
                page, errors = self.open_report({"width": width, "height": height})
                self.wait_for_report(page)
                for name in (
                    "overview", "trend", "amount", "customer", "geo",
                    "behavior", "features", "model", "insights",
                ):
                    with self.subTest(viewport=width, workspace=name):
                        page.locator(f'[data-page="{name}"]').click()
                        self.assertEqual(page.locator("#report-body .studio-screen").count(), 1)
                        self.assertEqual(
                            page.locator("#report-body .visual-body").evaluate_all(
                                "(nodes) => nodes.filter(node => !node.innerHTML.trim()).length"
                            ),
                            0,
                            "An analytical chart must not be silently empty",
                        )
                        self.assertLessEqual(
                            page.evaluate(
                                "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                            ),
                            1,
                        )
                        button = page.locator('[data-visual-mode="support"]')
                        if button.count():
                            button.click()
                            self.assertGreater(page.locator("#report-body .visual-card").count(), 0)
                            self.assertEqual(
                                page.locator("#report-body .visual-body").evaluate_all(
                                    "(nodes) => nodes.filter(node => !node.innerHTML.trim()).length"
                                ),
                                0,
                            )
                            page.locator('[data-visual-mode="main"]').click()
                self.assertEqual(errors, [])

    def test_model_threshold_simulation_keeps_real_validation_feedback(self):
        page, errors = self.open_report({"width": 1440, "height": 900})
        self.wait_for_report(page)
        page.locator('[data-page="model"]').click()
        self.assertTrue(page.locator(".studio-model-simulator").is_visible())
        slider = page.locator("#threshold-slider")
        self.assertGreater(int(slider.get_attribute("max")), 3)
        slider.fill("3")
        page.wait_for_function(
            "() => document.querySelector('#threshold-slider')?.value === '3'"
        )
        self.assertEqual(page.locator("#threshold-summary .kpi-card").count(), 6)
        self.assertEqual(page.locator("#model-confusion .confusion-tile").count(), 4)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
