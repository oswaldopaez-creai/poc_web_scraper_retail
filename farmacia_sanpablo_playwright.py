"""
Standalone Playwright scraper for Farmacia San Pablo
This script uses Playwright directly (without Scrapy) to scrape product data.
"""

import asyncio
import csv
import time
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FarmaciaSanPabloScraper:
    """Scraper for Farmacia San Pablo using Playwright"""
    
    def __init__(self, output_file: str = 'farmacia_sanpablo_output.csv', headless: bool = True):
        """
        Initialize the scraper
        
        Args:
            output_file: Path to output CSV file
            headless: If False, browser window will be visible (default: True)
        """
        self.output_file = output_file
        self.base_url = 'https://www.farmaciasanpablo.com.mx'
        self.start_url = 'https://www.farmaciasanpablo.com.mx/alimentos-y-bebidas/c/01?pageSize=192&currentPage=0'
        self.products = []
        self.headless = headless
        
    async def scrape_page(self, page: Page, url: str) -> List[Dict]:
        """
        Scrape products from a single page
        
        Args:
            page: Playwright page object
            url: URL to scrape
            
        Returns:
            List of product dictionaries
        """
        logger.info(f'Scraping page: {url}')
        
        try:
            # Navigate to the page
            response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
            
            # Check response status
            if response:
                logger.info(f'Response status: {response.status}')
                if response.status != 200:
                    logger.warning(f'Non-200 status code: {response.status}')
            
            # Simulate human behavior: random mouse movement and scroll
            await page.mouse.move(500, 300)
            await asyncio.sleep(0.5)
            await page.evaluate('window.scrollTo(0, 200)')
            await asyncio.sleep(1)
            
            # Wait a bit for initial page load
            await asyncio.sleep(2)
            
            # Check what's actually on the page
            page_title = await page.title()
            current_url = page.url
            logger.info(f'Page title: {page_title}')
            logger.info(f'Current URL: {current_url}')
            
            # Take a screenshot for debugging (when browser is visible)
            if not self.headless:
                await page.screenshot(path='debug_page.png', full_page=True)
                logger.info('Screenshot saved to debug_page.png')
            
            # Check page content
            body_text = await page.evaluate('() => document.body.innerText')
            logger.info(f'Page body text length: {len(body_text)} characters')
            logger.info(f'First 500 chars of page: {body_text[:500]}')
            
            # Check for blocking pages or errors
            if 'access denied' in body_text.lower() or 'blocked' in body_text.lower():
                logger.error('Page appears to be blocked!')
            if 'captcha' in body_text.lower() or 'challenge' in body_text.lower():
                logger.error('Page shows captcha/challenge!')
            if len(body_text) < 100:
                logger.warning('Page content seems very short - might be blank or blocked')
            
            # Wait for the SPA app to initialize - look for app root element
            logger.info('Waiting for SPA application to initialize...')
            try:
                # Wait for the app root to have content (not just empty div)
                await page.wait_for_function(
                    '''() => {
                        const body = document.body;
                        return body.children.length > 0 && body.innerText.length > 100;
                    }''',
                    timeout=30000
                )
                logger.info('SPA application initialized!')
            except PlaywrightTimeoutError:
                logger.warning('SPA might not have initialized, continuing...')
            
            # Wait for product API calls specifically
            logger.info('Waiting for product API calls...')
            product_api_detected = False
            try:
                # Use a promise-based approach to wait for API response
                async def wait_for_product_api():
                    async with page.expect_response(
                        lambda response: 'api.farmaciasanpablo.com.mx' in response.url and 
                                       ('product' in response.url.lower() or 
                                        'category' in response.url.lower() or 
                                        'catalog' in response.url.lower() or
                                        'search' in response.url.lower() or
                                        '/c/' in response.url or
                                        'pages' in response.url.lower()),
                        timeout=30000
                    ) as response_info:
                        response = await response_info.value
                        logger.info(f'Product API call detected: {response.url[:150]}')
                        return True
                
                product_api_detected = await wait_for_product_api()
                await asyncio.sleep(5)  # Give more time for content to render
            except Exception as e:
                logger.warning(f'No product API call detected: {e}, trying to wait for content anyway...')
            
            # Try waiting for the page to fully load with networkidle
            try:
                await page.wait_for_load_state('networkidle', timeout=30000)
                logger.info('Page reached networkidle state')
            except PlaywrightTimeoutError:
                logger.warning('Page did not reach networkidle state, continuing anyway...')
            
            # Wait longer for React/Vue to render content
            logger.info('Waiting for dynamic content to render...')
            await asyncio.sleep(5)
            
            # Try scrolling to trigger lazy loading
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await asyncio.sleep(2)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(2)
            
            # Wait for products to load - try multiple selectors with longer timeout
            product_found = False
            selectors_to_try = [
                ('div[class*="product-grid"]', 15000),
                ('div.col-md-3', 15000),
                ('div[class*="product"]', 15000),
                ('div.product-item', 10000),
                ('div[data-product]', 10000),
                ('cx-product', 10000),  # Angular component
                ('app-product', 10000),   # Angular component
                ('[class*="Product"]', 10000),
                ('article', 10000),
            ]
            
            for selector, timeout in selectors_to_try:
                try:
                    await page.wait_for_selector(selector, timeout=timeout)
                    logger.info(f'Found products using selector: {selector}')
                    product_found = True
                    break
                except PlaywrightTimeoutError:
                    continue
            
            if not product_found:
                logger.warning('No product selectors found, checking page content...')
                # Check what's actually on the page now
                page_info = await page.evaluate('''() => {
                    return {
                        divCount: document.querySelectorAll("div").length,
                        bodyTextLength: document.body.innerText.length,
                        bodyHTML: document.body.innerHTML.substring(0, 500),
                        allClasses: Array.from(document.querySelectorAll("*")).slice(0, 50).map(el => el.className).filter(c => c)
                    };
                }''')
                logger.info(f'Total divs on page: {page_info["divCount"]}')
                logger.info(f'Body text length: {page_info["bodyTextLength"]}')
                logger.info(f'Body HTML (first 500 chars): {page_info["bodyHTML"]}')
                logger.info(f'Sample classes: {page_info["allClasses"][:20]}')
            
            # Wait even more for any dynamic content to load (SPA needs time)
            wait_time = 15 if not self.headless else 12
            logger.info(f'Waiting {wait_time} seconds for SPA content to render...')
            
            # Check periodically if content has loaded
            for i in range(wait_time):
                await asyncio.sleep(1)
                body_text_check = await page.evaluate('() => document.body.innerText.length')
                if body_text_check > 100:
                    logger.info(f'Content detected after {i+1} seconds!')
                    break
            
            # Final check after waiting
            body_text_after = await page.evaluate('() => document.body.innerText')
            logger.info(f'Body text length after wait: {len(body_text_after)} characters')
            
            if len(body_text_after) == 0:
                logger.warning('Page still appears blank - trying to trigger content load...')
                # Try scrolling to trigger lazy loading
                await page.evaluate('window.scrollTo(0, 500)')
                await asyncio.sleep(2)
                await page.evaluate('window.scrollTo(0, 0)')
                await asyncio.sleep(2)
                
                # Try clicking any visible buttons/links
                try:
                    buttons = await page.query_selector_all('button:not([disabled]), a[role="button"]:not([disabled])')
                    logger.info(f'Found {len(buttons)} interactive buttons on page')
                    if buttons and len(buttons) > 0:
                        # Try clicking the first button (might trigger content load)
                        try:
                            await buttons[0].click(timeout=2000)
                            await asyncio.sleep(3)
                            logger.info('Clicked a button to trigger content load')
                        except:
                            pass
                except Exception as e:
                    logger.debug(f'Error checking buttons: {e}')
            
            # If browser is visible, give user time to inspect
            if not self.headless:
                logger.info('=' * 60)
                logger.info('Browser is visible - inspect the page now')
                logger.info('Check if you see products or if page is blank/blocked')
                logger.info('=' * 60)
                # Uncomment the line below to actually pause and wait for user input
                # input('Press Enter in terminal to continue...')
            
            # Extract products - try multiple selector strategies
            # First, let's see what's actually on the page
            page_structure = await page.evaluate('''() => {
                const info = {
                    totalDivs: document.querySelectorAll('div').length,
                    divsWithProduct: document.querySelectorAll('div[class*="product"]').length,
                    divsWithCol: document.querySelectorAll('div[class*="col-"]').length,
                    allLinks: document.querySelectorAll('a').length,
                    bodyTextLength: document.body.innerText.length,
                    sampleClasses: []
                };
                
                // Get sample class names
                const divs = Array.from(document.querySelectorAll('div')).slice(0, 50);
                divs.forEach(div => {
                    if (div.className && div.className.trim()) {
                        info.sampleClasses.push(div.className);
                    }
                });
                
                return info;
            }''')
            
            logger.info(f'Page structure analysis:')
            logger.info(f'  Total divs: {page_structure["totalDivs"]}')
            logger.info(f'  Divs with "product" in class: {page_structure["divsWithProduct"]}')
            logger.info(f'  Divs with "col-" in class: {page_structure["divsWithCol"]}')
            logger.info(f'  Total links: {page_structure["allLinks"]}')
            logger.info(f'  Body text length: {page_structure["bodyTextLength"]}')
            logger.info(f'  Sample classes (first 20): {page_structure["sampleClasses"][:20]}')
            
            # Extract products - try multiple selector strategies
            products = await page.evaluate('''() => {
                const products = [];
                
                // Try the original selector first
                let productElements = document.querySelectorAll('div[class="col-md-3 col-lg-3 col-sm-6 col-6 product-grid-margins"]');
                console.log('Selector 1 (exact match):', productElements.length);
                
                // If nothing found, try more flexible selectors
                if (productElements.length === 0) {
                    productElements = document.querySelectorAll('div[class*="product-grid"]');
                    console.log('Selector 2 (product-grid):', productElements.length);
                }
                if (productElements.length === 0) {
                    productElements = document.querySelectorAll('div.col-md-3');
                    console.log('Selector 3 (col-md-3):', productElements.length);
                }
                if (productElements.length === 0) {
                    productElements = document.querySelectorAll('[data-product], .product-item, .product');
                    console.log('Selector 4 (data-product):', productElements.length);
                }
                if (productElements.length === 0) {
                    // Try finding any divs that might be products
                    productElements = document.querySelectorAll('div[class*="col-"]');
                    console.log('Selector 5 (any col-):', productElements.length);
                }
                
                console.log('Total elements found:', productElements.length);
                
                productElements.forEach((product, index) => {
                    // Try multiple ways to find title
                    let titleElement = product.querySelector('a.nameProduct') || 
                                     product.querySelector('a[href*="/product"]') ||
                                     product.querySelector('a[href*="/p/"]') ||
                                     product.querySelector('h2, h3, h4, h5') ||
                                     product.querySelector('.product-name, .product-title, .nameProduct') ||
                                     product.querySelector('a[class*="name"]');
                    
                    // Try multiple ways to find price
                    let priceElement = product.querySelector('div.price p') ||
                                      product.querySelector('.price') ||
                                      product.querySelector('[class*="price"]') ||
                                      product.querySelector('span[class*="price"]') ||
                                      product.querySelector('div[class*="price"]');
                    
                    // Try multiple ways to find content/description
                    let contentElement = product.querySelector('div.custom-postop') ||
                                        product.querySelector('.product-description') ||
                                        product.querySelector('.description') ||
                                        product.querySelector('[class*="postop"]');
                    
                    // Get all text content as fallback
                    const allText = product.innerText.trim();
                    
                    // Only add if we found something meaningful
                    if (titleElement || allText.length > 10) {
                        products.push({
                            title: titleElement ? titleElement.textContent.trim() : (allText.split('\\n')[0] || 'N/A'),
                            content: contentElement ? contentElement.textContent.trim() : 'N/A',
                            price: priceElement ? priceElement.textContent.trim() : 'N/A',
                            url: window.location.href,
                            raw_html: product.innerHTML.substring(0, 300), // First 300 chars for debugging
                            all_text: allText.substring(0, 200) // First 200 chars of all text
                        });
                    }
                });
                
                console.log('Products extracted:', products.length);
                return products;
            }''')
            
            # Log what we found
            if products:
                logger.info(f'Found {len(products)} products')
                if products[0].get('raw_html'):
                    logger.info(f'Sample product HTML: {products[0]["raw_html"]}')
                if products[0].get('all_text'):
                    logger.info(f'Sample product text: {products[0]["all_text"]}')
            else:
                logger.warning('No products extracted!')
                logger.warning('This might mean:')
                logger.warning('  1. Page is still loading (try increasing wait times)')
                logger.warning('  2. Content loads via API calls (need to wait for network requests)')
                logger.warning('  3. Selectors have changed (check debug files)')
                
                # Save page HTML for inspection
                page_html = await page.content()
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(page_html)
                logger.info('Saved page HTML to debug_page.html for inspection')
                
                # Also check for API calls that might be loading products
                logger.info('Checking for API calls...')
                try:
                    # Wait a bit more and check again
                    await asyncio.sleep(5)
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Try extracting again after waiting
                    products_retry = await page.evaluate('''() => {
                        const elements = document.querySelectorAll('div[class*="col-"]');
                        return elements.length;
                    }''')
                    logger.info(f'After additional wait, found {products_retry} div elements with "col-" class')
                except Exception as e:
                    logger.debug(f'Error checking API calls: {e}')
            
            logger.info(f'Found {len(products)} products on page')
            return products
            
        except PlaywrightTimeoutError as e:
            logger.error(f'Timeout error while scraping {url}: {e}')
            return []
        except Exception as e:
            logger.error(f'Error scraping {url}: {e}')
            return []
    
    async def find_next_page(self, page: Page) -> str:
        """
        Find the next page URL if pagination exists
        
        Args:
            page: Playwright page object
            
        Returns:
            Next page URL or None
        """
        try:
            # Look for pagination link
            next_link = await page.query_selector('li.next a')
            if next_link:
                href = await next_link.get_attribute('href')
                if href:
                    # Make absolute URL if relative
                    if href.startswith('http'):
                        return href
                    else:
                        return f"{self.base_url}{href}"
        except Exception as e:
            logger.debug(f'Error finding next page: {e}')
        
        return None
    
    async def scrape_all_pages(self, max_pages: int = None):
        """
        Scrape all pages starting from the start URL
        
        Args:
            max_pages: Maximum number of pages to scrape (None for all)
        """
        async with async_playwright() as p:
            # Launch browser with aggressive anti-detection settings
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-site-isolation-trials',
                ]
            )
            
            # Create context with realistic settings
            context = await browser.new_context(
                locale='es-MX',
                timezone_id='America/Mexico_City',
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True,
                accept_downloads=True,
                has_touch=False,
                is_mobile=False,
                color_scheme='light',
            )
            
            # Add stealth JavaScript to hide automation
            await context.add_init_script('''
                // Override navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Override chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['es-MX', 'es', 'en-US', 'en']
                });
            ''')
            
            # Add extra headers to look more like a real browser
            await context.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-MX,es;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            })
            
            page = await context.new_page()
            
            # Monitor network requests to see if products load via API
            api_requests = []
            product_api_response = None
            
            def handle_request(request):
                url = request.url
                if any(keyword in url.lower() for keyword in ['api', 'product', 'search', 'catalog', 'category']):
                    api_requests.append({
                        'url': url,
                        'method': request.method,
                        'resource_type': request.resource_type
                    })
            
            async def handle_response(response):
                url = response.url
                # Look for product/category API endpoints
                if 'api.farmaciasanpablo.com.mx' in url and ('product' in url.lower() or 'category' in url.lower() or 'catalog' in url.lower() or 'search' in url.lower()):
                    logger.info(f'Product API Response: {response.status} - {url[:150]}')
                    try:
                        # Try to get the response body
                        body = await response.body()
                        if body:
                            product_api_response = {
                                'url': url,
                                'status': response.status,
                                'body': body.decode('utf-8', errors='ignore')
                            }
                            logger.info(f'Captured API response body ({len(product_api_response["body"])} chars)')
                    except Exception as e:
                        logger.debug(f'Could not read API response body: {e}')
                elif any(keyword in url.lower() for keyword in ['api', 'product', 'search', 'catalog', 'category']):
                    logger.debug(f'API Response: {response.status} - {url[:100]}')
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # First, visit the homepage to establish a session
            logger.info('Visiting homepage first to establish session...')
            try:
                await page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(2)
                
                # Simulate human-like behavior: move mouse, scroll
                await page.mouse.move(100, 100)
                await page.evaluate('window.scrollTo(0, 100)')
                await asyncio.sleep(1)
                
                logger.info('Homepage visited, now navigating to product page...')
            except Exception as e:
                logger.warning(f'Could not visit homepage: {e}, continuing anyway...')
            
            current_url = self.start_url
            page_num = 0
            
            try:
                while current_url:
                    if max_pages and page_num >= max_pages:
                        logger.info(f'Reached maximum page limit ({max_pages})')
                        break
                    
                    page_num += 1
                    logger.info(f'Processing page {page_num}...')
                    
                    # Scrape current page
                    products = await self.scrape_page(page, current_url)
                    self.products.extend(products)
                    
                    # Log API requests if any
                    if api_requests:
                        logger.info(f'Detected {len(api_requests)} API requests during page load')
                        for req in api_requests[:5]:  # Show first 5
                            logger.info(f'  {req["method"]} {req["url"][:100]}')
                        api_requests.clear()  # Clear for next page
                    
                    # Find next page
                    next_url = await self.find_next_page(page)
                    
                    if next_url and next_url != current_url:
                        current_url = next_url
                        # Add delay between pages to be respectful
                        # Longer delay when browser is visible so you can see what's happening
                        delay = 3 if not self.headless else 2
                        await asyncio.sleep(delay)
                    else:
                        logger.info('No more pages found')
                        break
                        
            finally:
                await browser.close()
    
    def save_to_csv(self):
        """Save scraped products to CSV file"""
        if not self.products:
            logger.warning('No products to save')
            return
        
        logger.info(f'Saving {len(self.products)} products to {self.output_file}')
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['title', 'content', 'price', 'url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for product in self.products:
                # Remove debug fields before saving
                clean_product = {k: v for k, v in product.items() if k in fieldnames}
                writer.writerow(clean_product)
        
        logger.info(f'Successfully saved data to {self.output_file}')


async def main():
    """Main function to run the scraper"""
    # Set headless=False to see the browser window while scraping
    # Set headless=True to run in background (faster, no window)
    scraper = FarmaciaSanPabloScraper(
        output_file='farmacia_sanpablo_output.csv',
        headless=False  # Change to True to hide browser window
    )
    
    logger.info('Starting Farmacia San Pablo scraper...')
    if not scraper.headless:
        logger.info('Browser window will be visible (headless=False)')
    start_time = time.time()
    
    try:
        # Scrape all pages (set max_pages=None to scrape all, or a number to limit)
        await scraper.scrape_all_pages(max_pages=None)
        
        # Save results to CSV
        scraper.save_to_csv()
        
        elapsed_time = time.time() - start_time
        logger.info(f'Scraping completed in {elapsed_time:.2f} seconds')
        logger.info(f'Total products scraped: {len(scraper.products)}')
        
    except Exception as e:
        logger.error(f'Error during scraping: {e}', exc_info=True)
        # Still save what we have
        if scraper.products:
            scraper.save_to_csv()


if __name__ == '__main__':
    # Run the async main function
    asyncio.run(main())
