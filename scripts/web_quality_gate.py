"""Fail the build for missing local page assets and invalid JS syntax.

Fast, offline-only contract checks. No customer data, live API calls or secrets.
"""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
ATTRS = {
    "a": ("href",), "link": ("href",), "script": ("src",),
    "img": ("src",), "iframe": ("src",), "source": ("src",),
    "video": ("src", "poster"), "audio": ("src",), "form": ("action",),
}
CSS_URL = re.compile(r"url\\(\\s*['\\\"]?([^\\)\\\"]+)['\\\"]?\\s*\\)", re.I)


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        valid = ATTRS.get(tag, ())
        self.urls.extend(value for key, value in attrs if key in valid and value)


def local_path(parent: Path, url: str):
    s = url.strip()
    if not s or s.startswith(("#", "//", "${", "{{")):
        return None
    parts = urlsplit(s)
    if parts.scheme:
        if parts.scheme.lower() == "javascript":
            raise ValueError("javascript: URL is prohibited")
        return None
    if parts.path.startswith("/api/") or not parts.path:
        return None
    rel = unquote(parts.path)
    if rel.startswith("/"):
        target = ROOT / rel.lstrip("/")
    else:
        target = parent / rel
    target = target.resolve()
    if not target.is_relative_to(ROOT):
        raise ValueError("Path escapes repository root")
    if target.is_dir():
        target = target / "index.html"
    return target


def main():
    issues = []
    checked = 0
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        parser = Links()
        parser.feed(path.read_text(encoding="utf-8"))
        for url in parser.urls:
            try:
                target = local_path(path.parent, url)
                if target is not None and not target.is_file():
                    issues.append(f"{path.relative_to(ROOT)} => {url} (missing)")
                checked += 1
            except (ValueError, OSError) as exc:
                issues.append(f"{path.relative_to(ROOT)} => {url} ({exc})")

    for path in sorted(ROOT.rglob("*.css")):
        if ".git" in path.parts:
            continue
        for url in CSS_URL.findall(path.read_text(encoding="utf-8")):
            try:
                target = local_path(path.parent, url)
                if target is not None and not target.is_file():
                    issues.append(f"{path.relative_to(ROOT)} => CSS url({url}) (missing)")
                checked += 1
            except (ValueError, OSError) as exc:
                issues.append(f"{path.relative_to(ROOT)} => CSS url({url}) ({exc})")

    js = sorted(p for p in ROOT.rglob("*") if p.is_file() and p.suffix in (".js", ".mjs") and ".git" not in p.parts)
    if shutil.which("node"):
        for path in js:
            result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True, timeout=15)
            if result.returncode:
                issues.append(f"{path.relative_to(ROOT)} => syntax: {result.stderr[-500:]}")
    print(f"GARAKLAND QA: {checked} local-reference checks, {len(js)} JS modules scanned, {len(issues)} issues")
    for line in issues:
        print("FAIL:", line, file=sys.stderr)
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
