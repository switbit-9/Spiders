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
    name = "demaurissens_be"
    start_urls = [
        "https://www.demaurissens.be/fr/locations?&goal=1&pricemin=0&pricemax=0"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[@class='property-list']//div[contains(@class,'span4 property')]//div[contains(@class,'prop-link pull-right')]/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.demaurissens.be/fr/locations?page={page}&goal=1&pricemin=0&pricemax=0"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        item_loader.add_value("external_link", response.url)
        address = response.css("h3.address.pull-right").extract_first()
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        item_loader.add_xpath("description", "//div[@class='descr']")
        price = response.xpath(
            "normalize-space(//h3[@class='price pull-left']/text())"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[0])
            item_loader.add_value("currency", "EUR")
        square = response.xpath(
            "//div[@class='group']//div[@class='field' and ./div[@class='name' and .='Superficie totale']]/div[@class='value']"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        item_loader.add_xpath(
            "room_count",
            "//div[@class='group']//div[@class='field' and ./div[@class='name' and .='Nombre de chambres']]/div[@class='value']",
        )
        item_loader.add_xpath(
            "floor",
            "//div[@class='group']//div[@class='field' and ./div[@class='name' and .='Etage']]/div[@class='value']/text()",
        )

        terrace = response.xpath(
            "//div[div[@class='group-container']]//div[@class='field' and ./div[.='Terrasse']]/div[@class='value']"
        ).get()
        if terrace:
            item_loader.add_value("terrace", True)

        terrace = response.xpath(
            "//div[div[@class='group-container']]//div[@class='field' and ./div[.='Garages, Parkings']]/div[@class='value']"
        ).get()
        if terrace:
            item_loader.add_value("parking", True)

        terrace = response.xpath(
            "//div[div[@class='group-container']]//div[@class='field' and ./div[.='Ascenseur']]/div[@class='value' and .='Oui']/text()"
        ).get()
        if terrace:
            if terrace == "Oui":
                item_loader.add_value("elevator", True)
            else:
                item_loader.add_value("elevator", False)
        item_loader.add_xpath("images", "//div[@class='pic']/ul/li/a/img/@src")
        item_loader.add_xpath(
            "energy_label",
            "//div[div[@class='group-container']]//div[@class='field' and ./div[.='E totale']]/div[@class='value']",
        )
        phone = response.xpath(
            '//div[@class="custom"]//p/text()[contains(., "Tél")]'
        ).get()
        if phone:
            item_loader.add_value(
                "landlord_phone", phone.split(" - ")[0].strip().replace("Tél ", "")
            )
        email = response.xpath(
            '//div[@class="footer-1-1 span5"]//a/@href[contains(., "mailto:")]'
        ).get()
        if email:
            item_loader.add_value(
                "landlord_email", email.replace("mailto:", "").strip()
            )

        yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
