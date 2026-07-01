"""
Convert walmart_products.csv to JSON.
Usage: python csv_to_json.py [input_csv] [output_json]
"""

import csv
import json
import sys

def main():
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'walmart_products.csv'
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.csv', '.json')

    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f'Converted {len(rows)} rows to {output_file}')

if __name__ == '__main__':
    main()
