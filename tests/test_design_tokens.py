"""Design system v1 — tokens on customer pages, required CSS variables."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_VARS = (
    "--gl-deep",
    "--gl-green",
    "--gl-accent-explore",
    "--gl-accent-deal",
    "--gl-paper",
    "--gl-border",
    "--gl-radius-md",
)

PAGES_NEED_TOKENS = (
    "home.html",
    "index.html",
    "market.html",
    "map.html",
    "ops.html",
    "login.html",
    "design/design-system.html",
)


class DesignTokenTests(unittest.TestCase):
    def test_tokens_file_defines_core_vars(self):
        text = (ROOT / "design" / "tokens.css").read_text(encoding="utf-8")
        for var in REQUIRED_VARS:
            self.assertIn(var, text, msg=f"missing {var} in tokens.css")

    def test_customer_pages_load_tokens(self):
        needle = "/design/tokens.css"
        for name in PAGES_NEED_TOKENS:
            path = ROOT / name
            self.assertTrue(path.is_file(), msg=f"missing page {name}")
            body = path.read_text(encoding="utf-8")
            self.assertIn(needle, body, msg=f"{name} must link tokens.css")

    def test_platform_css_removed(self):
        self.assertFalse((ROOT / "platform.css").is_file(), "legacy platform.css should be deleted")
        for py in (ROOT / "tests").glob("*.py"):
            if py.name == "test_design_tokens.py":
                continue
        html_files = list(ROOT.glob("*.html")) + list((ROOT / "design").glob("*.html"))
        for path in html_files:
            text = path.read_text(encoding="utf-8", errors="ignore")
            self.assertNotIn("platform.css", text, msg=f"{path.name} still references platform.css")

    def test_site_chrome_tabs(self):
        js = (ROOT / "design" / "site-chrome.mjs").read_text(encoding="utf-8")
        self.assertIn("gl-mobile-nav", js)
        self.assertEqual(len(re.findall(r'id:\s*"', js)), 5, "mobile nav should expose 5 tabs")


if __name__ == "__main__":
    unittest.main()
