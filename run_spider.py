#!/usr/bin/env python
"""
Simple script to run the Scrapy spider.
Usage: python run_spider.py [spider_name] [output_format]
Example: python run_spider.py example json
"""

import sys
import subprocess
from scrapy.cmdline import execute

if __name__ == '__main__':
    # Default spider name
    spider_name = sys.argv[1] if len(sys.argv) > 1 else 'example'
    
    # Default output format (optional)
    output_format = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Build command
    cmd = ['scrapy', 'crawl', spider_name]
    
    if output_format:
        output_file = f'output.{output_format}'
        cmd.extend(['-o', output_file])
    
    # Execute
    execute(cmd)
