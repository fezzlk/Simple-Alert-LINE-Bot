#!/usr/bin/env python3
"""Capture rich_menu_preview.html as a 2500x1686 PNG using Playwright."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HTML_PATH = Path(__file__).parent / "rich_menu_preview.html"
OUTPUT = Path(__file__).parent / "assets" / "rich_menu_default.png"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 2500, "height": 1686})
        page.goto(f"file://{HTML_PATH.resolve()}")
        # Google Fontsの読み込みを待つ
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(OUTPUT), full_page=False)
        browser.close()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
