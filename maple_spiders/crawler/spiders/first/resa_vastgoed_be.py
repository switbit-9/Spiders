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
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
from scrapy import Request
import dateparser


class MySpider(Spider):
    name = "resa_vastgoe_be"
    start_urls = ["https://www.resa-vastgoed.be/nl/te-huur"]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        for item in response.xpath("//div[@class='row-fluid']"):
            url = item.xpath(".//div[@class='image']/a/@href").extract_first()
            if url:
                prop_type = (
                    item.xpath("//div[@class='prop-type pull-left']/text()")
                    .extract_first()
                    .split(" ")[0]
                )
                follow_url = response.urljoin(url)
                yield Request(
                    follow_url,
                    callback=self.populate_item,
                    meta={"prop_type": prop_type},
                )

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "h1.detailtitle")
        desc = "".join(
            response.xpath("//div[@class='content descr']/div//span//text()").extract()
        )
        item_loader.add_value("description", desc.lstrip().rstrip())
        price = response.xpath(
            "//div[@class='content']/div/div[div[.='Prijs']]/div[3]/text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1])
            item_loader.add_value("currency", "EUR")

        utilities = response.xpath(
            "//div[@class='content']//div[div[.='Lasten huurder']]/div[3]/text()[contains(., '€')]"
        ).get()
        if utilities:
            utilities = utilities.split("€")[1]
            item_loader.add_value("utilities", utilities)

        item_loader.add_xpath(
            "address", "//div[@class='content']/div[div[.='Adres']]/div[3]"
        )
        address = response.xpath(
            "//div[@class='content']/div[contains(.,'Adres')]/div[@class='value']/text()[2]"
        ).extract_first()
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))
        else:
            address_2 = response.xpath(
                "//div[@class='content']/div[contains(.,'Adres')]/div[@class='value']/text()"
            ).extract_first()
            if address_2:
                item_loader.add_value("address", address_2)
                item_loader.add_value("zipcode", split_address(address_2, "zip"))
                item_loader.add_value("city", split_address(address_2, "city"))

        square = response.xpath(
            "//div[@class='content']/div[div[.='Bewoonbare opp.']]/div[3]/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
            # elif response.xpath("//div[@class='content']/div[div[.='Grondoppervlakte']]/div[3]/text()").extract_first():

            floor = response.xpath(
                "//div[@class='content']//div[div[.='Verdieping']]/div[3]/text()"
            ).get()
            if floor:
                item_loader.add_value("floor", floor)

            prop_type = response.meta.get("prop_type")
            item_loader.add_value("property_type", prop_type)
            room = response.xpath(
                "//div[@class='content']/div[div[.='Aantal slaapkamers']]/div[3]"
            ).get()
            if room:
                item_loader.add_value("room_count", room)
                available_date = response.xpath(
                    "//div[@class='content']/div[div[.='Beschikbaarheid']]/div[3]/text()[. != 'Onmiddellijk' and . != 'Overeen te komen']"
                ).get()
                if available_date:
                    date_parsed = dateparser.parse(
                        available_date, date_formats=["%d/%m/%Y"]
                    )
                    date2 = date_parsed.strftime("%Y-%m-%d")
                    item_loader.add_value("available_date", date2)

                item_loader.add_xpath(
                    "energy_label",
                    "//div[@class='content']/div[div[.='E spec']]/div[3]",
                )

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//div[@class='swiper-container gallery-top']//img/@src"
                    ).extract()
                ]
                item_loader.add_value("images", images)

                terrace = response.xpath(
                    "//div[@class='content']/div[div[.='Lift']]/div[3]"
                ).get()
                if terrace:
                    if "Ja" in terrace:
                        item_loader.add_value("elevator", True)
                    elif "Yes" in terrace:
                        item_loader.add_value("elevator", True)
                    elif "No" in terrace:
                        item_loader.add_value("elevator", False)
                    else:
                        item_loader.add_value("elevator", False)

                phone = response.xpath(
                    '//div[@class="person-phone"]//a[contains(@href, "tel:")]/@href'
                ).get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
                email = "".join(
                    response.xpath('//div[@class="person-mail"]//text()').extract()
                )
                if email:
                    item_loader.add_value("landlord_email", email.strip())
                item_loader.add_xpath(
                    "landlord_name", "//div[@class='person-name']/span/text()"
                )

                yield item_loader.load_item()


def split_address(address, get):
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
