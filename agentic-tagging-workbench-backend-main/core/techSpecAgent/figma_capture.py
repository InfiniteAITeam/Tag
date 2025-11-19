import os
import asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

FIGMA_FILE_URL = os.getenv("FIGMA_FILE_URL")
WAIT_SELECTOR = os.getenv("FIGMA_WAIT_SELECTOR", "[data-testid='canvas_zoom_controls']")
VIEW_W = int(os.getenv("FIGMA_VIEWPORT_WIDTH", "1600"))
VIEW_H = int(os.getenv("FIGMA_VIEWPORT_HEIGHT", "1000"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "TechSpecOutputs")

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--enable-webgl",
    "--ignore-gpu-blocklist",
    "--use-gl=swiftshader",
    "--disable-blink-features=AutomationControlled",
]

def _normalize_figma_url(u: str) -> str:
    if not u:
        return u
    u = u.strip()
    if "figma.com/design/" in u:
        u = u.replace("figma.com/design/", "figma.com/file/")
    if "figma.com/proto/" in u:
        u = u.replace("figma.com/proto/", "figma.com/file/")
    return u

async def capture_figma_screenshot() -> str:
    if not FIGMA_FILE_URL:
        raise RuntimeError("FIGMA_FILE_URL is required in .env")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "figma_screen.png")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        try:
            ctx = await browser.new_context(
                viewport={"width": VIEW_W, "height": VIEW_H},
                device_scale_factor=2,
                user_agent=UA,
                locale="en-US",
                timezone_id="America/Chicago",
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": "https://www.figma.com/",
                },
            )
            # Hide webdriver fingerprint
            await ctx.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            page = await ctx.new_page()

            # Normalize URL to /file/ form (more scrape-friendly)
            url = _normalize_figma_url(FIGMA_FILE_URL)
            resp = await page.goto(url, wait_until="domcontentloaded")

            # If blocked, save HTML for inspection
            if resp and resp.status >= 400:
                dbg = os.path.join(OUTPUT_DIR, "figma_error.html")
                try:
                    html = await resp.text()
                except Exception:
                    html = await page.content()
                with open(dbg, "w", encoding="utf-8") as f:
                    f.write(html)
                raise RuntimeError(f"HTTP {resp.status} from Figma. Saved {dbg}")

            # Robust paint waits
            try:
                await page.wait_for_load_state("networkidle", timeout=30_000)
            except Exception:
                pass

            # Wait for a real canvas; fallback to toolbar selector
            try:
                await page.locator("canvas").first.wait_for(
                    state="visible", timeout=30_000
                )
            except Exception:
                try:
                    await page.wait_for_selector(WAIT_SELECTOR, timeout=15_000)
                except Exception:
                    pass

            # Screenshot the canvas container (avoid full_page on infinite-canvas apps)
            container = page.locator("div:has(canvas)").first
            if await container.count() > 0:
                await container.screenshot(path=out_path)
            else:
                await page.screenshot(path=out_path)

            # Sanity check: ensure it isn't tiny/blank
            if not (os.path.exists(out_path) and os.path.getsize(out_path) > 10_000):
                dbg2 = os.path.join(OUTPUT_DIR, "figma_403_or_blank.html")
                try:
                    html = await page.content()
                except Exception:
                    html = "<no page content available>"
                with open(dbg2, "w", encoding="utf-8") as f:
                    f.write(html)
                raise RuntimeError(f"Screenshot empty/blocked. Saved {dbg2}")

            return out_path
        finally:
            await browser.close()

def capture_sync() -> str:
    return asyncio.run(capture_figma_screenshot())
