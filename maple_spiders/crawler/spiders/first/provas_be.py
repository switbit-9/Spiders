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
    name = "provas_be"
    start_urls = ["https://www.provas.be/tehuur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 0)

        seen = False
        for item in response.css("body > a::attr(href)").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 0 or seen:
            url = f"https://www.provas.be/ajax/estates/{page}?_=1600463139414"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@id='text-block']")
        price = response.xpath(
            "//div[@id='estate-nav-block']//p/text()[contains(., 'Euro')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("Euro")[0])
            item_loader.add_value("currency", "EUR")

        prop = "".join(response.xpath("//title/text()").extract()).strip()
        if prop:
            item_loader.add_value("property_type", prop.split(" te ")[0])
        address = "".join(
            response.xpath(
                "//div[@id='estate-nav-block']/div[@class='text-left']//text()"
            ).extract()
        ).replace(" - ", ",")
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        square = response.xpath(
            "//div[@class='wrap']/ul/li[contains(.,'bewoonbare oppervlakte')]/text()"
        ).get()
        if square:
            square = square.split(":")[1]
            item_loader.add_value("square_meters", square.split("m²")[0])

        room = response.xpath(
            "//div[@class='wrap']/ul/li[contains(.,'aantal slaapkamers')]/text()"
        ).get()
        if room:
            room = room.split(":")[1]
            item_loader.add_value("room_count", room)

            floor = response.xpath(
                "//div[@class='wrap']/ul/li[contains(.,'verdieping')]/text()"
            ).get()
            if floor:
                floor = floor.split(":")[1]
                item_loader.add_value("floor", floor)

            terrace = response.xpath(
                "//div[@class='wrap']/ul/li[contains(.,'terras') and contains(.,'ja')]"
            ).get()
            if terrace:
                item_loader.add_value("terrace", True)

            terrace = response.xpath(
                "//div[@class='wrap']/ul/li[contains(.,'aantal garages')]"
            ).get()
            if terrace:
                item_loader.add_value("parking", True)

            images = [
                response.urljoin(x)
                for x in response.xpath("//div[@class='item']/img/@src").extract()
            ]
            if images:
                item_loader.add_value("images", images)

            energy = response.xpath(
                "substring-before(substring-after(//li[@class='epclabel']/img/@src, 'epc-'), '.png')"
            ).get()
            if energy:
                # energy = energy.split(":")[1]
                item_loader.add_value("energy_label", energy.upper())
            phone = response.xpath(
                '//div[@class="separator"]//p/b/a[contains(@href, "tel:")]/@href'
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
            email = response.xpath(
                '//div[@class="separator"]//p/b/a[contains(@href, "mailto:")]/@href'
            ).get()
            if email:
                item_loader.add_value("landlord_email", email.replace("mailto:", ""))

            item_loader.add_value("landlord_name", "Provas Immo Management BV")

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
