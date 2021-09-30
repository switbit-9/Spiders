# -*- coding: utf8 -*-
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
from datetime import datetime


class MySpider(Spider):
    name = "nadimmo"
    start_urls = ["https://www.nadimmo.be/Search/For%20Rent"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        seen = False
        url = response.xpath("//div[@class='grid']/div[contains(@class,'list-item')]")
        for item in url:
            follow_url = response.urljoin(item.xpath("./a/@href").extract_first())
            address = item.xpath(".//h4/text()").extract_first()
            if "javascript" not in follow_url:
                yield Request(
                    follow_url, callback=self.populate_item, meta={"address": address}
                )
            seen = True

        if page <= 13:
            url = f"https://www.nadimmo.be/Search/For%20Rent/PageNumber-{page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        address = response.meta.get("address")

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@class='row']/following-sibling::p")
        price = response.xpath(
            "//table[@class='table table-striped']//tr[./td[.='Price']]/td[2]/text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[0])
            item_loader.add_value("currency", "EUR")

        item_loader.add_xpath("external_id", "//a[@class='btn btn-primary']/span[2]/b")
        square = response.xpath(
            "//table[@class='table table-striped']//tr[./td[.='Net living area']]/td[2]/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        prop = response.xpath("//title/text()[contains(., '€')]").extract_first()
        if prop:
            item_loader.add_value("property_type", prop.split(" ")[0])
        item_loader.add_xpath(
            "room_count",
            "//table[@class='table table-striped']//tr[./td[.='Bedrooms']]/td[2]/text()",
        )

        date = response.xpath(
            "//tr[./td[.='Availability']]/td[2]/text()[contains(.,'/')]"
        ).extract_first()
        if date:
            item_loader.add_value(
                "available_date",
                datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d"),
            )

        item_loader.add_value("address", address)
        item_loader.add_value("city", address)

        utilities = response.xpath(
            "//table[@class='table table-striped']//tr[./td[.='Charges']]/td[2][contains(., '€')]"
        ).extract_first()
        if utilities:
            item_loader.add_value("utilities", utilities.split("€")[0])

        item_loader.add_xpath(
            "floor",
            "//table[@class='table table-striped']//tr[contains(.,'Number of floors')]/td[2]/text()",
        )

        terrace = response.xpath("//tr[./td[.='Terrace']]/td[.='Yes']/text()").get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("terrace", True)
            elif terrace == "No":
                item_loader.add_value("terrace", False)
        terrace = response.xpath(
            "//table[@class='table table-striped']//tr[./td[.='Furniture' or .='Furnished']]/td[2]/text()"
        ).get()
        if terrace:
            if "Yes" in terrace:
                item_loader.add_value("furnished", True)
            elif "No" in terrace:
                item_loader.add_value("furnished", False)

        terrace = response.xpath("//tr[@id='contentHolder_parkingZone']/td[2]").get()
        if terrace:
            item_loader.add_value("parking", True)
        else:
            terrace = response.xpath("//tr[td[.='Parking places']]/td[2]").get()
            if terrace:
                item_loader.add_value("parking", True)
            # else:
            #     item_loader.add_value("parking", False)

        terrace = response.xpath(
            "//tr[@id='contentHolder_interiorList_detailZone_3']/td[.='Yes']"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("elevator", True)
            else:
                item_loader.add_value("elevator", False)

        energy = response.xpath("//img[@alt='peb']/@src").get()
        if energy:
            item_loader.add_value(
                "energy_label",
                energy.split(
                    "https://bbl.evosys.be/Virtual/ETTW3b/v3/images/PEB/large/NL/"
                )[1]
                .split(".")[0]
                .upper(),
            )
        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[@class='carousel-inner']/div/div/img/@src"
            ).extract()
        ]
        if images:
            item_loader.add_value("images", images)
        # email = response.xpath("//div[@class='col-md-12 text-center']/address/a/text()").get()
        # if email:
        item_loader.add_value("landlord_email", " info@nadimmo.be")

        item_loader.add_value("landlord_name", "NADIMMO Ltd")
        item_loader.add_value("landlord_phone", "00322/280.03.03")

        dishwasher = response.xpath(
            "//tr[contains(.,'Indoor facilities')]/td[2]/text()[contains(.,'Dishwasher')]"
        ).extract_first()
        if dishwasher:
            item_loader.add_value("dishwasher", True)

        yield item_loader.load_item()
