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


    def test_rate_uncertainty_and_heatmap_support_are_explicit(self):
        """Reject the old visual failure: n=2 must not appear as a stable 100% heat cell."""
        page, errors = self.open_report({"width": 1440, "height": 900})
        self.wait_for_report(page)
        page.locator('[data-page="amount"]').click()
        page.locator("#amount-bar .rate-evidence-chart").wait_for(timeout=15000)
        self.assertGreater(page.locator("#amount-bar .rate-value").count(), 0)
        self.assertGreater(page.locator("#amount-bar .rate-denominator").count(), 0)
        self.assertTrue(page.locator("#amount-bar .rate-evidence-legend").is_visible())
        sparse = page.locator("#amount-heatmap .heat-insufficient")
        self.assertGreater(sparse.count(), 0, "Sparse cells must be explicitly identified")
        self.assertGreater(page.locator('#amount-heatmap [data-stat-status="observed"]').count(), 0)
        for cell in sparse.all():
            self.assertIn("n < 30", cell.inner_text())
            self.assertNotIn("%", cell.locator(".heat-value").inner_text())
            self.assertIn("observed rate", cell.get_attribute("data-tooltip"))
        self.assertEqual(errors, [])

    def test_customer_and_proxy_rates_show_measured_denominators(self):
        """Do not revert evidence charts to unlabeled percentage bars."""
        page, errors = self.open_report({"width": 1440, "height": 900})
        self.wait_for_report(page)
        for name, chart_ids in (
            ("customer", ("customer-identity", "customer-email")),
            ("geo", ("proxy-risk",)),
        ):
            page.locator(f'[data-page="{name}"]').click()
            for chart_id in chart_ids:
                with self.subTest(workspace=name, chart=chart_id):
                    plot = page.locator(f"#{chart_id}")
                    plot.locator(".rate-evidence-chart").wait_for(timeout=15000)
                    self.assertGreater(plot.locator(".rate-denominator").count(), 0)
                    self.assertIn("Wilson 95%", plot.inner_text())
        self.assertEqual(errors, [])


    def test_dark_nexus_chart_surfaces_and_evidence_drill(self):
        """Overview SVG, risk bands, segment drill and chart drawer stay on dark surfaces."""
        for width, height in ((1440, 900), (375, 812)):
            with self.subTest(viewport=width):
                page, errors = self.open_report({"width": width, "height": height})
                self.wait_for_report(page)
                page.locator("#overview-trend svg").wait_for(timeout=15000)
                for selector in (
                    ".studio-overview .visual-card",
                    ".studio-overview .risk-band-card",
                    ".studio-overview .chart-figure",
                ):
                    background = page.locator(selector).first.evaluate(
                        "(node) => getComputedStyle(node).backgroundImage"
                    )
                    self.assertNotIn("rgb(255, 255, 255)", background)
                self.assertIn(
                    "linear-gradient",
                    page.locator(".studio-overview .risk-band-card").first.evaluate(
                        "(node) => getComputedStyle(node).backgroundImage"
                    ),
                )
                page.locator(".risk-band-card[data-filter-key]").first.click()
                self.assertTrue(page.locator(".studio-drill-hero").is_visible())
                self.assertEqual(page.locator(".studio-drill-metrics .kpi-card").count(), 4)
                self.assertIn(
                    "No finer cohort has been published",
                    page.locator("#drill-nested").inner_text(),
                )
                self.assertGreater(page.locator("#drill-peers svg").count(), 0)
                self.assertLessEqual(
                    page.evaluate(
                        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    ),
                    1,
                )
                page.locator("#drill-back-btn").click()
                page.locator("#overview-trend").locator(
                    "xpath=ancestor::article[contains(@class, 'visual-card')]"
                ).locator(".visual-title").click()
                drawer = page.locator("#detail-drawer")
                self.assertTrue(drawer.is_visible())
                self.assertEqual(drawer.get_attribute("role"), "dialog")
                self.assertNotIn(
                    "rgb(255, 255, 255)",
                    drawer.evaluate("(node) => getComputedStyle(node).backgroundImage"),
                )
                page.keyboard.press("Escape")
                self.assertFalse(drawer.is_visible())
                self.assertEqual(errors, [])


    def test_fraud_chart_numbers_have_no_white_halo_or_scaled_down_axes(self):
        """Guard against the SVG 4px white text stroke and miniature chart numerals."""
        for width, height in ((1440, 900), (375, 812)):
            with self.subTest(viewport=width):
                page, errors = self.open_report({"width": width, "height": height})
                self.wait_for_report(page)
                page.locator("#overview-trend svg .svg-axis").first.wait_for(timeout=15000)
                axis = page.locator("#overview-trend svg .svg-axis").first
                style = axis.evaluate(
                    """(element) => {
                      const s = getComputedStyle(element);
                      return {stroke: s.stroke, strokeWidth: s.strokeWidth,
                        shadow: s.textShadow, filter: s.filter, opacity: s.opacity,
                        font: parseFloat(s.fontSize)};
                    }"""
                )
                self.assertEqual(style["stroke"], "none")
                self.assertEqual(style["strokeWidth"], "0px")
                self.assertEqual(style["shadow"], "none")
                self.assertEqual(style["filter"], "none")
                self.assertEqual(style["opacity"], "1")
                self.assertGreaterEqual(style["font"], 12)

                latest = page.locator("#overview-trend .chart-current-readout")
                self.assertTrue(latest.is_visible())
                self.assertIn("%", latest.inner_text())

                geometry = page.locator("#overview-trend .chart-figure").evaluate(
                    """figure => ({
                      client: figure.clientWidth,
                      scroll: figure.scrollWidth,
                      svg: figure.querySelector('svg').getBoundingClientRect().width
                    })"""
                )
                if width == 1440:
                    self.assertGreaterEqual(geometry["svg"], 740)
                else:
                    self.assertGreater(geometry["scroll"], geometry["client"])

                page.locator('[data-page="geo"]').click()
                label = page.locator("#report-body svg .svg-value").first
                label.wait_for(timeout=15000)
                metrics = label.evaluate(
                    """element => {
                      const s = getComputedStyle(element);
                      return {stroke: s.stroke, strokeWidth: s.strokeWidth,
                        shadow: s.textShadow, filter: s.filter, font: parseFloat(s.fontSize)};
                    }"""
                )
                self.assertEqual(metrics["stroke"], "none")
                self.assertEqual(metrics["strokeWidth"], "0px")
                self.assertEqual(metrics["shadow"], "none")
                self.assertEqual(metrics["filter"], "none")
                self.assertGreaterEqual(metrics["font"], 13)

                page.locator('[data-page="model"]').click()
                tile = page.locator(".confusion-tile strong").first
                tile.wait_for(timeout=15000)
                self.assertEqual(
                    tile.evaluate("(element) => getComputedStyle(element).textShadow"), "none"
                )
                self.assertLessEqual(
                    page.evaluate(
                        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    ), 1
                )
                self.assertEqual(errors, [])


    def test_diagnostic_svg_scale_and_dark_model_panels(self):
        """Support diagnostics must not shrink labels to 37% or retain white tables."""
        for width, height in ((1440, 900), (1024, 768), (375, 812)):
            with self.subTest(viewport=width):
                page, errors = self.open_report({"width": width, "height": height})
                self.wait_for_report(page)
                checks = (
                    ("geo", "main", "#proxy-importance svg"),
                    ("features", "main", "#feature-scatter svg"),
                    ("amount", "support", "#amount-boxplot svg"),
                    ("model", "support", "#model-curves .curve-panel svg"),
                )
                for view, mode, target in checks:
                    with self.subTest(view=view, mode=mode):
                        page.locator(f'[data-page="{view}"]').click()
                        if mode == "support":
                            page.locator('[data-visual-mode="support"]').click()
                        element = page.locator(target).first
                        element.wait_for(timeout=15000)
                        effective_scale = element.evaluate(
                            "(svg) => svg.getBoundingClientRect().width / svg.viewBox.baseVal.width"
                        )
                        self.assertGreaterEqual(
                            effective_scale, 0.8, f"{view} chart text is scaled too small"
                        )
                page.locator('[data-page="model"]').click()
                page.locator('[data-visual-mode="support"]').click()
                self.assertEqual(page.locator("#model-curves .curve-axis-caption").count(), 2)
                self.assertEqual(page.locator("#model-curves .curve-panel svg").count(), 2)
                for panel in page.locator("#model-curves .curve-panel").all():
                    svg = panel.locator("svg")
                    caption = panel.locator(".curve-axis-caption")
                    self.assertGreaterEqual(
                        caption.bounding_box()["y"],
                        svg.bounding_box()["y"] + svg.bounding_box()["height"] - 1,
                    )
                cell = page.locator("#model-calibration .table-wrap td").first
                cell.wait_for(timeout=15000)
                self.assertNotEqual(
                    cell.evaluate("(element) => getComputedStyle(element).backgroundColor"),
                    "rgb(255, 255, 255)",
                )
                calibration = page.locator("#model-calibration .metric-grid>.metric").first
                self.assertEqual(calibration.locator("span").count(), 1)
                self.assertEqual(calibration.locator("strong").count(), 1)
                self.assertGreater(
                    calibration.locator("strong").bounding_box()["y"],
                    calibration.locator("span").bounding_box()["y"],
                )
                self.assertLessEqual(
                    page.evaluate(
                        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
                    ), 1
                )
                self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
