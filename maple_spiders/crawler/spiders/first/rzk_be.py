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
import re
import dateparser


class MySpider(Spider):
    name = "rzk_be"
    start_urls = [
        "https://www.rzk.be/nl/verhuur/woning/",
        "https://www.rzk.be/nl/verhuur/appartement/",
        "https://www.rzk.be/nl/verhuur/bedrijfsvastgoed/",
        "https://www.rzk.be/nl/verhuur/bedrijfsvastgoed/",
        "https://www.rzk.be/nl/verhuur/garage/",
    ]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        for item in response.xpath(
            "//div[@id='tab-list']/ul/li//div[@class='photo first']/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(
            response.xpath("//div[contains(@class,'text-center')]/h1/text()").extract()
        )
        item_loader.add_value(
            "title", title.strip().replace("\n                        ", "")
        )

        desc = " ".join(
            response.xpath(
                "//div[@class='detail-info-block']/div/span/text()"
            ).extract()
        )
        item_loader.add_value("description", desc.strip())

        price = response.xpath(
            "//tr[td[.='Prijs']]/td[@class='value'][contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1])
            item_loader.add_value("currency", "EUR")

        square = response.xpath(
            "//tr[td[.='Woonoppervlakte']]/td[@class='value']"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m")[0])

            address = "".join(
                response.xpath(
                    "//div[contains(@class,'text-center')]/h1/text()"
                ).extract()
            ).strip()
            item_loader.add_value("address", re.sub("\s{2,}", " ", address))
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

            item_loader.add_xpath(
                "property_type", "//div[@class='page-title-block row']/h3"
            )

            room = response.xpath(
                "//tr[td[.='Aantal slaapkamers']]/td[@class='value']"
            ).get()
            if room:
                item_loader.add_value("room_count", room)
                available_date = response.xpath(
                    "//tr[td[.='Vrij op']]/td[@class='value']/text()[. !='onmiddellijk' and .!= 'na opzeg huurovereenkomst']"
                ).get()
                if available_date:
                    date_parsed = dateparser.parse(
                        available_date, date_formats=["%d/%m/%Y"]
                    )
                    date2 = date_parsed.strftime("%Y-%m-%d")
                    item_loader.add_value("available_date", date2)
                item_loader.add_xpath(
                    "floor",
                    "normalize-space(//tr[td[.='Verdieping']]/td[@class='value']/text())",
                )
                energy = response.xpath(
                    "//table[@class='epc detail-fields']//td[@class='value']/text()[not(contains(.,'kWh'))][1]"
                ).get()
                if energy:
                    item_loader.add_value("energy_label", energy.strip())

                terrace = response.xpath(
                    "//tr[td[.='Terras']]/td/text()"
                ).extract_first()
                if terrace:
                    if terrace is not None:
                        item_loader.add_value("terrace", True)
                    else:
                        item_loader.add_value("terrace", False)

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//a[@rel='property-pictures']/@href"
                    ).extract()
                ]
                if images:
                    item_loader.add_value("images", images)

                floor_images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//table[@class='downloads detail-fields']//tr[./td/a[.='Grondplan']]//a/@href"
                    ).extract()
                ]
                if floor_images:
                    item_loader.add_value("floor_plan_images", floor_images)

                terrace = response.xpath(
                    "//tr[td[.='Aantal parkeerplaatsen' or .='Tuin aanwezig']]/td[@class='value']"
                ).extract_first()
                if terrace:
                    if terrace is not None:
                        item_loader.add_value("parking", True)
                    else:
                        item_loader.add_value("parking", False)

                phone = response.xpath(
                    '//div[@id="footer-contact"]/div/a[contains(@href, "tel:")]/@href'
                ).get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
                item_loader.add_value("landlord_name", "Rzk")
                item_loader.add_value("landlord_email", "info@rzk.be")

                item_loader.add_xpath("latitude", "//div[@id='map']/@data-geolat")
                item_loader.add_xpath("longtitude", "//div[@id='map']/@data-geolong")
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
