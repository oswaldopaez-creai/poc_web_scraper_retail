"""
Script to save the full HTML from Farmacia San Pablo page
This will wait for the page to fully load and save the HTML
"""

import asyncio
from playwright.async_api import async_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def save_page_html():
    """Save the full HTML from the product page"""
    url = 'https://www.farmaciasanpablo.com.mx/alimentos-y-bebidas/c/01?pageSize=192&currentPage=0'
    output_file = 'farmacia_sanpablo_full.html'
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Show browser so you can see what's happening
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = await browser.new_context(
            locale='es-MX',
            timezone_id='America/Mexico_City',
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Add stealth script
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
        
        # Wait for content to appear - check every second
        max_wait = 60  # Wait up to 60 seconds
        for i in range(max_wait):
            await asyncio.sleep(1)
            body_text_length = await page.evaluate('() => document.body.innerText.length')
            div_count = await page.evaluate('() => document.querySelectorAll("div").length')
            
            logger.info(f'  Second {i+1}: Body text length: {body_text_length}, Divs: {div_count}')
            
            # If we have substantial content, break
            if body_text_length > 500 and div_count > 10:
                logger.info(f'Content detected after {i+1} seconds!')
                break
        
        # Wait a bit more for any lazy-loaded content
        logger.info('Waiting additional 5 seconds for lazy-loaded content...')
        await asyncio.sleep(5)
        
        # Scroll to trigger lazy loading
        logger.info('Scrolling to trigger lazy loading...')
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(2)
        await page.evaluate('window.scrollTo(0, 0)')
        await asyncio.sleep(2)
        
        # Get the full HTML
        logger.info('Getting full HTML...')
        html_content = await page.content()
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f'HTML saved to: {output_file}')
        logger.info(f'HTML size: {len(html_content)} characters')
        
        # Also save a screenshot
        await page.screenshot(path='farmacia_sanpablo_screenshot.png', full_page=True)
        logger.info('Screenshot saved to: farmacia_sanpablo_screenshot.png')
        
        # Show final stats
        final_stats = await page.evaluate('''() => {
            return {
                bodyTextLength: document.body.innerText.length,
                divCount: document.querySelectorAll("div").length,
                linkCount: document.querySelectorAll("a").length,
                productDivs: document.querySelectorAll('div[class*="product"]').length
            };
        }''')
        
        logger.info('Final page stats:')
        logger.info(f'  Body text length: {final_stats["bodyTextLength"]}')
        logger.info(f'  Total divs: {final_stats["divCount"]}')
        logger.info(f'  Total links: {final_stats["linkCount"]}')
        logger.info(f'  Product divs: {final_stats["productDivs"]}')
        
        logger.info('\nBrowser will stay open for 10 seconds so you can inspect...')
        await asyncio.sleep(10)
        
        await browser.close()
        logger.info('Done!')

if __name__ == '__main__':
    asyncio.run(save_page_html())
