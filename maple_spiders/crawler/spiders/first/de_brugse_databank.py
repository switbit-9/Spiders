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
import unicodedata
import dateparser


class MySpider(Spider):
    name = "de_brugse_databank"
    start_urls = [
        "https://www.de-brugse-databank.be/Producten/Tehuur/AanbodTehuur.html"
    ]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        for item in response.xpath(
            "//article//div[@class='folio-info']/a[1]/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "div.col-lg-9.col-md-9.col-sm-9 > h2")
        item_loader.add_xpath(
            "description", "//div[@class='col-lg-7 col-md-7 col-sm-8']//p"
        )
        price = response.xpath(
            "//div[@class='col-lg-3 col-md-3 col-sm-3']//h2/text()"
        ).extract_first()
        if price:
            r = unicodedata.normalize("NFKD", price)
            item_loader.add_value("rent", r.split("€ ")[1].replace(" ", ""))
            item_loader.add_value("currency", "EUR")

        ref = response.xpath("//div[@class='col-lg-3 col-md-3 col-sm-3']//h4").get()
        ref = ref.split(".")[1]
        item_loader.add_value("external_id", ref)
        square = response.xpath(
            "//tr[./td[.='Bewoonbare opp. m²' or .='Opp.bebouwd m²' or .='Living opp. in m²']]/td[2]/text()"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
            item_loader.add_xpath("property_type", "//tr[./td[.='Type pand']]/td[2]")

            available_date = response.xpath(
                "//tr[./td[.='Datum vrij']]/td[2]/text()"
            ).get()
            if available_date:
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d/%m/%Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

            room = response.xpath("//tr[./td[.='Aantal slaapkamers']]/td[2]").get()
            if room:
                item_loader.add_value("room_count", room)
                item_loader.add_xpath(
                    "floor", "//tr[./td[text()='Verdieping']]/td[2]/text()"
                )

                terrace = response.xpath("//tr[./td[text()='Terras']]/td[2]").get()
                if terrace:
                    item_loader.add_value("terrace", True)

                terrace = response.xpath("//tr[./td[.='Gemeubeld']]/td[2]").get()
                if terrace:
                    item_loader.add_value("furnished", True)

                terrace = response.xpath(
                    "//tr[./td[text()='Type pand']]/td[.='Garage']"
                ).get()
                if terrace:
                    item_loader.add_value("parking", True)

                terrace = response.xpath("//tr[./td[text()='Lift']]/td[2]").get()
                if terrace:
                    item_loader.add_value("elevator", True)

                item_loader.add_xpath(
                    "energy_label", "//tr[./td[.='EPC label']]/td[2]/text()"
                )
                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//div[@id='main-slider']/ul/li/img/@src"
                    ).extract()
                ]
                if images:
                    item_loader.add_value("images", images)
                address = response.xpath(
                    "//div[@class='col-lg-9 col-md-9 col-sm-9']//h4//text()"
                ).extract_first()
                if address:
                    item_loader.add_value("address", address)
                    city = address.split("(")[0]
                    zipcode = address.split("(")[1].split(")")[0]
                    item_loader.add_value("zipcode", zipcode)
                    item_loader.add_value("city", city)

                phone = response.xpath(
                    '//h1[@class="section-title"]/a[contains(@href, "tel:")]/@href'
                ).get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
                email = response.xpath(
                    '//div[@class="contact-info"]//a[contains(@href, "mailto:")]/@href'
                ).get()
                if email:
                    item_loader.add_value(
                        "landlord_email", email.replace("mailto:", "")
                    )
                item_loader.add_value("landlord_name", "De Brugse Databank")
                dishwasher = response.xpath(
                    "//tr[./td[.='Keukentoestellen']]/td[.='Vaatwas']"
                ).get()
                if dishwasher:
                    item_loader.add_value("dishwasher", True)

                yield item_loader.load_item()
