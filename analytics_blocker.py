import asyncio
import aiohttp  # For async robots.txt check
import time
from playwright.async_api import async_playwright

async def check_robots_txt(domain: str):
    print(f"[INFO] Checking robots.txt for {domain}...")
    url = f"https://{domain}/robots.txt"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.text()
                    print("[INFO] robots.txt found:")
                    print("=" * 30)
                    print(content)
                    print("=" * 30)
                else:
                    print(f"[INFO] No robots.txt found (status code: {response.status})")
    except Exception as e:
        print(f"[WARNING] Failed to fetch robots.txt: {e}")

# Run robots.txt check before everything else
async def precheck():
    await check_robots_txt("https://www.onecfoph.co/")

asyncio.run(precheck())
# Expand known trackers and suspected internal tracking endpoints
analytics_domains = [
    "google-analytics.com", "analytics.google.com", "doubleclick.net",
    "facebook.net", "hotjar.com", "mixpanel.com", "segment.io",
    "googletagmanager.com", "onecfoph/api/log", "onecfoph/track", "onecfoph/events"
]

def is_analytics(url):
    return any(domain in url for domain in analytics_domains)

async def debug_route(route, req):
    url = req.url
    if is_analytics(url):
        print(f"[BLOCKED] Analytics request: {url}")
        await route.abort()
    else:
        await route.continue_()

async def main():
    async with async_playwright() as p:
        print("[INFO] Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            timezone_id="America/New_York"
        )

        # Patch fingerprint leaks and intercept fetch/beacon for stealth
        await context.add_init_script("""() => {
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });

            const originalFetch = window.fetch;
            window.fetch = async (...args) => {
                console.log('[DEBUG] FETCH →', args[0]);
                return originalFetch.apply(this, args);
            };

            const originalSendBeacon = navigator.sendBeacon;
            navigator.sendBeacon = function(url, data) {
                console.log('[DEBUG] BEACON →', url);   
                return originalSendBeacon.apply(this, arguments);
            };
        }""")

        page = await context.new_page()

        # Intercept and block known analytics
        await page.route("**/*", lambda route, req: asyncio.create_task(debug_route(route, req)))

        # Log ALL network activity
        page.on("request", lambda request: print(
            f"[DEBUG] {request.resource_type.upper()} → {request.method} {request.url}"
        ))

        print("[INFO] Navigating to login page...")
        await page.goto("https://www.onecfoph.co//", wait_until="networkidle")

        print("[INFO] Filling email and password...")
        await page.fill('input[name="email"]', "javierdirk1979@gmail.com")
        await page.fill('input[name="password"]', "112803Ds!")

        print("[INFO] Clicking login button...")
        login_button = page.locator('button:has-text("Log in")')
        await login_button.wait_for(state="visible", timeout=5000)
        await login_button.click()
        print("[INFO] Login button clicked.")

        print("[INFO] Waiting for dashboard to load...")
        try:
            await page.wait_for_url("**/dashboard", timeout=15000)
            print("[SUCCESS] Logged in and redirected to dashboard.")
        except Exception as e:
            print(f"[WARNING] Dashboard URL not detected: {e}")

        try:
            dashboard_element = page.locator("text=Dashboard")
            await dashboard_element.wait_for(state="visible", timeout=10000)
            print("[SUCCESS] Dashboard content is visible.")
        except Exception as e:
            print(f"[ERROR] Dashboard not visible: {e}")

        print("[INFO] Taking screenshot...")
        await page.screenshot(path="final_stealth_pass.png")
        print("[INFO] Screenshot saved as final_stealth_pass.png")

        print("[INFO] Waiting so you can interact manually...")
        time.sleep(400)

        await browser.close()

asyncio.run(main())
