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
    name = "macnash_sud"
    start_urls = [
        "https://www.macnash.com/en/our-agencies/macnash-sud/properties.aspx"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        url = response.xpath("//div[@id='rentZone']//div")
        for item in url:
            follow_url = response.urljoin(item.xpath("./h3/a/@href").extract_first())
            prop = item.xpath("./p[@class='type']/text()").extract_first()
            yield Request(follow_url, callback=self.populate_item, meta={"prop": prop})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        prop = response.meta.get("prop")

        item_loader.add_css("title", "h1")
        rent = response.xpath(
            "//div[@class='contact-content']/h3[@class='lead']//text()"
        ).get()
        if rent:
            item_loader.add_value("rent", rent.split("€")[0].replace(",", ""))
        item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_link", response.url)

        ref = response.xpath(
            "//div[@class='contact-content']/p[@class='reference']/text()"
        ).get()
        if ref:
            item_loader.add_value("external_id", ref.split(" ")[1])
        if prop is not None:
            item_loader.add_value("property_type", prop.split(" - ")[1])
        square = response.xpath("//tr[./td[.='Surface']]/td[2]//text()").get()
        if square:
            item_loader.add_xpath("square_meters", square.split("m²")[0])
            room = response.xpath("//tr[./td[.='Number of bedrooms']]/td[2]").get()
            if room:
                item_loader.add_value("room_count", room)
                item_loader.add_xpath("utilities", "//tr[./td[.='Charges (€)']]/td[2]")
                item_loader.add_xpath("floor", "//tr[./td[.='Floors']]/td[2]/text()")

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//div[@id='lightgallery']/a/@href"
                    ).extract()
                ]
                item_loader.add_value("images", images)

                terrace = response.xpath(
                    "//tr[td[.='Well furnished']]/td[2]/text()"
                ).get()
                if terrace:
                    if terrace == "Yes":
                        item_loader.add_value("furnished", True)
                    elif terrace == "No":
                        item_loader.add_value("furnished", False)

                terrace = response.xpath("//tr[td[.='Elevator']]/td[2]/text()").get()
                if terrace:
                    if terrace == "Yes":
                        item_loader.add_value("elevator", True)
                    elif terrace == "No":
                        item_loader.add_value("elevator", False)

                terrace = response.xpath(
                    "//tr[@id='contentHolder_terraceZone']/td[2]/text()"
                ).get()
                if terrace:
                    if terrace == "Yes":
                        item_loader.add_value("terrace", True)
                    elif terrace == "No":
                        item_loader.add_value("terrace", False)

                address = " ".join(
                    response.xpath(
                        "//div[@class='contact-content']/p[3]/text()"
                    ).extract()
                )
                if address:
                    item_loader.add_value("address", address)
                    item_loader.add_value("zipcode", split_address(address, "zip"))
                    item_loader.add_value("city", split_address(address, "city"))

                item_loader.add_xpath(
                    "latitude", "//tr[./td[.='Xy coordinates']][1]/td[2]/text()"
                )
                item_loader.add_xpath(
                    "longtitude", "//tr[./td[.='Xy coordinates']][2]/td[2]/text()"
                )

                energy = response.xpath(
                    "//tr[./td[.='Energy certificate']]/td[2]/text()"
                ).extract()
                for e in energy:
                    if e.isalpha():
                        item_loader.add_value("energy_label", e)

                item_loader.add_value("landlord_phone", "+32 (0)2 347 11 47")
                item_loader.add_value("landlord_name", "Macnash")
                yield item_loader.load_item()


def split_address(address, get):
    temp = address.split(" ")[-2]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
