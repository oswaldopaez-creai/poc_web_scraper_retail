# HTML Parser for Farmacia San Pablo

This approach downloads the full HTML and then parses it to extract products.

## Step 1: Install Dependencies

```powershell
pip install beautifulsoup4 lxml playwright
playwright install chromium
```

## Step 2: Save the HTML

Run the script to save the full HTML from the page:

```powershell
python save_html.py
```

This script will:
- Open a browser window (so you can see what's happening)
- Navigate to the product page
- Wait up to 60 seconds for content to load
- Scroll to trigger lazy loading
- Save the full HTML to `farmacia_sanpablo_full.html`
- Save a screenshot to `farmacia_sanpablo_screenshot.png`

**Important:** While the script is running, watch the browser window. If you see products loading, you can manually wait longer or interact with the page before the script finishes.

## Step 3: Parse the HTML

Once you have the HTML file, parse it to extract products:

```powershell
python parse_html.py
```

Or specify a different HTML file:

```powershell
python parse_html.py my_html_file.html
```

This will:
- Read the HTML file
- Extract product information (title, price, content, URL)
- Save to `products_from_html.csv`

## Manual Method (Alternative)

If the automated script doesn't work, you can manually save the HTML:

1. Open the browser and navigate to: `https://www.farmaciasanpablo.com.mx/alimentos-y-bebidas/c/01?pageSize=192&currentPage=0`
2. Wait for all products to load (scroll down if needed)
3. Right-click on the page → "Save As" → Save as HTML
4. Or use browser DevTools (F12) → Right-click on `<html>` → Copy → Copy element
5. Save the HTML to a file (e.g., `farmacia_sanpablo_full.html`)
6. Run: `python parse_html.py farmacia_sanpablo_full.html`

## Output

The parser will create `products_from_html.csv` with columns:
- `title`: Product name
- `content`: Product description
- `price`: Product price
- `url`: Product URL

## Troubleshooting

- **No products found**: The HTML might not contain the rendered content. Try saving the HTML again after waiting longer.
- **Empty HTML**: Make sure you're saving the HTML after the page fully loads (wait for products to appear).
- **Wrong selectors**: The parser tries multiple selector strategies. Check the output to see which ones worked.
