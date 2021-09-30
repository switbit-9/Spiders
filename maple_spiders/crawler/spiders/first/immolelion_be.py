#
# This file was created by Maple Software
#
#
# This template is usable for TWO-LEVEL DEEP scrapers.
#
#
# HOW IT WORKS:
#
# 1. FOLLOWING: Follow the urls specified in rules.
# 2. SCRAPING: Scrape the fields and populate item.
#
#


from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request, FormRequest
from scrapy.selector import Selector
from crawler.items import CrawlerItem
from crawler.loader import MapleLoader
from w3lib.html import remove_tags
import json
import re


class MySpider(Spider):
    name = "immolelion_be"
    start_urls = ["https://immo-lelion.be/sitemap.xml"]

    def parse(self, response):
        for item in response.xpath("//*"):
            url = item.xpath("./text()").extract_first()
            if "/location/" in url:
                yield Request(url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        title = response.xpath("//h3/text()").extract_first()
        item_loader.add_value("title", re.sub("\s{2,}", " ", title))
        item_loader.add_value("external_link", response.url)

        rent = "".join(response.xpath("//li[contains(.,'Prix')]/text()").extract())
        item_loader.add_value("rent", rent)
        item_loader.add_value("currency", "EUR")

        item_loader.add_xpath("description", "//div[@id='text']/p")
        item_loader.add_value(
            "property_type", title.split("-")[0].strip().split("/")[0]
        )

        ref = "".join(response.xpath("//li[contains(.,'Reference')]/text()").extract())
        item_loader.add_value("external_id", ref.strip())

        s_meter = "".join(
            response.xpath("//li[contains(.,'Superficie')]/text()").extract()
        )
        item_loader.add_value("square_meters", s_meter.strip())

        energy_label = "".join(
            response.xpath("//li[contains(.,'PEB:')]/text()").extract()
        )
        item_loader.add_value("energy_label", energy_label.strip())

        latlong = response.xpath("//div[@class='maps']/iframe/@src").extract_first()
        if latlong:
            item_loader.add_value(
                "latitude", latlong.split("ll=")[1].split("&sp")[0].split(",")[0]
            )
            item_loader.add_value(
                "longtitude", latlong.split("ll=")[1].split("&sp")[0].split(",")[1]
            )

        r_count = "".join(
            response.xpath("//li[contains(.,'Chambres')]/text()").extract()
        )
        if r_count:
            item_loader.add_value("room_count", r_count.strip())

            parking = response.xpath("//li[label[.='Garages:']]").get()
            if parking:
                item_loader.add_value("parking", True)

            terrace = response.xpath("//li[contains(.,'Terrasse')]").get()
            if terrace:
                item_loader.add_value("terrace", True)
            address = response.xpath("//ul[@class='breadcrumb']/li[3]/a/text()").get()
            if address:
                item_loader.add_value("address", address)
                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//div[@class='carousel-inner']//img/@src"
                    ).extract()
                ]
                if images:
                    item_loader.add_value("images", images)
                phone = response.xpath('//b[@class="phone"]/a/@href').get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
                yield item_loader.load_item()
