"""Official owner-provided NEXUS SVG identity appears consistently in the live UI.

The artwork was verified byte-for-byte against the approved private Drive pack.
No browser/network access or SVG alterations are required in this test.
"""
from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
app = importlib.import_module("webapp.main").app
SHA256 = {
    "docs/assets/nexus-official-midnight.svg": "c31c9df29384ea3d75587a757a7b28386e66e41c1b52ce072887df1cbf00d6bd",
    "docs/assets/nexus-official-transparent.svg": "143788fc114348b03bcef5285c134d63135bd7dbd908380e973596f743c9f45b",
    "docs/assets/nexus-official-mark.svg": "62b6f2a3b306b4c969098f92dfb578ef7ca20373b202872782c70ec8e1dd1dbe",
    "webapp/static/seo/favicon.svg": "62b6f2a3b306b4c969098f92dfb578ef7ca20373b202872782c70ec8e1dd1dbe",
}


def test_official_brand_vectors_match_owner_approved_source_bytes() -> None:
    for path, expected_hash in SHA256.items():
        svg_bytes = (ROOT / path).read_bytes()
        assert hashlib.sha256(svg_bytes).hexdigest() == expected_hash
        root = ET.fromstring(svg_bytes)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert (ROOT / "docs/assets/nexus-official-mark.svg").read_bytes() == (
        ROOT / "webapp/static/seo/favicon.svg"
    ).read_bytes()


def test_official_icon_replaces_both_sidebar_letter_placeholders() -> None:
    for path, placeholder in (
        ("webapp/static/index.html", '<div class="brand-mark" aria-hidden="true">NX</div>'),
        ("webapp/static/decision-studio.html", '<span class="brand-mark">N</span>'),
    ):
        html = (ROOT / path).read_text(encoding="utf-8")
        assert placeholder not in html
        assert '<img class="brand-symbol" src="/static/seo/favicon.svg"' in html
        assert 'width="36" height="36" alt="" decoding="async"' in html
        assert 'rel="icon" type="image/svg+xml" href="/static/seo/favicon.svg"' in html
    for style in ("webapp/static/nexus-design.css", "webapp/static/decision-studio.css"):
        css = (ROOT / style).read_text(encoding="utf-8")
        assert ".brand-mark .brand-symbol" in css
        assert "object-fit:contain" in css.replace(" ", "")


def test_served_nexus_brand_is_local_and_both_routes_use_it() -> None:
    client = TestClient(app)
    symbol = client.get("/static/seo/favicon.svg")
    assert symbol.status_code == 200
    assert hashlib.sha256(symbol.content).hexdigest() == SHA256["webapp/static/seo/favicon.svg"]
    for route in ("/", "/studio"):
        response = client.get(route)
        assert response.status_code == 200
        assert 'src="/static/seo/favicon.svg"' in response.text
        assert 'href="/static/seo/favicon.svg"' in response.text


def test_readme_uses_approved_midnight_wordmark_and_source_is_documented() -> None:
    landing = (ROOT / "README.md").read_text(encoding="utf-8")
    docs = (ROOT / "docs/BRAND_IDENTITY.md").read_text(encoding="utf-8")
    assert 'src="docs/assets/nexus-official-midnight.svg"' in landing
    assert "NEXUS_Identity_2_0" in docs
    assert "Google Drive" in docs
    assert "not an external Drive hotlink" in docs
