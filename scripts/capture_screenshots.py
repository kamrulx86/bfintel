#!/usr/bin/env python3
"""Capture BFIntel UI screenshots for README (requires lab URL + admin creds in env)."""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "screenshots"
BASE = os.environ.get("BFINTEL_URL", "http://127.0.0.1:8080").rstrip("/")
EMAIL = os.environ.get("BFINTEL_EMAIL", "")
PASSWORD = os.environ.get("BFINTEL_PASSWORD", "")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    shots: list[tuple[str, str]] = [
        ("01-login.png", "/login"),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/login", wait_until="networkidle", timeout=60_000)
        page.screenshot(path=str(OUT / "01-login.png"), full_page=False)

        if not EMAIL or not PASSWORD:
            print("Set BFINTEL_EMAIL and BFINTEL_PASSWORD to capture authenticated pages.", file=sys.stderr)
            browser.close()
            return 0

        page.fill('input[type="email"]', EMAIL)
        page.fill('input[type="password"]', PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url("**/app**", timeout=30_000)

        routes = [
            ("02-overview.png", "/app"),
            ("03-attacks.png", "/app/attacks"),
            ("04-sources.png", "/app/sources"),
            ("05-cases.png", "/app/cases"),
            ("06-abuse-reports.png", "/app/abuse-reports"),
        ]
        for name, path in routes:
            page.goto(f"{BASE}{path}", wait_until="networkidle", timeout=60_000)
            page.wait_for_timeout(800)
            page.screenshot(path=str(OUT / name), full_page=False)

        browser.close()

    print(f"Wrote screenshots to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
