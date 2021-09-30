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
    name = "era_be"
    start_urls = ["http://www.era.be/"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 1)

        # text = bytes(response.body.decode('utf-8').split('","url_array"')[0].split('"nodes":"')[-1], 'utf-8').decode('unicode-escape')
        # selector = Selector(text=text)

        seen = False
        for item in response.css(
            "div.results--container div.field-item > a::attr(href)"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            url = f"https://www.era.be/nl/te-huur?page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "div.property--intro h1")
        item_loader.add_xpath(
            "description",
            "//div[@class='fieldset-wrapper']//div[@class='field-item']/*[self::p or self::ul/li]//text()",
        )
        price = response.xpath(
            "//div[@class='group-prices hide-mobile']/div/text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value(
                "rent", price.split("€")[1].split(" / ")[0].strip().replace(" ", "")
            )
            item_loader.add_value("currency", "EUR")

            item_loader.add_xpath(
                "external_id",
                "//div[@class='field-name-field-publication-number field-type-text']/div",
            )
            square = response.xpath(
                "normalize-space(//div[@class='field-name-copy-oppervlakte-bewoonbaar field-type-number-decimal' or @class='field-name-era-oppervlakte-grond--c field-type-number-decimal']/div/text())"
            ).extract_first()
            if square:
                item_loader.add_value("square_meters", square.split("m²")[0])
                item_loader.add_xpath(
                    "property_type",
                    "//div[@class='field-name-field-property-type field-type-entityreference']/div",
                )
                room = response.xpath(
                    "normalize-space(//div[@class='property--intro']/div[@class='field-name-era-aantal-slaapkamers--c field-type-text']//div[@class='era-tooltip-field']/text())"
                ).get()
                if room:
                    item_loader.add_value("room_count", room)
                    item_loader.add_xpath(
                        "available_date",
                        "normalize-space(//table[@class='BodyText']//tr[./td[.='vrij :']]/td[2])",
                    )
                    # item_loader.add_xpath("utilities", "//div[@class='field-name-era-nutsvoorzieningen--c field-type-text']/div[@class='field-items']")

                    floor = response.xpath(
                        "normalize-space(//div[@class='field-name-era-verdieping--c field-type-number-decimal']/div/text())"
                    ).get()
                    if floor:
                        item_loader.add_value("floor", floor)

                    elevator = response.xpath(
                        "//div[@class='field-name-era-lift--c field-type-list-boolean']/label/text()"
                    ).get()
                    if elevator:
                        item_loader.add_value("elevator", True)

                    energy_label = response.xpath(
                        "normalize-space(//div[@class='field-item']/img/@src)"
                    ).extract_first()
                    if energy_label:
                        item_loader.add_value(
                            "energy_label",
                            energy_label.split("_")[1].split(".")[0].upper(),
                        )

                    dishwasher = " ".join(
                        response.xpath(
                            "//div[@class='field-item odd'][1]/div[@class='field-name-field-property-item-items field-type-text']/div/div/text()"
                        ).extract()
                    )
                    if "Vaatwasser" in dishwasher:
                        item_loader.add_value("dishwasher", True)

                    latlong = response.xpath(
                        "//div[@id='era-property-map']/iframe/@src"
                    ).extract_first()
                    if latlong:
                        item_loader.add_value(
                            "latitude", latlong.split("q=")[1].split(",")[0]
                        )
                        item_loader.add_value(
                            "longtitude", latlong.split("q=")[1].split(",")[1]
                        )

                    floor_plan_images = response.xpath(
                        "//div[@class='field-item']/span/a/@href"
                    ).extract_first()
                    if floor_plan_images:
                        item_loader.add_value("floor_plan_images", floor_plan_images)

                    address = response.xpath(
                        "//div[@class='field-name-era-adres--c field-type-text notranslate']/div[@class='field-item']/a/span[2]/text()"
                    ).extract_first()
                    if address:
                        item_loader.add_value("address", address)
                        item_loader.add_value("zipcode", split_address(address, "zip"))
                        item_loader.add_value("city", split_address(address, "city"))
                    else:
                        item_loader.add_xpath(
                            "address",
                            "//div[@class='field-name-era-adres--c field-type-text notranslate']/div/text()",
                        )
                    item_loader.add_xpath(
                        "landlord_name",
                        "normalize-space(//div[@class='property-contact-person']//h3)",
                    )
                    item_loader.add_xpath(
                        "landlord_email",
                        "normalize-space(//div[@class='field-name-property-contact-email field-type-text']//a)",
                    )
                    phone = response.xpath(
                        "normalize-space(//div[@class='field-name-property-contact-phone field-type-text']//a)"
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_phone", phone.replace("tel:", "")
                        )

                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//div[contains(@class,'slick-item')]/img/@src"
                        ).extract()
                    ]
                    if images:
                        item_loader.add_value("images", images)

                    terrace = response.xpath(
                        "//div[@class='field-item odd']/h2[contains(text(),'Terras')]/text()"
                    ).get()
                    if terrace:
                        item_loader.add_value("terrace", True)

                    yield item_loader.load_item()


def split_address(address, get):
    if address is not None:
        zip_code = "".join(filter(lambda i: i.isdigit(), address))
        city = address.split(" ")[-1]

        if get == "zip":
            return zip_code
        else:
            return city
