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
import dateparser


class MySpider(Spider):
    name = "immobastogne"
    start_urls = [
        "https://www.immobastogne.be/Search/Appartement%20For%20rent%20/For%20rent/Type-03%7CAppartement/Localisation-/Prix-/Tri-PRIX%20ASC,COMM%20ASC,CODE/"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        # page = response.meta.get('page', 2)
        urls = [
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006827898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006815898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006816898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006969898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006991898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00007002898/Lang-EN",
            "/fiche/%20for%20rent%20Bertogne/Code-00005601898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006962898/Lang-EN",
            "/fiche/%20for%20rent%20Bastogne/Code-00006994898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006976898/Lang-EN",
            "/fiche/%20for%20rent%20SAINTE-ODE/Code-00006860898/Lang-EN",
            "/fiche/%20for%20rent%20BASTOGNE/Code-00006825898/Lang-EN",
            "/fiche/%20for%20rent%20VAUX-SUR-SURE/Code-00006958898/Lang-EN",
            "/fiche/%20for%20rent%20HOUFFALIZE/Code-00006797898/Lang-EN",
            "/fiche/%20for%20rent%20HOUFFALIZE/Code-00006998898/Lang-EN",
        ]

        for item in urls:
            follow_url = response.urljoin(item)
            # property_type= item.xpath(".//div[@class='estate-type']/text()").extract_first()
            # if "javascript" not in follow_url:
            yield Request(follow_url, callback=self.populate_item)
            # print(follow_url)
        # if page == 2:
        #     url = f"https://www.immobastogne.be/Search/For%20Rent/Type-/Localisation-/Prix-/Tri-ESIW_DATE%20DESC,CODE/PageNumber-{page}"
        #     yield Request(url, callback=self.parse, meta={"page": page+1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        property_type = "apartment"

        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@class='col-md-6']/p")
        rent = response.xpath(
            "//tr[td[.='Price']]/td/text()[contains(., '€')]"
        ).extract_first()
        if rent:
            item_loader.add_value("rent", rent)
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("currency", "EUR")
        item_loader.add_xpath("external_id", "//div[@class='ref-tag']//span/b")

        square = response.xpath(
            "//tr[td[.='Net living area']]/td[2]/text()"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

            item_loader.add_xpath("room_count", "//tr[td[.='Bedrooms']]/td[2]/text()")
            date = response.xpath(
                "//tr[td[.='Availability']]/td/text()[contains(.,'/')]"
            ).extract_first()
            if date:
                date_parsed = dateparser.parse(date, date_formats=["%d/%m/%Y"])
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

            energy_label = response.xpath(
                "normalize-space(//div[contains(@class,'container')]//div/img/@src)"
            ).extract_first()
            if energy_label:
                item_loader.add_value(
                    "energy_label", energy_label.split("L/")[1].split(".")[0].upper()
                )

            # property_type = response.xpath("//h1/text()").get()
            item_loader.add_value("property_type", property_type)

            address = response.xpath(
                "//div[@id='adresse_fiche']/p/text()"
            ).extract_first()
            if address:
                item_loader.add_value("address", address)
                item_loader.add_value("zipcode", split_address(address, "zip"))
                item_loader.add_value("city", split_address(address, "city"))
                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//div[@class='carousel-inner hvr-grow']/div/a/img/@src"
                    ).extract()
                ]
                item_loader.add_value("images", images)

                terrace = response.xpath("//tr[td[.='Terrace']]/td[2]/text()").get()
                if terrace:
                    if terrace == "Yes":
                        item_loader.add_value("terrace", True)
                    elif terrace == "No":
                        item_loader.add_value("terrace", False)
                    elif "m²" in terrace:
                        item_loader.add_value("terrace", True)

                terrace = response.xpath("//tr[td[.='Furnished']]/td[2]/text()").get()
                if terrace:
                    if terrace == "Yes":
                        item_loader.add_value("furnished", True)
                    elif terrace == "No":
                        item_loader.add_value("furnished", False)

                item_loader.add_value("landlord_name", "IMMO BASTOGNE")
                item_loader.add_xpath(
                    "landlord_email",
                    "//div[@class='col-md-12 text-center']/address/a/text()",
                )
                item_loader.add_value("landlord_phone", "061/21.70.91")
                yield item_loader.load_item()


def split_address(address, get):
    if "-" in address:
        temp = address.split("-")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(" ")[1]

        if get == "zip":
            return zip_code
        else:
            return city
