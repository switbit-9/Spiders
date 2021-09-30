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
import dateparser


class MySpider(Spider):
    name = "address_re_be"
    start_urls = ["https://www.address-re.be/nl/te-huur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[@class='property-list']//div[contains(@class,'span2 property')]/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.address-re.be/nl/te-huur?view=list&page={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("title", "//h3[@class='pull-left leftside']")
        item_loader.add_xpath(
            "description", "//div[div[.='Omschrijving']]//div[@class='field']/text()"
        )
        price = response.xpath(
            "//h3[@class='pull-right rightside']//text()[contains(., '€')]"
        ).extract_first()
        item_loader.add_xpath("rent", price.split("€ ")[1])
        item_loader.add_value("currency", "EUR")

        property_type = response.xpath(
            "//h3[@class='pull-left leftside']/text()"
        ).extract_first()
        if property_type:
            property_type = property_type.split("(")[0].split(" ")[-4].strip()
            item_loader.add_value("property_type", property_type)
        item_loader.add_xpath(
            "external_id",
            "//div[div[@class='group-container']]//div[@class='field'][1]/div[@class='value']",
        )
        square_meters = response.xpath(
            "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Bewoonbare opp.']]/div[@class='value']/text()"
        ).extract_first()
        if square_meters:
            item_loader.add_value("square_meters", square_meters.split("m²")[0])
            item_loader.add_xpath(
                "square_meters",
                "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Bewoonbare opp.']]/div[@class='value']",
            )

            room = response.xpath(
                "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Aantal slaapkamers']]/div[@class='value']"
            ).get()
            if room:
                item_loader.add_value("room_count", room)

                available_date = response.xpath(
                    "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Beschikbaarheid']]/div[@class='value']/text()[. != 'Onmiddelijk' and . != 'Overeen te komen']"
                ).get()
                if available_date:
                    date_parsed = dateparser.parse(
                        available_date, date_formats=["%d/%m/%Y"]
                    )
                    date2 = date_parsed.strftime("%Y-%m-%d")
                    item_loader.add_value("available_date", date2)

                utilities = response.xpath(
                    "//div[div[.='Lasten']]//div[@class='field' and ./div[.='Lasten huurder']]//div[@class='value']//text()"
                ).extract_first()
                if utilities:
                    item_loader.add_value("utilities", utilities.split("€ ")[1])

                terrace = response.xpath(
                    "//div[div[.='Composition']]//div[@class='field']/div[@class='value']"
                ).get()
                if terrace:
                    item_loader.add_value("terrace", True)

                terrace = response.xpath(
                    "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Gemeubileerd']]/div[@class='value' and .='Ja']"
                ).get()
                if terrace:
                    if terrace == "Ja":
                        item_loader.add_value("furnished", True)
                    else:
                        item_loader.add_value("furnished", False)

                terrace = response.xpath(
                    "//div[div[@class='group-container']]//div[@class='field' and ./div[.='Garage']]/div[@class='value']"
                ).get()
                if terrace:
                    item_loader.add_value("parking", True)

                terrace = response.xpath(
                    "//div[div[.='Comfort']]//div[@class='field' and ./div[.='Lift']]/div[@class='value' and .='Ja']"
                ).get()
                if terrace:
                    if terrace == "Ja":
                        item_loader.add_value("elevator", True)
                    else:
                        item_loader.add_value("elevator", False)

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//ul[@class='thumbnails']/li/a/img/@src"
                    ).extract()
                ]
                item_loader.add_value("images", images)

                address = response.xpath(
                    "//div[div[@class='group-container']]//div[@class='field' and ./div[@class='name' and .='Adres']]/div[@class='value']/text()"
                ).extract_first()
                item_loader.add_value("address", address)
                item_loader.add_value("zipcode", split_address(address, "zip"))
                item_loader.add_value("city", split_address(address, "city"))

                energy = response.xpath(
                    "//div[div[.='Stedenbouwkundige informatie']]//div[@class='field' and ./div[.='EPC']]/div[@class='value']/text()"
                ).get()
                if energy:
                    item_loader.add_value("energy_label", energy.split("&")[0])

                item_loader.add_value("landlord_name", "Address Real Estate")
                item_loader.add_value("landlord_email", "info@address-re.be")
                item_loader.add_value("landlord_phone", "+32 (0)2 64 62 561")

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
    else:
        # temp = address.split(" ")[0]
        zip_code = "".join(filter(lambda i: i.isdigit(), address))
        city = address.split(zip_code)[1]

        if get == "zip":
            return zip_code
        else:
            return city
