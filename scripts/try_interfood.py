from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto("https://www.interfood.hu/", wait_until="domcontentloaded", timeout=60_000)
            print(f"Oldal címe: {page.title()}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
