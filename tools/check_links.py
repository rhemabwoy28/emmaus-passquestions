#!/usr/bin/env python3
"""Verify that local href/src targets in generated HTML actually exist.

PDF targets are skipped on purpose: the archived papers are gitignored and
only present on the local machine, and the public build omits those links.
"""
from __future__ import annotations

import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "javascript:", "data:")


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for attr in ("href", "src"):
            value = values.get(attr)
            if not value or value.startswith("#") or value.startswith(SKIP_PREFIXES):
                continue
            self.targets.append(value)


def main() -> int:
    pages = sorted(p for p in ROOT.rglob("*.html") if "templates" not in p.parts)
    broken: list[str] = []
    skipped_pdfs = 0
    for page in pages:
        parser = LinkParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.targets:
            url = urlparse(raw)
            path = unquote(url.path)
            if not path:
                continue
            if path.lower().endswith(".pdf"):
                skipped_pdfs += 1
                continue
            target = (page.parent / path).resolve()
            if not target.exists():
                broken.append(f"{page.relative_to(ROOT)} -> {raw}")

    if broken:
        print(f"broken local links: {len(broken)}")
        for item in broken[:50]:
            print(f"  {item}")
        return 1
    print(f"checked {len(pages)} pages: 0 broken local links ({skipped_pdfs} PDF targets skipped by design)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
