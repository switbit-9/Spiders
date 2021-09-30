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
from scrapy import Request
from scrapy.selector import Selector
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
import json
from datetime import datetime


class MySpider(Spider):
    name = "dermul_be"
    start_urls = [
        "https://www.dermul.be/nl/te-huur/lijst?type%5B%5D=5096&type%5B%5D=5100&type%5B%5D=5097&selectAlltype%5B%5D=on&selectItemtype%5B%5D=5096&selectItemtype%5B%5D=5100&selectItemtype%5B%5D=5097&price%5Bmin%5D=&price%5Bmax%5D=&bedrooms%5Bmin%5D=&bedrooms%5Bmax%5D=&street=&ref=&sort_bef_combine=field_price_value+ASC"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath(
            "//div[@class='search-view-results']/div[@class='view-content']/div[not (contains(@class,'block'))]//div[contains(@class,'views-field-field-subtitle')]//a/@href"
        ).extract():
            yield Request(item, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            url = f"https://www.dermul.be/nl/te-huur/lijst?type%5B0%5D=5096&type%5B1%5D=5100&type%5B2%5D=5097&selectAlltype%5B0%5D=on&selectItemtype%5B0%5D=5096&selectItemtype%5B1%5D=5100&selectItemtype%5B2%5D=5097&price%5Bmin%5D=&price%5Bmax%5D=&bedrooms%5Bmin%5D=&bedrooms%5Bmax%5D=&street=&ref=&sort_bef_combine=field_price_value%20ASC&page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h1")
        item_loader.add_xpath(
            "description", "//div[@class='field field-name-field-description']"
        )

        rent = response.xpath(
            "//div[@class='field field-name-field-price']/text()"
        ).get()
        if rent:
            item_loader.add_value("rent", rent.split(" ")[1])
        item_loader.add_value("currency", "EUR")

        item_loader.add_value("external_link", response.url)
        square = response.xpath(
            "//div[@class='field field-name-field-livable-surface']/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
            item_loader.add_xpath(
                "property_type",
                "//div[@class='field field-name-field-maximmo-type']/text()",
            )
            item_loader.add_xpath(
                "room_count", "//div[@class='field field-name-field-bedrooms']/text()"
            )
            date = response.xpath(
                "//div[@class='field-item even'][1]/text()[contains(.,'/')]"
            ).get()
            if date:
                item_loader.add_value(
                    "available_date",
                    datetime.strptime(
                        date.replace("vrij", "").replace("op", "").strip(), "%d/%m/%Y"
                    ).strftime("%Y-%m-%d"),
                )

            floor = response.xpath(
                "//div[@class='field-item odd' and contains(.,'verdieping')]/text()"
            ).get()
            if floor:
                item_loader.add_value("floor", floor.split("verdieping")[0])

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='field field-name-field-maximmo-hoofdfoto']/img/@src"
                ).extract()
            ]
            item_loader.add_value("images", images)

            # item_loader.add_xpath("energy_label", "//div[@class='field field-name-field-epc']/text()")
            address = response.xpath(
                "//div[@class='field field-name-field-maximmo-address']//text()"
            ).extract_first()
            if address:
                item_loader.add_value("address", address)
                item_loader.add_xpath("zipcode", "//span[@class='postal-code']/text()")
                item_loader.add_xpath("city", "//span[@class='locality']/text()")

            terrace = response.xpath(
                "//div[@class='field-item odd' and contains(.,'terrace')]"
            ).get()
            if terrace:
                item_loader.add_value("terrace", True)
            # phone = response.xpath('//div[@class="top-call-us"]/strong[1]').get()
            # if phone:
            item_loader.add_value("landlord_name", "Agence Dermul")
            item_loader.add_value("landlord_phone", "059 55 10 50")
            # email = response.xpath('//div[@class="top-mail-us hidden-phone"]/a[1]').get()
            # if email:
            item_loader.add_value("landlord_email", "info@dermul.be")

            yield item_loader.load_item()
