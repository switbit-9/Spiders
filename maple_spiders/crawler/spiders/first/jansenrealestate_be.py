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
from scrapy.spiders import Rule
from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy.selector import Selector
from crawler.loader import MapleLoader
import json


class MySpider(Spider):
    name = "jansenrealestate_be"
    start_urls = ["https://www.jansenrealestate.be/residentieel/te-huur/"]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1

    def parse(self, response):
        for item in response.xpath(
            "//ul[contains(@class,'properties-list')]/li/a[@class='property-container']/@href"
        ).extract():
            yield Request(item, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("address", "div.prop-address")
        item_loader.add_xpath("description", "//div[@class='prop-description']")
        rent = response.xpath("//div[@class='prop-price']/text()").extract_first()
        if rent:
            price = rent.replace("/m", "").split("€")[1]
            item_loader.add_value("rent", price)

        item_loader.add_xpath(
            "title", "//div[@class='prop-description']/p/ya-tr-span[1]/@data-value"
        )
        item_loader.add_xpath(
            "external_id",
            "normalize-space(//div[@class='detail financieel']//div[./dt[.='Referentie']]//span)",
        )

        address = response.xpath("//div[@class='prop-address']/text()").extract_first()
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        item_loader.add_value("currency", "EUR")
        square = response.xpath(
            "normalize-space(//div[contains(@class,'afmetingen ')]//div[./dt[.='Bewoonbare oppervlakte']]/dd/span/text())"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
            item_loader.add_xpath("property_type", "//div[@class='prop-category']")
            item_loader.add_xpath(
                "available_date",
                "normalize-space(//table[@class='BodyText']//tr[./td[.='vrij :']]/td[2])",
            )
            item_loader.add_xpath(
                "room_count",
                "//ul[@class='prop-features']/li[contains(.,'Kamers:')]/text()",
            )
            item_loader.add_xpath("energy_label", "//div[./dt[.='EPC']]//span/text()")
            item_loader.add_xpath(
                "floor_plan_images",
                "//div[@class='detail downloads']/dl/div/dt/a/@href",
            )

            terrace = "".join(
                response.xpath(
                    "//div[@class='detail algemeen']//div[./dt[.='Terrassen']]//span/text()"
                ).extract()
            ).strip()
            if terrace:
                if terrace is not None:
                    item_loader.add_value("terrace", True)

            terrace = response.xpath(
                "//div[@class='tabs-container']/div[@id='details']//h4[.='Equipements de Cuisine']"
            ).get()
            if terrace:
                if terrace is not None:
                    item_loader.add_value("furnished", True)
                else:
                    item_loader.add_value("furnished", False)

            terrace = "".join(
                response.xpath(
                    "//div[@class='detail algemeen']//div[./dt[.='Parking binnen']]//span/text() | //div[@class='detail algemeen']//div[./dt[.='Garage']]//span/text()"
                ).extract()
            ).strip()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("parking", True)
                else:
                    item_loader.add_value("parking", False)

            terrace = "".join(
                response.xpath(
                    "//div[@class='detail comfort']//div[./dt[.='Lift']]//span/text()"
                ).extract()
            ).strip()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("elevator", True)

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//aside[@class='images-sidebar']/ul/li/picture/a/img/@src"
                ).extract()
            ]
            if images:
                item_loader.add_value("images", images)
            # item_loader.add_value("external_images_count", len(response.xpath("//aside[@class='images-sidebar']/ul/li/picture/a/img/@src").extract()))
            item_loader.add_xpath(
                "landlord_name",
                "//div[contains(@class,'office')]/div[@class='prop-contact-person_name']/text()",
            )
            phone = response.xpath(
                '//div[@class="prop-contact-person office"]/a[contains(@href, "tel:")]/@href'
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
            email = " ".join(
                response.xpath('//input[@id="email"]/@placeholder').extract()
            )
            if email:
                item_loader.add_value(
                    "landlord_email", "info@{}".format(email.split(" ")[0])
                )

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
