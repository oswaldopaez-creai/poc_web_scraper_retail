# Farmacia San Pablo Playwright Scraper

This is a standalone Playwright scraper (no Scrapy dependency) for scraping Farmacia San Pablo products.

## Installation

1. Install Playwright:
```powershell
pip install playwright
```

2. Install Playwright browsers:
```powershell
playwright install chromium
```

## Usage

Run the scraper:
```powershell
python farmacia_sanpablo_playwright.py
```

## Features

- **Pure Playwright**: No Scrapy dependency - uses Playwright directly
- **JavaScript Rendering**: Handles JavaScript-heavy sites and bot protection
- **Pagination Support**: Automatically follows pagination links
- **CSV Export**: Saves results to `farmacia_sanpablo_output.csv`
- **Error Handling**: Robust error handling and logging
- **Respectful Scraping**: Includes delays between requests

## Configuration

You can modify the scraper behavior in `farmacia_sanpablo_playwright.py`:

- **Change output file**: Modify `output_file` parameter in `FarmaciaSanPabloScraper()`
- **Limit pages**: Set `max_pages` in `scrape_all_pages()` (e.g., `max_pages=5`)
- **Change start URL**: Modify `start_url` in the `__init__` method
- **Headless mode**: Set `headless=False` in `browser.launch()` to see the browser

## Example Usage

```python
from farmacia_sanpablo_playwright import FarmaciaSanPabloScraper
import asyncio

async def run():
    scraper = FarmaciaSanPabloScraper(output_file='my_output.csv')
    await scraper.scrape_all_pages(max_pages=3)  # Scrape only 3 pages
    scraper.save_to_csv()

asyncio.run(run())
```

## Output Format

The CSV file contains the following columns:
- `title`: Product name
- `content`: Product description/custom-postop text
- `price`: Product price
- `url`: Page URL where product was found

## Troubleshooting

- **403 Errors**: The script uses a real browser, so it should bypass bot detection. If you still get errors, try setting `headless=False` to debug.
- **Timeout Errors**: Increase timeout values in `wait_for_selector()` calls
- **No Products Found**: Check if the CSS selectors match the current website structure
