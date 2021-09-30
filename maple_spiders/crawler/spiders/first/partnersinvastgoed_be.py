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
import dateparser


class MySpider(Spider):
    name = "partnersinvastgoed_be"
    start_urls = [
        "https://www.partnersinvastgoed.be/te-huur?searchon=list&transactiontype=Rent"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        for item in response.xpath(
            "//div[contains(@class,'row switch-view-container')]/a[contains(@class,'pand-wrapper')]/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

        url = f"https://www.partnersinvastgoed.be/te-huur?pageindex=2&searchon=list&transactiontype=Rent"
        yield Request(url, callback=self.parse)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(
            response.xpath("//section[@class='container head']/h1/text()").extract()
        ).strip()
        item_loader.add_value("title", re.sub("\s{2,}", " ", title))
        item_loader.add_xpath(
            "description", "//div[@class='row tab description']/div/p"
        )
        price = response.xpath("//tr[./td[.='Prijs:']]/td[2]").extract_first()
        if price:
            item_loader.add_value(
                "rent", price.split("€")[1].split("/")[0].split("<")[0]
            )
            item_loader.add_value("currency", "EUR")

        address = " ".join(
            response.xpath("//tr[./td[.='Adres:']]/td[2]/text()").extract()
        )
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

        square = response.xpath(
            "//tr[./td[.='Bewoonbare opp.:']]/td[2]"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

            item_loader.add_xpath("property_type", "//tr[./td[.='Type:']]/td[2]")
            item_loader.add_xpath("room_count", "//tr[./td[.='Slaapkamers:']]/td[2]")
            floor = response.xpath("//tr[./td[.='Op verdieping:']]/td[2]/text()").get()
            if floor:
                item_loader.add_value("floor", floor)
            available_date = response.xpath(
                "//tr[./td[.='Beschikbaar vanaf:']]/td[2]/text()[. != 'Onmiddellijk' and . !='In overleg']"
            ).extract_first()
            if available_date:
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d/%m/%Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)
            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='owl-carousel']//a/@href"
                ).extract()
            ]
            item_loader.add_value("images", images)

            terrace = response.xpath("//tr[./td[.='Terras:']]/td[2]/text()").get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("terrace", True)
                elif terrace == "Nee":
                    item_loader.add_value("terrace", False)
                elif response.xpath("//tr[./td[.='Terras:']]/td[2]/text()").get():
                    item_loader.add_value("terrace", True)

            terrace = response.xpath("//tr[./td[.='Parking:']]/td[2]/text()").get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("parking", True)

            terrace = response.xpath(
                "//tr[./td[.='Lift:']]/td[2]/text()/text()[.='Ja']"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("elevator", True)
                if terrace == "Nee":
                    item_loader.add_value("elevator", False)

            phone = response.xpath('//div[@class="col-sm-4"][3]/a/@href').get()
            if phone:
                item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

            email = response.xpath('//div[@class="col-sm-4"][1]/a/@href').get()
            if email:
                item_loader.add_value("landlord_email", email.replace("mailto:", ""))

            item_loader.add_value("landlord_name", "Sofie Vynckier")
            script = " ".join(response.xpath("//script[5]/text()").extract())

            script = (
                script.strip()
                .split("PR4.detail.enableMap({")[1]
                .strip()
                .split("});")[0]
                .strip()
            )

            item_loader.add_value(
                "latitude", script.strip().split(",")[0].split(" ")[1]
            )
            item_loader.add_value(
                "longtitude",
                script.replace("            ", " ").split(",")[1].split(" ")[2],
            )
            yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
