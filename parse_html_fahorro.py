"""
Script to parse HTML file and extract products from Farmacias del Ahorro (fahorro.com)
Usage: python parse_html_fahorro.py [html_file]
"""

import sys
import csv
import re
from typing import List, Dict
from bs4 import BeautifulSoup


def extract_products_from_html(html_file: str) -> List[Dict]:
    """
    Extract products from Farmacias del Ahorro HTML file.
    """
    print(f'Reading HTML file: {html_file}')

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    products = []

    # Selectors commonly used by e-commerce / catalog pages
    selectors = [
        'li[class*="item product product-item"]'
    ]

    product_elements = []
    for selector in selectors:
        try:
            elements = soup.select(selector)
        except Exception:
            elements = []
        if elements:
            # Filter out containers that are too generic (e.g. whole grid)
            if selector in ('div[class*="product-grid"] div', 'div[class*="col-"]'):
                # Keep only if count looks like product list (e.g. 10-500)
                if 5 <= len(elements) <= 800:
                    product_elements = elements
                    break
            else:
                product_elements = elements
                print(f'Found {len(product_elements)} elements using selector: {selector}')
                break

    if not product_elements:
        print('Trying broader search...')
        for pattern in [r'product', r'item', r'card', r'catalog']:
            all_divs = soup.find_all('div', class_=re.compile(pattern, re.I))
            if 5 <= len(all_divs) <= 800:
                product_elements = all_divs
                print(f'Found {len(product_elements)} divs with class matching: {pattern}')
                break

    if not product_elements:
        print('No product containers found.')
        return products

    print(f'\nExtracting data from {len(product_elements)} product elements...')

    for element in product_elements:
        product = {}

        # Title / name
        title_selectors = [
            'a[class*="product-item-link"]',
        ]
        title = None
        for sel in title_selectors:
            el = element.select_one(sel)
            if el:
                t = el.get_text(strip=True)
                if t and len(t) > 2 and len(t) < 300:
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

        # Price
        price_selectors = [
            '.price',
        ]
        price = None
        for sel in price_selectors:
            el = element.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if text and (re.search(r'\d', text) or '$' in text or 'MXN' in text.upper()):
                    price = text
                    break

        # URL
        url = None
        link = element.find('a', href=True)
        if link:
            href = link['href'].strip()
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f'https://www.fahorro.com{href}'
            else:
                url = f'https://www.fahorro.com/{href}'

        # Description / content (optional)
        content_selectors = ['.description', '.product-desc', '[class*="desc"]']
        content = None
        for sel in content_selectors:
            el = element.select_one(sel)
            if el:
                content = el.get_text(strip=True)
                if content and len(content) < 500:
                    break

        if title and len(title) > 2:
            product = {
                'title': title,
                'content': content or 'N/A',
                'price': price or 'N/A',
                'url': url or 'N/A',
            }
            products.append(product)
            print(f'  Product {len(products)}: {title[:55]}...')

    return products


def save_to_csv(products: List[Dict], output_file: str = 'fahorro_products.csv'):
    if not products:
        print('No products to save.')
        return

    print(f'\nSaving {len(products)} products to {output_file}...')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'content', 'price', 'url'])
        writer.writeheader()
        writer.writerows(products)
    print(f'Successfully saved to {output_file}')


def main():
    html_file = 'fahorro_full.html'
    if len(sys.argv) > 1:
        html_file = sys.argv[1]

    try:
        products = extract_products_from_html(html_file)
        if products:
            save_to_csv(products)
            print(f'\nSuccessfully extracted {len(products)} products.')
        else:
            print('\nNo products found. Save the page HTML first with: python save_html_fahorro.py')
    except FileNotFoundError:
        print(f'HTML file not found: {html_file}')
        print('Run first: python save_html_fahorro.py')
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
