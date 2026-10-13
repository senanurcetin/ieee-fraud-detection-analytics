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
        self.assertIn("Model Performance Analysis", html)
        self.assertIn('id="page-nav"', html)

    def test_design_preserves_light_readable_analytics_canvas_and_dark_nexus_nav(self):
        css = (ROOT / "webapp/static/nexus-design.css").read_text(encoding="utf-8")
        self.assertIn("#071829", css)
        self.assertIn("#4ea8ff", css)
        self.assertIn(".report-canvas", css)
        self.assertIn(".sidebar", css)
        self.assertIn("prefers-reduced-motion", css)


if __name__ == "__main__":
    unittest.main()
