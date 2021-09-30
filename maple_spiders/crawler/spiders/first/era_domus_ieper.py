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
    name = "era_domus_ieper"
    start_urls = ["https://www.era.be/nl/te-huur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[contains(@class,'era-search--result-nodes')]/div[contains(@class,'node-property')]//div[contains(@class,'field-name-node-link')]//a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.era.be/nl/te-huur?page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@class='field-item']/p")
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("currency", "EUR")
        rent = response.xpath(
            "normalize-space(//div[@class='total-rent-price']/text())"
        ).get()
        if rent:
            item_loader.add_value(
                "rent", rent.split("/")[0].split("€")[1].replace(" ", "")
            )

            item_loader.add_xpath(
                "external_id",
                "//div[@class='field-name-field-publication-number field-type-text']/div",
            )
            square = response.xpath(
                "normalize-space(//div[@class='field-name-copy-oppervlakte-bewoonbaar field-type-number-decimal' or @class='field-name-era-oppervlakte-grond--c field-type-number-decimal']/div/text())"
            ).get()
            if square:
                item_loader.add_value("square_meters", square.split("m²")[0])
                room = response.xpath(
                    "normalize-space(//div[@class='property--intro']/div[@class='field-name-era-aantal-slaapkamers--c field-type-text']//div[@class='era-tooltip-field'])"
                ).get()
                if room:
                    item_loader.add_value("room_count", room)
                    item_loader.add_xpath(
                        "property_type",
                        "//div[@class='field-name-field-property-type field-type-entityreference']/div",
                    )
                    item_loader.add_xpath(
                        "available_date",
                        "normalize-space(//table[@class='BodyText']//tr[./td[.='vrij :']]/td[2])",
                    )
                    item_loader.add_xpath(
                        "floor",
                        "(//div[@class='field-name-era-verdieping--c field-type-number-decimal'])[2]/div/text()",
                    )

                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//div[@class='field-name-field-property-main-visual field-type-image']//img/@src"
                        ).extract()
                    ]
                    item_loader.add_value("images", images)

                    address = "".join(
                        response.xpath(
                            "//div[@class='field-name-era-adres--c field-type-text notranslate']//a//text()"
                        ).extract()
                    )
                    addres = "".join(
                        response.xpath(
                            "//div[@class='field-name-era-adres--c field-type-text notranslate']//a/span[2]/text()"
                        ).extract()
                    )
                    if address:
                        item_loader.add_value("address", address)
                        item_loader.add_value("zipcode", split_address(addres, "zip"))
                        item_loader.add_value("city", split_address(addres, "city"))
                    else:
                        item_loader.add_xpath(
                            "address",
                            "//div[@class='field-name-era-adres--c field-type-text notranslate']/div/text()",
                        )

                    terrace = response.xpath(
                        "//div[@class='field-item even']/h2[contains(text(),'Terras')]"
                    ).get()
                    if terrace:
                        item_loader.add_value("terrace", True)

                    terrace = response.xpath(
                        "//div[@class='field-item even']/h2[contains(text(),'Garage')]"
                    ).get()
                    if terrace:
                        item_loader.add_value("parking", True)

                    latlong = response.xpath(
                        "//div[@id='era-property-map']/iframe/@src"
                    ).get()
                    if latlong:
                        latitude, longitude = linkToLatLong(latlong)
                        if latitude != "" and longitude != "":
                            item_loader.add_value("latitude", latitude)
                            item_loader.add_value("longtitude", longitude)

                    landlord_name = response.xpath(
                        "(//div[@class='ds-1col node node-property-contact view-mode-full clearfix'])[1]/h3/text()"
                    ).get()
                    if landlord_name:
                        item_loader.add_value("landlord_name", landlord_name)

                    phone = response.xpath(
                        '//div[@class="property-contact-person"]//div/a[contains(@href, "tel:")]/@href'
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_phone", phone.replace("tel:", "")
                        )

                    email = response.xpath(
                        "normalize-space(//div[@class='field-name-property-contact-email field-type-text']//a)"
                    ).get()
                    if email:
                        item_loader.add_value("landlord_email", email)

                    energy_label = response.xpath(
                        "//div[@class='field-name-field-energy-label field-type-text']/div/img/@src"
                    ).get()
                    if energy_label:
                        item_loader.add_value(
                            "energy_label",
                            (
                                ((energy_label.split("/")[-1]).split("_")[1]).split(
                                    "."
                                )[0]
                            ).upper(),
                        )

                    yield item_loader.load_item()


def split_address(address, get):
    if address is not None:
        zip_code = "".join(filter(lambda i: i.isdigit(), address))
        city = address.split(" ")[-1]

        if get == "zip":
            return zip_code
        else:
            return city


def linkToLatLong(link):
    latlong = link.split("=")[2]
    latitude, longitude = latlong.split(",")[0], latlong.split(",")[1]
    return latitude, longitude
