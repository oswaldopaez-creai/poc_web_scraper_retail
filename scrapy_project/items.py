# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapyProjectItem(scrapy.Item):
    # Define the fields for your item here
    title = scrapy.Field()
    content = scrapy.Field()
    url = scrapy.Field()
    # Add more fields as needed for your specific use case
    pass
