"""
Script to save the full HTML from Farmacias del Ahorro (fahorro.com) page
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def save_page_html():
    """Save the full HTML from the product page"""
    url = (
        'https://www.fahorro.com/catalogo-extendido/catalogo-extendido-lo-mas-vendido.html'
        '?msclkid=7d923da71a0e112ace54542d1d05d6b1'
        '&utm_source=bing&utm_medium=cpc'
        '&utm_campaign=ma_fda_ecomm_do_sem_brand_general'
        '&utm_term=farmacias+del+ahorro&utm_content=ma_fda_ecomm_do_sem_brand_general'
        '&rows=200'
    )
    output_file = 'fahorro_full.html'

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

        logger.info(f'Navigating to: {url}')
        await page.goto(url, wait_until='domcontentloaded', timeout=60000)

        logger.info('Waiting for page to load...')

        max_wait = 60
        for i in range(max_wait):
            await asyncio.sleep(1)
            body_text_length = await page.evaluate('() => document.body.innerText.length')
            div_count = await page.evaluate('() => document.querySelectorAll("div").length')

            logger.info(f'  Second {i+1}: Body text length: {body_text_length}, Divs: {div_count}')

            if body_text_length > 500 and div_count > 10:
                logger.info(f'Content detected after {i+1} seconds!')
                break

        logger.info('Waiting additional 5 seconds for lazy-loaded content...')
        await asyncio.sleep(5)

        logger.info('Scrolling to bottom 10 times (3 second pause between each)...')
        for scroll_num in range(1, 11):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            logger.info(f'  Scroll {scroll_num}/10 - waiting 3 seconds...')
            await asyncio.sleep(3)

        logger.info('Scrolling back to top...')
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)

        logger.info('Getting full HTML...')
        html_content = await page.content()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f'HTML saved to: {output_file}')
        logger.info(f'HTML size: {len(html_content)} characters')

        await page.screenshot(path='fahorro_screenshot.png', full_page=True)
        logger.info('Screenshot saved to: fahorro_screenshot.png')

        final_stats = await page.evaluate('''() => {
            return {
                bodyTextLength: document.body.innerText.length,
                divCount: document.querySelectorAll("div").length,
                linkCount: document.querySelectorAll("a").length,
                productDivs: document.querySelectorAll('div[class*="product"], [class*="product-card"], .product-item').length
            };
        }''')

        logger.info('Final page stats:')
        logger.info(f'  Body text length: {final_stats["bodyTextLength"]}')
        logger.info(f'  Total divs: {final_stats["divCount"]}')
        logger.info(f'  Total links: {final_stats["linkCount"]}')
        logger.info(f'  Product-related elements: {final_stats["productDivs"]}')

        logger.info('\nBrowser will stay open for 10 seconds so you can inspect...')
        await asyncio.sleep(10)

        await browser.close()
        logger.info('Done!')

if __name__ == '__main__':
    asyncio.run(save_page_html())
