"""
Script to parse Walmart Mexico HTML files and extract products.
Usage:
  python parse_html_walmart.py                    # parses walmart_page_1.html ... walmart_page_10.html
  python parse_html_walmart.py walmart_page_1.html
  python parse_html_walmart.py walmart_page_1.html walmart_page_2.html ...
"""

import sys
import csv
import re
import glob
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup


def extract_products_from_html(html_content: str, source_name: str = '') -> List[Dict]:
    """Extract products from a single HTML document."""
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []

    selectors = [
        'div[class*="mb0 ph0-xl pt0-xl bb b--near-white w-50 w-25-m pb3-m ph1"]'
    ]

    product_elements = []
    for selector in selectors:
        try:
            elements = soup.select(selector)
        except Exception:
            elements = []
        if elements and 3 <= len(elements) <= 2000:
            product_elements = elements
            break

    if not product_elements:
        for pattern in [r'product', r'item-card', r'product-tile']:
            product_elements = soup.find_all(['div', 'article', 'li'], class_=re.compile(pattern, re.I))
            if 3 <= len(product_elements) <= 2000:
                break

    for element in product_elements:
        product = {}

        title_selectors = [
            'span[data-automation-id*="product-title"]',
        ]
        title = None
        for sel in title_selectors:
            el = element.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t and 2 < len(t) < 300:
                    title = t
                    break
        if not title:
            link = element.find('a')
            if link:
                title = link.get_text(strip=True)
        if not title:
            for tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                h = element.find(tag)
                if h:
                    title = h.get_text(strip=True)
                    break

        price_selectors = [
            '[data-automation-id="product-price"] > div.mr1',
        ]
        price = None
        for sel in price_selectors:
            el = element.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and (re.search(r'\d', text) or '$' in text or 'MXN' in text.upper() or 'mx' in text.lower()):
                    price = text
                    break

        url = None
        link = element.find('a', href=True)
        if link:
            href = link['href'].strip()
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f'https://www.walmart.com.mx{href}'
            else:
                url = f'https://www.walmart.com.mx/{href}'

        

        if title and len(title) > 2:
            product = {
                'title': title,
                # 'content': 'N/A',
                'price': price or 'N/A',
                'url': url or 'N/A',
                'source_page': source_name,
            }
            products.append(product)

    return products


def main():
    if len(sys.argv) > 1:
        html_files = [f for f in sys.argv[1:] if Path(f).exists()]
    else:
        html_files = sorted(glob.glob('walmart_page_*.html'))

    if not html_files:
        print('No HTML files found. Run first: python save_html_walmart.py')
        return

    all_products = []
    seen_titles = set()

    for html_file in html_files:
        print(f'Reading: {html_file}')
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            print(f'  Error: {e}')
            continue

        source_name = Path(html_file).stem
        products = extract_products_from_html(html_content, source_name)

        for p in products:
            key = (p['title'][:80], p.get('url', ''))
            if key not in seen_titles:
                seen_titles.add(key)
                all_products.append(p)

        print(f'  Extracted {len(products)} products (total unique so far: {len(all_products)})')

    if not all_products:
        print('No products extracted.')
        return

    output_file = 'walmart_products.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'price', 'url', 'source_page'])
        writer.writeheader()
        writer.writerows(all_products)

    print(f'\nSaved {len(all_products)} unique products to {output_file}')


if __name__ == '__main__':
    main()
