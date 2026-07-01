# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ScrapyProjectPipeline:
    """Basic pipeline for processing items"""
    
    def process_item(self, item, spider):
        """
        Process each item scraped.
        You can add data cleaning, validation, or storage logic here.
        """
        adapter = ItemAdapter(item)
        
        # Example: Clean whitespace from text fields
        for field_name in adapter.field_names():
            value = adapter.get(field_name)
            if isinstance(value, str):
                adapter[field_name] = value.strip()
        
        return item


class SaveToFilePipeline:
    """Example pipeline to save items to a JSON file"""
    
    def open_spider(self, spider):
        import json
        self.file = open('scraped_data.json', 'w', encoding='utf-8')
        self.items = []
    
    def close_spider(self, spider):
        import json
        json.dump(self.items, self.file, ensure_ascii=False, indent=2)
        self.file.close()
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        self.items.append(dict(adapter))
        return item
