"""Nyilvános étlap gyűjtése Playwright segítségével."""

import re
import time
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

from .normalization import normalize_menu

SITE = "https://rendel.interfood.hu/"

API = "https://ia.interfood.hu/api/v1/"


def fetch_menu(monday):
    year, week, _ = monday.isocalendar()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.set_default_timeout(60_000)
            captured = {}

            def capture(response):
                if response.url in (API + "weeks", API + "menu") and response.request.method != "OPTIONS":
                    if not response.ok:
                        raise ValueError(f"HTTP {response.status}: {response.url}")
                    captured[response.url] = response.json()

            def wait_for_data(endpoint):
                deadline = time.monotonic() + 60
                while endpoint not in captured:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"Nem érkezett meg: {endpoint}")
                    page.wait_for_timeout(100)
                return captured[endpoint]

            page.on("response", capture)
            page.goto(SITE, wait_until="domcontentloaded")
            available = wait_for_data(API + "weeks")["data"]
            initial_menu = wait_for_data(API + "menu")
            if not any(w["year"] == year and w["week"] == week and not w["disabled"] for w in available):
                raise ValueError(f"A következő hét ({year}/{week}) még nem elérhető.")
            # A sütipanel megjelenése előtt is működik a hétválasztó;
            # a csak szükséges sütiket engedjük, ha a panel már látható.
            reject = page.get_by_role("button", name="Tagadj meg minden cookies")
            if reject.is_visible():
                reject.click()
            selector = page.get_by_role("button", name=re.compile(r"^Hét kiválasztása, jelenleg"))
            selector.wait_for()
            if selector.get_attribute("aria-label") == f"Hét kiválasztása, jelenleg kiválasztott hét: {week}":
                payload = initial_menu
            else:
                selector.click()
                captured.pop(API + "menu", None)
                page.get_by_role("button", name=f"Hét kiválasztása: {week}. hét", exact=True).click()
                payload = wait_for_data(API + "menu")
            # Keskeny nézetben a dátum vizuálisan rejtett lehet, de a DOM-ban megmarad.
            tabs = page.locator('[role="tab"]')
            week_dates = re.compile("|".join(
                re.escape((monday + timedelta(days=offset)).strftime("%Y.%m.%d."))
                for offset in range(7)
            ))
            tabs.filter(has_text=week_dates).first.wait_for(state="attached")
            tab_dates = {
                date.fromisoformat(match.replace(".", "-")).isoformat()
                for text in tabs.all_text_contents()
                for match in re.findall(r"\d{4}\.\d{2}\.\d{2}", text)
            }
            meals = normalize_menu(payload, monday)
            if {meal["date"] for meal in meals} != tab_dates:
                raise ValueError("A válasz napjai eltérnek az oldalon felsorolt napoktól.")
            return payload
        finally:
            browser.close()
