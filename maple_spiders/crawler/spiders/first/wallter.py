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
from crawler.loader import MapleLoader
import json
import re


class MySpider(Spider):
    name = "wallter"
    start_urls = ["http://www.wallter.be/nl/te-huur"]  # LEVEL 1
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }
    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        for item in response.xpath(
            "//div[contains(@class,'seven columns')]/a[contains(@class,'half-btn')]/@href"
        ).extract():
            yield Request(item, callback=self.populate_item)

        if page < 7:
            url = f"http://www.wallter.be/nl/te-huur/pagina-{page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(
            response.xpath("//h1[@class='title color-detail-titles']/text()").extract()
        )
        if title:
            item_loader.add_value("title", title.strip())
            item_loader.add_value("property_type", title.split(" - ")[0].strip())
        item_loader.add_xpath("description", "//div[@class='text-height']")
        price = response.xpath(
            "//div[@class='details four columns price']/text()[contains(., '€')]"
        ).extract_first()
        if price is not None:
            item_loader.add_value("rent", price.replace("€", ""))
            item_loader.add_value("currency", "EUR")

        ref = response.xpath("//div[@class='questions']/p/text()").get()
        ref = ref.split(":")[1]
        item_loader.add_value("external_id", ref)
        item_loader.add_xpath(
            "available_date",
            "//div[@class='row property-details']//div[./h1[.='Financieel']]//li[text()='Beschikbaarheid datum: ' or text()='Beschikbaarheid: ']/span",
        )
        square = "".join(response.xpath("//span[@class='size-i']/text()").extract())
        if len(square) > 1:
            item_loader.add_value("square_meters", square)

        address = "".join(
            response.xpath(
                "//div[contains(@class,'row address')]/div[contains(@class,'eight columns')]/text()"
            ).extract()
        )
        address = re.sub("\s{2,}", " ", address)
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))

        terrace = response.xpath(
            "//div[@class='row property-details']//div[./h1[.='Comfort']]//li[contains(.,'Lift')]/span[.='Ja']"
        ).get()
        if terrace:
            if terrace == "Ja":
                item_loader.add_value("parking", True)
            else:
                item_loader.add_value("parking", False)

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[contains(@class,'slick-slide')]/a/@href"
            ).extract()
        ]
        if images:
            item_loader.add_value("images", images)

        item_loader.add_xpath(
            "energy_label",
            "//div[@class='row property-details']//div[./h1[.='Energie']]//li[text()='EPC score: ']/span",
        )
        phone = response.xpath(
            '//div[@class="four columns address"]/ul/li/div/a/text()'
        ).get()
        if phone:
            item_loader.add_value("landlord_phone", phone)
        email = response.xpath(
            '//div[@class="four columns address"]/ul/li//span/a/text()'
        ).get()
        if email:
            item_loader.add_value("landlord_email", email)

        yield item_loader.load_item()


def split_address(address, get):
    if "," in address:
        temp = address.split(",")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(zip_code)[1]

        if get == "zip":
            return zip_code
        else:
            return city
