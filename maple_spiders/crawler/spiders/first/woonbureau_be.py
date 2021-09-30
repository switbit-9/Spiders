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
import re
from datetime import datetime
import math


class MySpider(Spider):
    name = "woonbureau_be"
    start_urls = [
        "https://www.woonbureau.be/huren/",
        "http://www.woonbureau.eu/te-huur?searchon=list&transactiontype=Rent",
    ]
    # 1. FOLLOWING
    def parse(self, response):

        if "https://www.woonbureau.be/huren/" in response.url:
            for item in response.xpath(
                "//div[@class='pandList']//div[contains(@class,'large-4 cell')]/div"
            ):
                follow_url = item.xpath("./a/@href").extract_first()
                square_meters = item.xpath(
                    ".//div[@class='descr']/span[contains(.,'Bewoonbare')]/text()"
                ).extract_first()
                if square_meters:
                    square_meters = math.ceil(
                        float(square_meters.split(":")[1].replace("m²", "").strip())
                    )
                    yield Request(
                        follow_url,
                        callback=self.populate_item,
                        meta={"type": "niklaas", "s_meters": square_meters},
                    )
        else:
            for item in response.xpath(
                "//div[@data-view='showOnList']/a/@href"
            ).extract():
                follow_url = response.urljoin(item)
                yield Request(
                    follow_url, callback=self.populate_item, meta={"type": "lokeren"}
                )

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        if "lokeren" in response.meta.get("type"):

            item_loader.add_value("external_link", response.url)
            title = "".join(
                response.xpath(
                    "//section[@class='container head']/h1/text()[1]"
                ).extract()
            )
            item_loader.add_value("title", re.sub("\s{2,}", " ", title).strip())
            item_loader.add_xpath("description", "//div[@id='description']/div/p")
            price = response.xpath(
                "//tr[td[.='Prijs:']]/td[@class='kenmerk']"
            ).extract_first()

            if price:
                item_loader.add_value(
                    "rent", price.split("€")[1].split("/")[0].replace("<", "")
                )
                item_loader.add_value("currency", "EUR")

            address = (
                "".join(
                    response.xpath(
                        "//section[@class='container head']/h1/text()[1]"
                    ).extract()
                )
                .split(",")[1]
                .strip()
            )
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

            item_loader.add_xpath(
                "external_id", "//tr[td[.='Referentie:']]/td[@class='kenmerk']"
            )
            item_loader.add_xpath(
                "property_type", "//tr[td[.='Type:']]/td[@class='kenmerk']/text()"
            )
            item_loader.add_xpath(
                "room_count", "//tr[td[.='Slaapkamers:']]/td[@class='kenmerk']"
            )

            date = response.xpath(
                "//tr[td[.='Beschikbaar vanaf:']]/td[@class='kenmerk']/text()[contains(.,'/')]"
            ).extract_first()
            if date:
                item_loader.add_value(
                    "available_date",
                    datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d"),
                )

            item_loader.add_xpath(
                "floor", "//tr[td[.='Op verdieping:']]/td[@class='kenmerk']/text()"
            )
            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='owl-carousel']//a/@href"
                ).extract()
            ]
            item_loader.add_value("images", images)
            terrace = response.xpath(
                "//tr[td[.='Terras:']]/td[.='Ja']/text()"
            ).extract_first()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("terrace", True)
                else:
                    item_loader.add_value("terrace", False)

            square_meters = response.xpath(
                "//tr[contains(.,'Bewoonbare opp')]/td[2]/text()"
            ).extract_first()
            if square_meters:
                square_meters = math.ceil(
                    float(square_meters.replace("m²", "").strip())
                )
                item_loader.add_value("square_meters", str(square_meters))

            # phone = response.xpath('//div[@class="col-sm-4"]/a[contains(@href, "tel:")]/@href').get()
            # if phone:
            item_loader.add_value("landlord_phone", "09 348 37 19")
            # email = response.xpath('//div[@class="col-sm-4"]/a[contains(@href, "mailto:")]/@href').get()
            # if phone:
            item_loader.add_value("landlord_email", "lokeren@woonbureau.be")
            item_loader.add_value("landlord_name", "NV Woonbureau")

            lat_long = response.xpath(
                "//script[@type='application/ld+json' and contains(.,'latitude')][1]/text()"
            ).extract_first()
            if lat_long:
                data = json.loads(lat_long)
                lat = data["geo"]["latitude"]
                log = data["geo"]["longitude"]

                item_loader.add_value("latitude", lat)
                item_loader.add_value("longtitude", log)

            pet = response.xpath(
                "//tr[contains(.,'Huisdieren toegelaten')]/td[2]/text()"
            ).extract_first()
            if pet:
                if "Neen" in pet:
                    item_loader.add_value("pets_allowed", False)

        else:
            item_loader.add_value("external_link", response.url)
            title = "".join(
                response.xpath("//div[contains(@class,'title')]/h2/text()").extract()
            )
            item_loader.add_value("title", re.sub("\s{2,}", " ", title).lstrip("- "))
            item_loader.add_xpath("description", "//div/div[@class='large-8 cell']/p")
            price = response.xpath(
                "//div/div[@class='large-6 one cell']/p[contains(.,'Huurprijs:')]/span[contains(., '€')]"
            ).extract_first()
            if price:
                item_loader.add_value("rent", price.split("€")[1])
                item_loader.add_value("currency", "EUR")

            item_loader.add_value("square_meters", str(response.meta.get("s_meters")))

            ref = "".join(
                response.xpath(
                    "//div/div[@class='large-8 cell title']/h2/span[@class='pandID']/text()"
                ).extract()
            )
            item_loader.add_value("external_id", ref.strip())
            item_loader.add_xpath(
                "property_type",
                "//div/div[@class='large-6 one cell']/p[contains(.,'Type:')]/span",
            )
            item_loader.add_xpath(
                "room_count",
                "//div/div[contains(@class,'cell')]/p[contains(.,'Slaapkamers:')]/span",
            )

            date = response.xpath(
                "//div/div[@class='large-6 one cell']/p[contains(.,'Beschikbaarheid:')]/span/text()[contains(.,'-')]"
            ).extract_first()
            if date:
                item_loader.add_value(
                    "available_date",
                    datetime.strptime(date, "%d-%m-%Y").strftime("%Y-%m-%d"),
                )

            item_loader.add_xpath(
                "energy_label",
                "//div/div[contains(@class,'cell')]/p[contains(.,'EPC:')]/span",
            )
            item_loader.add_xpath(
                "floor",
                "//div/div[contains(@class,'cell')]/p[contains(.,'Verdieping:')]/span/text()",
            )

            terrace = response.xpath(
                "//div/div[contains(@class,'cell')]/p[contains(.,'Terras:')]/span/text()[contains(., 'Ja')]"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("terrace", True)
                else:
                    item_loader.add_value("terrace", False)
            terrace = response.xpath(
                "//div/div[contains(@class,'cell')]/p[contains(.,'Lift')]/span/text()[contains(., 'Ja')]"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("elevator", True)
                else:
                    item_loader.add_value("elevator", False)

            images = [
                response.urljoin(x)
                for x in response.xpath("//ul/li/a/img/@src").extract()
            ]
            if images:
                item_loader.add_value("images", images)
            terrace = response.xpath(
                "//div/div[contains(@class,'cell')]/p[contains(.,'Garage:')]/span/text()[contains(., 'Ja')]"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("parking", True)
                else:
                    item_loader.add_value("parking", False)

            item_loader.add_value("landlord_phone", "03 777 36 77")
            # email = response.xpath('//div[@class="col-sm-4"]/a[contains(@href, "mailto:")]/@href').get()
            # if phone:
            item_loader.add_value("landlord_email", "info@woonbureau.be")
            item_loader.add_value("landlord_name", "Woonbureau Sint-Niklaas")

            address = response.xpath(
                "//div[contains(@class,'title')]/h1/text()"
            ).extract_first()
            if address:
                item_loader.add_value("address", address.replace("\t", "").strip())
                item_loader.add_value("city", address.split(",")[1])

        yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
