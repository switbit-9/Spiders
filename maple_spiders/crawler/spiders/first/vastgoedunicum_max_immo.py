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
    name = "vastgoedunicum_max_immo"
    start_urls = ["http://vastgoedunicum.max-immo.be/nl/te-huur/"]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        for item in response.xpath(
            "//div[@class='property-col']//div[contains(@class,'picture-wrapper')]/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = " ".join(
            response.xpath("//div[@class='container']/h1//text()").extract()
        )
        item_loader.add_value("title", title)
        desc = "".join(response.xpath("//div[@class='description']/text()").extract())
        item_loader.add_value("description", desc.lstrip().rstrip())

        price = response.xpath(
            "//table[@class='financial detail-fields']//tr[@class='even']/td[@class='value'][contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1].replace(",", "."))
            item_loader.add_value("currency", "EUR")

        deposit = response.xpath(
            "//table[@class='financial detail-fields']//tr[@class='odd']/td[@class='value'][contains(., '€')]"
        ).extract_first()
        if deposit:
            item_loader.add_value("deposit", price.split("€")[1].replace(",", "."))

        utilities = response.xpath(
            "//table[@class='financial detail-fields']//tr[./td[.='Gemeenschappelijke kosten']]/td[2]/text()"
        ).get()
        if utilities:
            item_loader.add_value("utilities", utilities.split(" ")[1])

        ref = response.xpath("//div[@class='property-ref']/text()").get()
        ref = ref.split(":")[1]
        item_loader.add_value("external_id", ref)

        square = response.xpath(
            "//table[@class='construction detail-fields']//tr[./td[.='Woonoppervlakte']]/td[@class='value']/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

            prop_type = response.xpath("//h1/small/text()").get()
            if prop_type:
                prop_type = prop_type.split(",")[1]
                item_loader.add_value("property_type", prop_type.strip())
            item_loader.add_xpath(
                "floor",
                "//table[@class='construction detail-fields']//tr[./td[.='Aantal verdiepingen']]/td[@class='value']/text()",
            )
            item_loader.add_xpath(
                "room_count",
                "//table[@class='construction detail-fields']//tr[./td[.='Aantal slaapkamers']]/td[@class='value']",
            )

            terrace = response.xpath(
                "//table[@class='indeling detail-fields']//tr[./td[.='Terras']]/td[3]/text()"
            ).get()
            if terrace:
                item_loader.add_value("terrace", True)

            terrace = response.xpath(
                "//table[@class='overall detail-fields']//tr[./td[.='Aantal parkeerplaatsen']]/td[@class='value']/text()"
            ).get()
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("parking", True)
                elif "Yes" in terrace:
                    item_loader.add_value("parking", True)
                elif "No" in terrace:
                    item_loader.add_value("parking", False)
                else:
                    item_loader.add_value("parking", False)

            elevator = response.xpath(
                "//table[@class='comfort detail-fields']//tr[./td[.='Lift']]/td[@class='value']/text()"
            ).get()
            if elevator:
                if "ja" in elevator:
                    item_loader.add_value("elevator", True)
                elif "Yes" in elevator:
                    item_loader.add_value("elevator", True)
                elif "No" in elevator:
                    item_loader.add_value("elevator", False)
                else:
                    item_loader.add_value("elevator", False)

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='thumbnails-viewport']/ul/li/img/@src"
                ).extract()
            ]
            if images:
                item_loader.add_value("images", images)

            dishwasher = response.xpath(
                "//table[@class='indeling detail-fields']//tr[./td[contains(.,'Keuken')]]/td[3]/text()"
            ).get()
            if dishwasher:
                if "dishwasher" in dishwasher:
                    item_loader.add_value("dishwasher", True)

            item_loader.add_xpath(
                "energy_label",
                "normalize-space(//tr[td[.='Energieklasse label']]/td[@class='value']/text())",
            )

            address = response.xpath(
                "normalize-space(//tr[contains(.,'Adres')]/td[2]/text())"
            ).get()
            zip_city = response.xpath(
                "normalize-space(//tr[contains(.,'Gemeente')]/td[2]/text())"
            ).get()

            item_loader.add_value("address", address + " " + zip_city)
            item_loader.add_value("zipcode", split_address(zip_city, "zip"))
            item_loader.add_value("city", split_address(zip_city, "city"))

            phone = response.xpath(
                "//div[@class='col-sm-4 office-block']/p/span[@class='tel']/text()"
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone)

            email = response.xpath(
                "//div[@class='col-sm-4 office-block']/p/strong/a/text()"
            ).get()
            if email:
                item_loader.add_value("landlord_email", email)
            item_loader.add_value("landlord_name", "Vastgoed Unicum")

            item_loader.add_xpath("latitude", "//div[@id='map']/@data-geolat")
            item_loader.add_xpath("longtitude", "//div[@id='map']/@data-geolong")
            yield item_loader.load_item()


def split_address(address, get):

    temp = address.split(" ")[1]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[0]

    if get == "zip":
        return zip_code
    else:
        return city
