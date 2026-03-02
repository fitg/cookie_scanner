import asyncio
import json
import tomllib
import sys
from playwright.async_api import async_playwright

def load_config():
    try:
        with open("config.toml", "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        print("Error: config.toml not found.")
        sys.exit(1)

async def handle_cookie_consent(page):
    print("[Consent] Searching for consent banner...")
    
    # Common selectors for the 'Accept all' button
    selectors = [
        "button[data-action='consent']#accept",
        "button:has-text('Accept all')",
        ".uc-accept-button",
        "#accept"
    ]

    for selector in selectors:
        try:
            # Check all frames (iframes) because consent managers often sit in one
            for frame in page.frames:
                button = frame.locator(selector)
                if await button.is_visible(timeout=2000):
                    print(f"[Consent] Found button in frame: {frame.name or 'main'}")
                    await button.click()
                    # CRITICAL: Wait for the network to settle so the consent cookie is written
                    await page.wait_for_load_state("networkidle")
                    print("[Consent] Clicked and session updated.")
                    return True
        except Exception:
            continue
    
    print("[Consent] No banner found or already dismissed.")
    return False

async def run_traversal(browser, config):
    context = await browser.new_context(
        user_agent="CookieScanner/1.0 (+https://guerrilla.blog) Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    base_url = config['site']['domain'].rstrip('/')

    captured_cookies = []
    consent_accepted = False

    for path in config['traversal']['pages']:
        target = f"{base_url}{path}"
        print(f"[{config['site']['label']}] Visiting: {target}")
        try:
            await page.goto(target, wait_until="domcontentloaded")
            
            # Handle cookie consent on the first page visited (or if it reappears)
            if not consent_accepted:
                await handle_cookie_consent(page)
                consent_accepted = True
            
            # Small sleep to allow async tracking cookies to load
            await asyncio.sleep(config['site']['timeout']) 
            current_cookies = await context.cookies()
            captured_cookies.extend(current_cookies)
        except Exception as e:
            print(f"Error visiting {path}: {e}")

    # Deduplicate by name
    unique_cookies = {c['name']: c for c in captured_cookies}.values()
    await context.close()
    return list(unique_cookies)

async def scanner():
    config = load_config()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        print("Starting Traversal...")
        results = await run_traversal(browser, config)
        
        report = {
            "site": config['site']['domain'],
            "summary": {
                "results": len(results)
            },
            "cookies": {
                "results": results
            }
        }

        with open("cookie_report.json", "w") as f:
            json.dump(report, f, indent=4)
        
        print(f"\n[Success] Report generated: cookie_report.json")
        await browser.close()

def run():
    asyncio.run(scanner())
