import runpy
from pathlib import Path


def test_public_search_and_social_contract():
    checker = Path(__file__).resolve().parents[1] / "scripts" / "check_seo_assets.py"
    runpy.run_path(str(checker), run_name="seo_checker")["check"]()
