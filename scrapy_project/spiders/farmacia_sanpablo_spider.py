import scrapy
import time
from scrapy_project.items import ScrapyProjectItem


class ExampleSpider(scrapy.Spider):
    """
    Template spider for web scraping.
    
    This spider demonstrates how to:
    1. Start requests from URLs
    2. Parse HTML responses
    3. Extract data using CSS selectors or XPath
    4. Follow links to other pages
    5. Yield items with extracted data
    
    To customize for your website:
    1. Change the name, allowed_domains, and start_urls
    2. Modify the parse method to match your target website's structure
    3. Update the item fields in items.py if needed
    """
    
    name = 'FarmaciaSanPablo'
    allowed_domains = ['www.farmaciasanpablo.com.mx']
    start_urls = ['https://www.farmaciasanpablo.com.mx/alimentos-y-bebidas/c/01?pageSize=192&currentPage=0']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'ROBOTSTXT_OBEY': False,  # Disable robots.txt checking
        'HTTPERROR_ALLOWED_CODES': [403],  # Allow 403 responses to be processed
        'DOWNLOAD_DELAY': 2,  # Increase delay to be more respectful
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,  # Randomize delay
        # Enable Playwright
        'DOWNLOAD_HANDLERS': {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }
    
    def start_requests(self):
        """Override to use Playwright for JavaScript rendering"""
        from scrapy_playwright.page import PageMethod
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback_httpbin,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'div[class*="product-grid"]', timeout=30000),
                        PageMethod('wait_for_load_state', 'networkidle', timeout=30000),
                    ],
                    'playwright_context_kwargs': {
                        'locale': 'es-MX',
                        'timezone_id': 'America/Mexico_City',
                    },
                }
            )
    
    def errback_httpbin(self, failure):
        """Handle request errors"""
        self.logger.error(f'Request failed: {failure.request.url}')
        self.logger.error(f'Failure type: {type(failure).__name__}')
        if hasattr(failure.value, 'response'):
            self.logger.error(f'Response status: {failure.value.response.status}')
            self.logger.error(f'Response body (first 500 chars): {failure.value.response.text[:500]}')
    
    def parse(self, response):
        """
        Parse the main page and extract quotes.
        
        This method:
        - Extracts quotes from the current page
        - Follows pagination links
        - Yields items with extracted data
        """
        # Log response status for debugging
        self.logger.info(f'Response status: {response.status}')
        self.logger.info(f'Response URL: {response.url}')
        
        # If we get a 403, log the response body to see what's happening
        if response.status == 403:
            self.logger.warning(f'403 Forbidden - Response body (first 1000 chars): {response.text[:1000]}')
            # Try to save the response to a file for inspection
            with open('403_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            self.logger.warning('Saved 403 response to 403_response.html for inspection')
            return
        
        # # Extract all quotes from the page
        # quotes = response.css('div.quote')
        quotes = response.css('div[class="col-md-3 col-lg-3 col-sm-6 col-6 product-grid-margins"]')
        
        for quote in quotes:
            item = ScrapyProjectItem()
            
            # Extract text using CSS selectors
            item['title'] = quote.css('a.nameProduct::text').get() or 'N/A'
            item['content'] = quote.css('div.custom-postop::text').get() or 'N/A'
            item['price'] = quote.css('div.price p::text').get() or 'N/A'
            item['url'] = response.url or 'N/A'

            
            # Alternative: Extract using XPath
            # item['title'] = quote.xpath('.//span[@class="text"]/text()').get()
            # item['content'] = quote.xpath('.//span[@class="author"]/text()').get()

            time.sleep(1)
            
            yield item
        
        # Follow pagination link (if exists)
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            # Construct absolute URL if relative
            next_page_url = response.urljoin(next_page)
            from scrapy_playwright.page import PageMethod
            yield scrapy.Request(
                next_page_url, 
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'div[class*="product-grid"]', timeout=30000),
                        PageMethod('wait_for_load_state', 'networkidle', timeout=30000),
                    ],
                }
            )
        
        # Alternative: Follow links to detail pages
        # detail_links = response.css('a.detail-link::attr(href)').getall()
        # for link in detail_links:
        #     yield response.follow(link, callback=self.parse_detail)
    
    # def parse_detail(self, response):
    #     """
    #     Example method for parsing detail pages.
    #     Uncomment and customize if you need to scrape detail pages.
    #     """
    #     item = ScrapyProjectItem()
    #     item['title'] = response.css('h1::text').get()
    #     item['content'] = response.css('div.content::text').get()
    #     item['url'] = response.url
    #     yield item
