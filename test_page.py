"""
Simple test script to check what's happening on the Farmacia San Pablo page
Run this to see what the browser actually sees
"""

import asyncio
from playwright.async_api import async_playwright

async def test_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # Always show browser
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
        
        # Visit homepage first
        print("Visiting homepage...")
        await page.goto('https://www.farmaciasanpablo.com.mx/', wait_until='domcontentloaded')
        await asyncio.sleep(3)
        
        print(f"Homepage title: {await page.title()}")
        print(f"Homepage URL: {page.url}")
        
        # Now visit product page
        print("\nVisiting product page...")
        url = 'https://www.farmaciasanpablo.com.mx/alimentos-y-bebidas/c/01?pageSize=192&currentPage=0'
        await page.goto(url, wait_until='domcontentloaded')
        
        print(f"Product page title: {await page.title()}")
        print(f"Product page URL: {page.url}")
        
        # Wait and check content
        print("\nWaiting for page to load...")
        await asyncio.sleep(5)
        
        # Check page content
        body_text = await page.evaluate('() => document.body.innerText')
        print(f"\nPage body text length: {len(body_text)}")
        print(f"First 1000 chars:\n{body_text[:1000]}")
        
        # Check for products
        product_count = await page.evaluate('''() => {
            return document.querySelectorAll('div[class*="product"]').length;
        }''')
        print(f"\nElements with 'product' in class: {product_count}")
        
        # Check for specific selector
        specific_count = await page.evaluate('''() => {
            return document.querySelectorAll('div[class="col-md-3 col-lg-3 col-sm-6 col-6 product-grid-margins"]').length;
        }''')
        print(f"Products found with specific selector: {specific_count}")
        
        # Take screenshot
        await page.screenshot(path='test_page_screenshot.png', full_page=True)
        print("\nScreenshot saved to: test_page_screenshot.png")
        
        # Save HTML
        html = await page.content()
        with open('test_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML saved to: test_page.html")
        
        print("\n" + "="*60)
        print("Browser will stay open for 30 seconds so you can inspect")
        print("Check the browser window - do you see products?")
        print("="*60)
        
        await asyncio.sleep(30)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(test_page())
