"""
Script to save the full HTML from Walmart Mexico (walmart.com.mx) for pages 1-10.
Uses the 'page' URL argument for pagination.
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = (
    'https://www.walmart.com.mx/browse/especiales/360013_300279_300286'
    '?co_zn=contentSN1-sub-navegation'
    '&co_ty=WEB-OHWM-subnavegation'
    '&co_nm=Homepage'
    '&co_id=precios-bajos'
    '&co_or=ahorros'
    '&page={page}'
    '&affinityOverride=default'
)

FIRST_PAGE = 1
LAST_PAGE = 10
SCROLL_COUNT = 1
SCROLL_PAUSE_SECONDS = 3
PAUSE_BETWEEN_PAGES_SECONDS = 5


async def save_one_page(page_obj, page_num: int, output_file: str) -> bool:
    """Navigate to one page, scroll, and save HTML. Returns True if saved successfully."""
    url = BASE_URL.format(page=page_num)
    logger.info(f'Navigating to page {page_num}: {url}')
    try:
        await page_obj.goto(url, wait_until='domcontentloaded', timeout=60000)
    except Exception as e:
        logger.error(f'Failed to load page {page_num}: {e}')
        return False

    logger.info(f'Page {page_num}: Waiting for content...')
    for i in range(30):
        await asyncio.sleep(1)
        body_len = await page_obj.evaluate('() => document.body.innerText.length')
        if body_len > 500:
            logger.info(f'Page {page_num}: Content detected after {i+1} seconds')
            break

    await asyncio.sleep(5)

    logger.info(f'Page {page_num}: Scrolling to bottom {SCROLL_COUNT} times ({SCROLL_PAUSE_SECONDS}s pause)...')
    for scroll_num in range(1, SCROLL_COUNT + 1):
        await page_obj.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        logger.info(f'  Page {page_num} - Scroll {scroll_num}/{SCROLL_COUNT} - waiting {SCROLL_PAUSE_SECONDS}s...')
        await asyncio.sleep(SCROLL_PAUSE_SECONDS)

    await page_obj.evaluate('window.scrollTo(0, 0)')
    await asyncio.sleep(2)

    html_content = await page_obj.content()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f'Page {page_num}: HTML saved to {output_file} ({len(html_content)} characters)')
    return True


async def save_pages_html():
    """Save HTML for pages 1 through 10."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        context = await browser.new_context(
            locale='es-MX',
            timezone_id='America/Mexico_City',
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        await context.add_init_script('''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        ''')

        page = await context.new_page()

        saved = 0
        for page_num in range(FIRST_PAGE, LAST_PAGE + 1):
            output_file = f'walmart_page_{page_num}.html'
            if await save_one_page(page, page_num, output_file):
                saved += 1

            if page_num < LAST_PAGE:
                logger.info(f'Waiting {PAUSE_BETWEEN_PAGES_SECONDS}s before next page...')
                await asyncio.sleep(PAUSE_BETWEEN_PAGES_SECONDS)

        await browser.close()
        logger.info(f'Done! Saved {saved}/{LAST_PAGE - FIRST_PAGE + 1} pages.')


if __name__ == '__main__':
    asyncio.run(save_pages_html())
