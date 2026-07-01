# Scrapy Web Scraping Template

A basic Scrapy project template for extracting information from websites.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
scrapy_project/
├── scrapy_project/
│   ├── spiders/
│   │   ├── __init__.py
│   │   └── example_spider.py    # Main spider template
│   ├── __init__.py
│   ├── items.py                 # Data structure definitions
│   ├── middlewares.py           # Custom middlewares (optional)
│   ├── pipelines.py             # Data processing pipelines
│   └── settings.py              # Scrapy settings
├── requirements.txt
└── README.md
```

## Usage

### Running the Example Spider

The example spider scrapes quotes from http://quotes.toscrape.com/

```bash
cd scrapy_project
scrapy crawl example
```

### Saving Output

Save scraped data to JSON:
```bash
scrapy crawl example -o output.json
```

Save to CSV:
```bash
scrapy crawl example -o output.csv
```

### Creating Your Own Spider

1. **Copy the template spider:**
   ```bash
   cp scrapy_project/spiders/example_spider.py scrapy_project/spiders/my_spider.py
   ```

2. **Modify the spider:**
   - Change `name` - unique identifier for your spider
   - Update `allowed_domains` - list of allowed domains
   - Set `start_urls` - URLs to start scraping from
   - Customize `parse()` method to match your target website's HTML structure

3. **Update items.py** if you need different data fields

4. **Run your spider:**
   ```bash
   scrapy crawl my_spider
   ```

## Customization Guide

### Extracting Data

**CSS Selectors (recommended):**
```python
title = response.css('h1.title::text').get()
links = response.css('a::attr(href)').getall()
```

**XPath:**
```python
title = response.xpath('//h1[@class="title"]/text()').get()
links = response.xpath('//a/@href').getall()
```

### Following Links

```python
# Follow relative links
next_page = response.css('a.next::attr(href)').get()
if next_page:
    yield response.follow(next_page, callback=self.parse)

# Follow multiple links
for link in response.css('a.detail-link::attr(href)').getall():
    yield response.follow(link, callback=self.parse_detail)
```

### Handling Pagination

```python
# Check if next page exists
next_page = response.css('li.next a::attr(href)').get()
if next_page:
    yield response.follow(next_page, callback=self.parse)
```

## Settings

Key settings in `settings.py`:

- `ROBOTSTXT_OBEY`: Whether to respect robots.txt (default: True)
- `DOWNLOAD_DELAY`: Delay between requests in seconds (default: 1)
- `ITEM_PIPELINES`: Enable/disable data processing pipelines

## Tips

1. **Always check robots.txt** - Respect the website's scraping policies
2. **Add delays** - Don't overload servers with too many requests
3. **Use CSS selectors** - They're more readable than XPath
4. **Test selectors** - Use browser DevTools to test CSS/XPath selectors
5. **Handle errors** - Add error handling for missing elements
6. **Respect rate limits** - Adjust `DOWNLOAD_DELAY` if needed

## Example: Customizing for a Different Website

```python
class MySpider(scrapy.Spider):
    name = 'my_spider'
    allowed_domains = ['example.com']
    start_urls = ['https://example.com/articles']
    
    def parse(self, response):
        articles = response.css('article')
        for article in articles:
            item = ScrapyProjectItem()
            item['title'] = article.css('h2::text').get()
            item['content'] = article.css('p::text').getall()
            item['url'] = response.url
            yield item
```

## Troubleshooting

- **No items scraped**: Check your CSS/XPath selectors using browser DevTools
- **403 Forbidden**: The site may be blocking scrapers. Try adjusting headers or delays
- **Empty fields**: Add error handling: `item['title'] = response.css('h1::text').get() or 'N/A'`
