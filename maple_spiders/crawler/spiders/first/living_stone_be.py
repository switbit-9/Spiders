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
import math


class MySpider(Spider):
    name = "living_stone_be"
    start_urls = ["https://www.living-stone.be/te-huur?searchTerm="]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath("//a[@class='estate-image']/@href").extract():
            follow_url = response.urljoin(item)
            if "searchTerm=" not in follow_url:
                yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.living-stone.be/ajax/estates/{page}?_=1600667354735"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("title", "//h2/text()")
        address = response.xpath("//h1/text()").extract_first()
        item_loader.add_value("address", address.rstrip(" -").strip())
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        item_loader.add_xpath(
            "description", "normalize-space(//p[@class='description-text'])"
        )

        price = response.xpath(
            "//span[@class='price'][contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1].split(",")[0])
            item_loader.add_value("currency", "EUR")

        property_type = "".join(response.xpath("//h2/text()").extract())
        if property_type:
            item_loader.add_value("property_type", property_type.split(" te ")[0])

        square = response.xpath(
            "//div[@class='item']/div[.='Bewoonbare oppervlakte']/following-sibling::div[@class='right'][1]/text()"
        ).extract_first()
        if square:
            square = math.ceil(float(square.split("m²")[0].strip()))
            item_loader.add_value("square_meters", str(square))

        utilities = response.xpath(
            "//div[@class='item']/div[.='Lasten']/following-sibling::div[@class='right'][1]"
        ).extract_first()
        if utilities:
            item_loader.add_value("utilities", utilities.split("€")[0])
        item_loader.add_xpath(
            "room_count",
            "///div[@class='item']/div[.='Aantal slaapkamers']/following-sibling::div[@class='right'][1]",
        )

        terrace = response.xpath(
            "//div[@class='item']/div[contains(.,'Oppervlakte terras')]/following-sibling::div[@class='right'][1]"
        ).get()
        if terrace:
            item_loader.add_value("terrace", True)

        elevator = response.xpath(
            "//div[@class='item']/div[.='Lift']/following-sibling::div[@class='right' and contains(.,'Ja')][1]/text()"
        ).extract_first()
        if elevator:
            if "Ja" in elevator:
                item_loader.add_value("elevator", True)
            elif "Nee" in elevator:
                item_loader.add_value("elevator", False)

        terrace = response.xpath(
            "//div[@class='item']/div[.='Aantal parkeerplaatsen (binnen)']/following-sibling::div[@class='right'][1]"
        ).get()
        if terrace:
            item_loader.add_value("parking", True)

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//img[contains(@alt,'Slider image')]/@src"
            ).extract()
        ]
        if images:
            item_loader.add_value("images", images)

        phone = response.xpath(
            '//div[@class="col-sm-12 footer-disclaimer"]/p/a[contains(@href, "tel:")]/@href'
        ).get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
        email = response.xpath(
            '//div[@class="col-sm-12 footer-disclaimer"]/p/a[contains(@href, "mailto:")]/@href'
        ).get()
        if email:
            item_loader.add_value("landlord_email", email.replace("mailto:", ""))

        floor_plan_images = response.xpath(
            "//a[contains(.,'plannen')]/@href[contains(.,'pdf')]"
        ).extract_first()
        if floor_plan_images:
            item_loader.add_value("floor_plan_images", floor_plan_images)

        yield item_loader.load_item()


def split_address(address, get):
    if "," in address:
        temp = address.split(",")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(zip_code)[1].split("-")[0]

        if get == "zip":
            return zip_code
        else:
            return city
