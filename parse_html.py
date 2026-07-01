"""
Script to parse HTML file and extract products from Farmacia San Pablo
Usage: python parse_html.py [html_file]
"""

import sys
import csv
from bs4 import BeautifulSoup
import re
from typing import List, Dict

def extract_products_from_html(html_file: str) -> List[Dict]:
    """
    Extract products from HTML file
    
    Args:
        html_file: Path to HTML file
        
    Returns:
        List of product dictionaries
    """
    print(f'Reading HTML file: {html_file}')
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    products = []
    
    # Try multiple selector strategies
    selectors = [
        'div[class*="product-grid"]',
        'div.col-md-3',
        'div[class*="product"]',
        'div.product-item',
        '[data-product]',
        'cx-product',
        'app-product',
    ]
    
    product_elements = []
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            print(f'Found {len(elements)} elements using selector: {selector}')
            product_elements = elements
            break
    
    if not product_elements:
        print('No products found with standard selectors. Trying broader search...')
        # Try to find any divs that might contain product info
        all_divs = soup.find_all('div', class_=re.compile(r'col-', re.I))
        if all_divs:
            print(f'Found {len(all_divs)} divs with "col-" class')
            product_elements = all_divs
    
    print(f'\nExtracting data from {len(product_elements)} product elements...')
    
    for idx, element in enumerate(product_elements):
        product = {}
        
        # Try to find title/name
        title_selectors = [
            'a.nameProduct',
            'a[href*="/product"]',
            'a[href*="/p/"]',
            'h2', 'h3', 'h4', 'h5',
            '.product-name',
            '.product-title',
            'a[class*="name"]',
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem and title_elem.get_text(strip=True):
                title = title_elem.get_text(strip=True)
                break
        
        if not title:
            # Try to get first link text
            link = element.find('a')
            if link:
                title = link.get_text(strip=True)
        
        if not title:
            # Get first heading text
            heading = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if heading:
                title = heading.get_text(strip=True)
        
        # Try to find price
        price_selectors = [
            'div.price p',
            '.price',
            '[class*="price"]',
            'span[class*="price"]',
            'div[class*="price"]',
        ]
        
        price = None
        for selector in price_selectors:
            price_elem = element.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Check if it looks like a price (contains $ or numbers)
                if '$' in price_text or re.search(r'\d+', price_text):
                    price = price_text
                    break
        
        # Try to find content/description
        content_selectors = [
            'div.custom-postop',
            '.product-description',
            '.description',
            '[class*="postop"]',
        ]
        
        content = None
        for selector in content_selectors:
            content_elem = element.select_one(selector)
            if content_elem:
                content = content_elem.get_text(strip=True)
                break
        
        # Try to find product URL
        url = None
        link = element.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('http'):
                url = href
            elif href.startswith('/'):
                url = f'https://www.farmaciasanpablo.com.mx{href}'
            else:
                url = f'https://www.farmaciasanpablo.com.mx/{href}'
        
        # Only add if we found at least a title
        if title and len(title) > 2:
            product = {
                'title': title or 'N/A',
                'content': content or 'N/A',
                'price': price or 'N/A',
                'url': url or 'N/A',
            }
            products.append(product)
            print(f'  Product {len(products)}: {title[:50]}...')
    
    return products

def save_to_csv(products: List[Dict], output_file: str = 'products_from_html.csv'):
    """Save products to CSV file"""
    if not products:
        print('No products to save!')
        return
    
    print(f'\nSaving {len(products)} products to {output_file}...')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'content', 'price', 'url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for product in products:
            writer.writerow(product)
    
    print(f'Successfully saved to {output_file}')

def main():
    """Main function"""
    # Default HTML file
    html_file = 'farmacia_sanpablo_full.html'
    
    # Check if HTML file provided as argument
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    
    try:
        # Extract products
        products = extract_products_from_html(html_file)
        
        if products:
            # Save to CSV
            save_to_csv(products)
            print(f'\n✅ Successfully extracted {len(products)} products!')
        else:
            print('\n❌ No products found in HTML file.')
            print('\nTips:')
            print('  1. Make sure the HTML file contains the rendered page content')
            print('  2. Try saving the HTML again after the page fully loads')
            print('  3. Check if the page structure has changed')
            
    except FileNotFoundError:
        print(f'❌ Error: HTML file not found: {html_file}')
        print('\nFirst, run: python save_html.py')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
