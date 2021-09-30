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
    name = "rencura_be"
    start_urls = ["https://rencura.be/api/estates/1"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        data = json.loads(response.body)

        for item in data["data"]:
            if "te-huur" in item["url"]:
                yield Request(item["url"], callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        # https://rencura.be/aanbod?transactions=12771 -- listing url

        item_loader.add_css("title", "h1")
        item_loader.add_value("external_link", response.url)
        desc = "".join(
            response.xpath("//div[@class='Content Content--left']/text()").extract()
        )
        item_loader.add_value("description", desc.strip())
        price = response.xpath(
            "//div[@class='ProjectInfo-price']/text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1])
            item_loader.add_value("currency", "EUR")

        ref = "".join(
            response.xpath("//span[@class='ProjectDetail-reference']//text()").extract()
        )
        if ref:
            if ":" in ref:
                ref = ref.strip().split(":")[1]
                item_loader.add_value("external_id", ref)

        square = response.xpath(
            "//div[@class='ProjectInfo-icon']/text()[contains(., 'm')]"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m")[0])

        available_date = response.xpath(
            "//dl[@class='Table-list Table-list--columns']/div[./dt[.='Beschikbaar vanaf']]/dd/text()[. != 'onmiddellijk' and . != 'vanaf akte' and . != 'bij oplevering' and . != 'in onderling overleg' and . != 'af te spreken met eigenaar' and . != 'mits inachtneming huurders']"
        ).get()
        if available_date:
            item_loader.add_value("available_date", available_date)

        property_type = "".join(
            response.xpath("//div[@class='ProjectInfo-type']/a[1]/text()").extract()
        )
        if property_type:
            item_loader.add_value("property_type", property_type.split("/")[0].strip())

        room = response.xpath(
            "//dl[@class='Table-list Table-list--columns']/div[./dt[text()='Slaapkamers']]/dd/text()"
        ).get()
        if room:
            item_loader.add_value("room_count", room)

            terrace = response.xpath(
                "//dl[@class='Table-list Table-list--columns']/div[./dt[text()='Terras']]/dd/text()"
            ).get()
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("terrace", True)
                elif "Yes" in terrace:
                    item_loader.add_value("terrace", True)
                elif "No" in terrace:
                    item_loader.add_value("terrace", False)
                else:
                    item_loader.add_value("terrace", False)

            terrace = response.xpath(
                "//dl[@class='Table-list Table-list--columns']/div[./dt[.='Garage']]/dd/text()"
            ).get()
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("parking", True)
                elif "Yes" in terrace:
                    item_loader.add_value("parking", True)
                elif "No" in terrace:
                    item_loader.add_value("parking", False)
                else:
                    item_loader.add_value("parking", False)

            terrace = response.xpath(
                "//dl[@class='Table-list Table-list--columns']/div[./dt[.='Gemeubeld']]/dd/text()"
            ).get()
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("furnished", True)
                elif "Yes" in terrace:
                    item_loader.add_value("furnished", True)
                elif "No" in terrace:
                    item_loader.add_value("furnished", False)
                else:
                    item_loader.add_value("furnished", False)

            terrace = response.xpath(
                "//dl[@class='Table-list']/div[./dt[.='Lift']]/dd/text()"
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

            swimming_pool = response.xpath(
                "//dl[@class='Table-list Table-list--columns']/div[./dt[.='Zwembad']]/dd/text()"
            ).get()
            if swimming_pool:
                if "Ja" in swimming_pool:
                    item_loader.add_value("swimming_pool", True)
                elif "Yes" in swimming_pool:
                    item_loader.add_value("swimming_pool", True)
                elif "No" in swimming_pool:
                    item_loader.add_value("swimming_pool", False)
                else:
                    item_loader.add_value("swimming_pool", False)
            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='Thumbnail-items']/div/img/@src"
                ).extract()
            ]
            if images:
                item_loader.add_value("images", images)

            item_loader.add_xpath(
                "energy_label",
                "//dl[@class='Table-list Table-list--columns']/div[./dt[.='EPC-label']]/dd/text()[ . != 'IN AANVRAAG']",
            )

            address = response.xpath(
                "//a[@class='AddressLine AddressLine--full u-marginBlg js-fakeAddressLine']"
            ).extract_first()
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

            item_loader.add_xpath("landlord_name", "//h2[@class='ProjectContact-name']")

            item_loader.add_xpath(
                "landlord_phone", "//div[@class='ProjectContact-phone']/a"
            )

            yield item_loader.load_item()


def split_address(address, get):
    if address is not None:
        if "," in address:
            temp = address.split(",")[1]
            zip_code = "".join(filter(lambda i: i.isdigit(), temp))
            city = temp.split(zip_code)[1]

            if get == "zip":
                return zip_code
            else:
                return city
