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


class MySpider(Spider):
    name = "dejaegher"
    start_urls = ["https://www.dejaegher.com/nl/te-huur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[contains(@class,'property-list')]//div[contains(@class,'span12 property')]/div[contains(@class,'pic')]//a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.dejaegher.com/nl/te-huur?view=list&page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h3.pull-left.leftside")
        desc = "".join(
            response.xpath(
                "//div[@class='content description-e']/div/p//text()"
            ).extract()
        )
        item_loader.add_value("description", desc.strip())
        item_loader.add_value("external_link", response.url)
        rent = response.xpath(
            "//div[@class='accordion-inner']/div[div[.='Prijs']]/div[@class='value']/text()"
        ).get()
        if rent:
            item_loader.add_value("rent", rent.split(" ")[1])
        item_loader.add_value("currency", "EUR")

        address = response.xpath(
            "//div[@class='accordion-inner']/div[div[.='Adres']]/div[@class='value']/text()"
        ).extract_first()
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))

        square = response.xpath(
            "//div[@class='accordion-inner']/div[./div[.='Grondoppervlakte' or .='Bewoonbare opp.']]//div[@class='value']/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

        prop = response.xpath(
            "normalize-space(//h3[@class='pull-left leftside']/text())"
        ).get()
        if prop:
            item_loader.add_value("property_type", prop.split("te")[0])

        item_loader.add_xpath(
            "available_date",
            "//div[@class='accordion-inner']/div[div[.='Beschikbaarheid']]/div[@class='value']",
        )

        images = [response.urljoin(x) for x in response.xpath("//img/@src").extract()]
        item_loader.add_value("images", images)

        email = response.xpath(
            "//p[@class='cs544A7ABF']/span/a/@href[contains(.,'mailto')]"
        ).get()
        if email:
            item_loader.add_value("landlord_email", email.split(":")[1])

        yield item_loader.load_item()


def split_address(address, get):
    if address is not None:
        if "," in address:
            temp = address.split(",")[1]
            zip_code = "".join(filter(lambda i: i.isdigit(), temp))
            city = address.split(",")[0]

            if get == "zip":
                return zip_code
            else:
                return city
        if " " in address:
            temp = address.split(" ")[0]
            zip_code = "".join(filter(lambda i: i.isdigit(), temp))
            city = address.split(" ")[1]

            if get == "zip":
                return zip_code
            else:
                return city
