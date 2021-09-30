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


class MySpider(Spider):
    name = "macnash_com"
    start_urls = ["https://www.macnash.com/FR/a-louer/terrain.aspx"]  # LEVEL 1
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }
    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 0)
        i = response.meta.get("id", 0)

        seen = False
        for item in response.xpath("//div[@id='container']/div"):
            prop_type = (
                item.xpath(".//p[@class='type']/text()").extract_first().split("-")[1]
            )
            address = item.xpath(".//h3/a/text()").extract_first()
            follow_url = response.urljoin(
                item.xpath(".//div[@class='image']/a/@href").extract_first()
            )
            yield Request(
                follow_url,
                callback=self.populate_item,
                meta={"prop_type": prop_type, "address": address},
            )
            seen = True

        if page == 0:
            for i in range(1, 8):
                url = f"https://www.macnash.com/ui/propertyitems.aspx?Page={page}&Sort=0&ZPTID={i}&TT=1"
                yield Request(
                    url, callback=self.parse, meta={"page": page + 1, "id": i}
                )
        elif seen:
            url = f"https://www.macnash.com/ui/propertyitems.aspx?Page={page}&Sort=0&ZPTID={i}&TT=1"
            yield Request(url, callback=self.parse, meta={"page": page + 1, "id": i})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        address = response.meta.get("address")
        item_loader.add_value("property_type", response.meta.get("prop_type"))
        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "div.container h1")
        item_loader.add_xpath("description", "//div[@class='content']/p")
        price = response.xpath(
            "//h3[@class='lead']//text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[0].replace(",", ""))
            item_loader.add_value("currency", "EUR")

        ref = response.xpath("//p[@class='reference']/text()").get()
        ref = ref.split(" ")[1]
        item_loader.add_value("external_id", ref)

        square = response.xpath("//tr[@id='contentHolder_surfaceZone']/td[2]").get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        item_loader.add_xpath(
            "room_count",
            "//div[@class='property--intro']/div[@class='field-name-era-aantal-slaapkamers--c field-type-text']//div[@class='era-tooltip-field']/text() | //tr[td[.='Number of bedrooms']]/td[2]/text()",
        )
        item_loader.add_xpath(
            "available_date",
            "normalize-space(//table[@class='BodyText']//tr[./td[.='vrij :']]/td[2])",
        )

        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        utilities = response.xpath("//tr[./td[.='Charges (€)']]/td[2]").extract_first()
        if utilities:
            item_loader.add_value("utilities", utilities.split("€")[0])
        item_loader.add_xpath(
            "floor", "//tr[@id='contentHolder_floorZone']/td[2]/text()"
        )

        item_loader.add_xpath(
            "latitude", "//tr[td[.='Xy coordinates']][1]/td[2]/text()"
        )
        item_loader.add_xpath(
            "longtitude", "//tr[td[.='Xy coordinates']][2]/td[2]/text()"
        )

        energy = response.xpath(
            "//tr[td[.='Energy certificate']]/td[2]/text()"
        ).extract()
        for e in energy:
            if e.isalpha():
                item_loader.add_value("energy_label", e.upper())
        images = [
            response.urljoin(x)
            for x in response.xpath("//div[@id='lightgallery']/a/img/@src").extract()
        ]
        if images:
            item_loader.add_value("images", images)

        terrace = response.xpath(
            "//tr[td[.='Terrace']]/td[.='Yes']/text() | //tr[@id='contentHolder_interiorList_detailZone_3']/td[.='Yes']"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("terrace", True)
            elif terrace == "No":
                item_loader.add_value("terrace", False)

        terrace = response.xpath(
            "//tr[td[.='Parking']]/td/text() | //tr[@id='contentHolder_parkingZone']/td[2]"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("parking", True)
            elif terrace == "No":
                item_loader.add_value("parking", False)

        terrace = response.xpath(
            "//tr[td[.='Elevator']]/td[2]/text()| //tr[@id='contentHolder_interiorList_detailZone_3']/td[.='Yes']"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("elevator", True)
            elif terrace == "No":
                item_loader.add_value("elevator", False)

        phone = response.xpath("//p[@class='print']/text()[contains(.,'+')]").get()
        if phone:
            item_loader.add_value("landlord_phone", phone)
        email = response.xpath("//p[@class='print']/text()[contains(.,'@')]").get()
        if email:
            item_loader.add_value("landlord_email", email)

        yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(zip_code)[1].strip()

    if get == "zip":
        return zip_code
    else:
        return city
