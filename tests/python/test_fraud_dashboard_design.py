"""Source-level design contracts for the real Fraud Analytics web dashboard.

They do not claim browser screenshot or BigQuery data parity.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class NexusFraudDesignTests(unittest.TestCase):
    def test_real_report_loads_portfolio_brand_without_losing_bi_controls(self):
        html = (ROOT / "webapp/static/index.html").read_text(encoding="utf-8")
        self.assertIn('href="/static/nexus-design.css"', html)
        self.assertIn("NEXUS / RISK INTELLIGENCE", html)
        self.assertIn("NEXUS / FINANCIAL ANALYTICS", html)
        self.assertIn("Executive Fraud Overview", html)
        self.assertIn("data:image/svg+xml,", html)
        self.assertIn("%234ea8ff", html.lower())
        self.assertIn("%238f9bff", html.lower())

        self.assertIn("aria-current=", html)
        self.assertIn("navigationButton.setAttribute('aria-current'", html)
        self.assertIn('id="backend-pill" data-state="connecting"', html)
        self.assertIn("sourceStatus.dataset.state = 'unavailable'", html)
        self.assertIn("Source timestamp unavailable", html)
        self.assertNotIn("meta.refreshed_at || Date.now()", html)
        self.assertNotIn("'BigQuery live'", html)
        self.assertIn("'#4ea8ff', '#8f9bff', '#487fd8'", html)
        self.assertIn("Model Performance Analysis", html)
        self.assertIn('id="page-nav"', html)

    def test_design_preserves_light_readable_analytics_canvas_and_dark_nexus_nav(self):
        css = (ROOT / "webapp/static/nexus-design.css").read_text(encoding="utf-8")
        self.assertIn("#071829", css)
        self.assertIn("#4ea8ff", css)
        self.assertIn(".report-canvas", css)
        self.assertIn(".sidebar", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("scroll-snap-type:x proximity", css)
        self.assertIn("--teal:#4ea8ff", css)
        self.assertIn(".top-actions .btn.primary", css)

        self.assertIn("flex-flow:row nowrap", css)
        self.assertIn("overflow-x:auto", css)
        self.assertIn("@media(max-width:820px)", css)
        self.assertIn("body.light .sidebar", css)
        self.assertIn("body.light .topbar h1", css)
        self.assertIn("body.light .nav-btn.active", css)
        self.assertIn("body.light .pill.live", css)


if __name__ == "__main__":
    unittest.main()
