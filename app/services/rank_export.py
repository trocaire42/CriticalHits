import asyncio
import logging
from playwright.async_api import async_playwright
from app.util import ROUTES, BASE_URL

logger = logging.getLogger(__name__)

class RankExporter:
    _semaphore = asyncio.Semaphore(2)

    @classmethod
    async def capture_ranking_image(cls, uuid: str, count: int) -> bytes:
        async with cls._semaphore:
            cols = 5
            rows = -(-count // cols)

            # Height and width of individual cards; needs to match CSS .export-card-wrapper size
            card_width = 450
            card_height = 108

            width = card_width * cols
            height = card_height * rows

            async with async_playwright() as p:
                browser = await p.chromium.launch()
                context = await browser.new_context(viewport={'width': width, 'height': height})

                page = await context.new_page()

                try:
                    await page.goto(f"{BASE_URL}{ROUTES['export']}/{uuid}/{count}")
                    element = await page.wait_for_selector("#export-container", state="visible", timeout=10000)

                    await asyncio.sleep(0.5)

                    element = await page.query_selector("#export-container")
                    image_bytes = await element.screenshot(type="png")
                except Exception as e:
                    logger.error(f"[!] Error in playwright screenshot generation: {e}")
                finally:
                    await browser.close()

                return image_bytes