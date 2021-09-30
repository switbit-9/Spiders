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
    name = "ad_immo_be"
    start_urls = ["https://www.ad-immo.be/fr/a-louer"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[contains(@class,'property-list')]/div[@class='row-fluid']/div[contains(@class,'span3 property')]/div[@class='pic']//a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.ad-immo.be/fr/a-louer?view=list&page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):

        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h3.pull-left.leftside")
        prop_type = "".join(
            response.xpath(
                "normalize-space(//h3[@class='pull-left leftside']/text())"
            ).extract()
        )
        if prop_type:
            prop_type = prop_type.split(" ")[0]
            item_loader.add_value("property_type", prop_type)
        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath(
            "description",
            "//div[@class='row-fluid']/div[@class='group']/div/div[@class='field']/text()",
        )
        rent = response.xpath(
            "normalize-space(//div[@class='span8']/h3[@class='pull-right rightside'])"
        ).get()

        if rent:
            # currency = rent.split(" ")[1]
            rent = rent.split(" ")[0]

            item_loader.add_value("rent", rent)
            item_loader.add_value("currency", "EUR")

        address = response.xpath(
            "//div[@class='group']/div[@class='content']/div[div[.='Adresse']]/div[@class='value']/text()"
        ).extract_first()
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))
        square = response.xpath(
            "//div[@class='group']/div[@class='content']/div[div[.='Superficie totale']]/div[@class='value']/text()"
        ).get()
        if square:
            square = square.split(" ")[0]
            item_loader.add_value("square_meters", square)

        room = response.xpath(
            "//div[@class='group']/div[@class='content']/div[div[.='Nombre de Chambre(s)']]/div[@class='value']/text()"
        ).get()
        if room:
            room = room.split(" ")[0]
            item_loader.add_value("room_count", room)
            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@id='LargePhoto']/div//img/@src"
                ).extract()
            ]

            if images:
                item_loader.add_value("images", images)

            energy_label = response.xpath(
                "//div[@class='content']/div/img/@src"
            ).extract_first()
            if energy_label:
                label = energy_label.split("_")[1].split(".")[0]
                if label == "2":
                    item_loader.add_value("energy_label", "A+")
                if label == "3":
                    item_loader.add_value("energy_label", "A")
                if label == "4":
                    item_loader.add_value("energy_label", "B")
                if label == "5":
                    item_loader.add_value("energy_label", "C")
                if label == "6":
                    item_loader.add_value("energy_label", "D")
                if label == "7":
                    item_loader.add_value("energy_label", "E")
                if label == "8":
                    item_loader.add_value("energy_label", "F")
                if label == "9":
                    item_loader.add_value("energy_label", "G")

            utilities = response.xpath(
                "//div[@class='group span6']//div[@class='field' and ./div[.='Tenant charges']]/div[@class='value']//text()"
            ).get()
            if utilities:
                utilities = utilities.split(" ")[0]
                item_loader.add_value("utilities", utilities)

            parking = response.xpath(
                "//div[@class='group']//div[@class='field' and ./div[contains(.,'Garage')]]/div[@class='value']//text()"
            ).get()
            if parking:
                item_loader.add_value("parking", True)

            elevator = response.xpath(
                "//div[@class='content']//div[@class='field' and ./div[.='Ascenseur']]/div[@class='value']//text()"
            ).get()
            if elevator:
                if elevator == "Oui":
                    item_loader.add_value("elevator", True)
                elif elevator == "Yes":
                    item_loader.add_value("elevator", True)
                elif elevator == "No":
                    item_loader.add_value("elevator", False)
                else:
                    item_loader.add_value("elevator", False)
            item_loader.add_value("landlord_name", "AD-immo")
            item_loader.add_value("landlord_email", "info@ad-immo.be")
            item_loader.add_value("landlord_phone", "+ 32 81 74 73 75")
            yield item_loader.load_item()


def split_address(address, get):
    if " " in address:
        temp = address.split(" ")[0]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = address.split(" ")[1]

        if get == "zip":
            return zip_code
        else:
            return city
