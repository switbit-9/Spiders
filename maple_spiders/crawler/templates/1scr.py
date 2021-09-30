#
# This file was created by Maple Software
#
#
# This template is usable for ONE-LEVEL DEEP scrapers.
#
# HOW THE LOOP WORKS:
#
# 1. SCRAPING LEVEL 1: Scrape fields and populate item.
# 1. ...
#
#

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose
from scrapy import Spider
from crawler.items import CrawlerItem
from w3lib.html import remove_tags


class MySpider(Spider):
    name = ""
    start_urls = [""]  # FIRST LEVEL

    # 1. SCRAPING
    def parse(self, response):
        item_loader = ItemLoader(item=CrawlerItem(), response=response)
        item_loader.default_input_processor = MapCompose(remove_tags)
        item_loader.default_output_processor = TakeFirst()

        item_loader.add_css("title", "h1.new_title")
        #
        # item_loader.add_css("my_field", "my_css")
        # item_loader.add_xpath("my_field", "my_xpath")
        #
        return item_loader.load_item()
