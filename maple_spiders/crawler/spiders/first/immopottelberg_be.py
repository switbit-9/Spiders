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
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
import json


class MySpider(Spider):
    name = "immopottelberg_be"
    start_urls = ["https://www.immopottelberg.be/te-huur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)
        seen = False
        for item in response.xpath("//a[contains(.,'meer info')]/@href").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.immopottelberg.be/te-huur?pageindex={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_xpath("title", "//div[@class='titelbalk']//td[1]/strong/text()")
        desc = " ".join(
            response.xpath("//div[@class='links']/p/text()").extract()
        ).strip()
        item_loader.add_value("description", desc)

        rent = response.xpath("//tr[td[.='Prijs:']]/td[@class='kenmerk']/text()").get()
        if rent:
            item_loader.add_value("rent", rent.split("/")[0].split(" ")[1])
        item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath(
            "external_id", "//tr[td[.='Referentie:']]/td[@class='kenmerk']"
        )
        item_loader.add_xpath("address", "//tr[td[.='Adres:']]/td[@class='kenmerk']")
        address = " ".join(
            response.xpath("//tr[td[.='Adres:']]/td[@class='kenmerk']/text()").extract()
        )
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

        square = response.xpath(
            "//tr[td[.='Bewoonbare opp.:']]/td[@class='kenmerk']/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        item_loader.add_xpath(
            "room_count", "//tr[td[.='Slaapkamers:']]/td[@class='kenmerk']"
        )
        item_loader.add_xpath(
            "available_date", "//tr[td[.='Beschikbaar vanaf:']]/td[@class='kenmerk']"
        )
        item_loader.add_xpath("floor", "//tr[td[.='Bouwlagen:']]/td[@class='kenmerk']")
        property_type = "".join(
            response.xpath("//tr[td[.='Type:']]/td[@class='kenmerk']/text()").extract()
        )
        if property_type:
            item_loader.add_value("property_type", property_type.strip())
        item_loader.add_xpath(
            "energy_label", "//tr[contains(@class,'energyClass')]/td[2]/text()"
        )

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[@class='thumb']/a/@data-large-image"
            ).extract()
        ]
        item_loader.add_value("images", images)

        terrace = response.xpath(
            "//tr[td[.='Lift:']]/td[@class='kenmerk']/text()"
        ).get()
        if terrace:
            if terrace == "Ja":
                item_loader.add_value("elevator", True)
            else:
                item_loader.add_value("elevator", False)
        phone = response.xpath(
            "normalize-space(//div[@id='footerleft']/p[2]/text())"
        ).get()
        if phone:
            item_loader.add_value(
                "landlord_phone", phone.replace("Tel:", "").replace("|", "")
            )

        email = response.xpath(
            "normalize-space(//div[@id='footerleft']/p[2]/a/text())"
        ).get()
        if email:
            item_loader.add_value("landlord_email", email)
        yield item_loader.load_item()


def split_address(address, get):

    if " " in address:
        temp = address.split(" ")[-2]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = address.split(" ")[-1]

        if get == "zip":
            return zip_code
        else:
            return city
