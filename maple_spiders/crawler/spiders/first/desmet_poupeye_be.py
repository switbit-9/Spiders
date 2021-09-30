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


class MySpider(Spider):
    name = "desmet_poupeye_be"
    start_urls = [
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=1",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=2",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=3",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=4",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=5",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=6",
        # 'http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=12',
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=14",
        "http://www.desmet-poupeye.be/pages/selectie.asp?Aanbod=H&Type=15",
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        if "Type=1" in response.url:
            prop_type = "villa"
        elif "Type=2" in response.url:
            prop_type = "appartement"
        elif "Type=3" in response.url:
            prop_type = "studio"
        elif "Type=4" in response.url:
            prop_type = "gemeubelde"
        elif "Type=5" in response.url:
            prop_type = "Handelspanden"
        elif "Type=6" in response.url:
            prop_type = "garage"
        elif "Type=14" in response.url:
            prop_type = "bedrijfsvastgoed"
        elif "Type=15" in response.url:
            prop_type = "assistentiewoning"

        for item in response.xpath("//table//td/a[@class='Title']/@href").extract():
            follow_url = response.urljoin(item)
            yield Request(
                follow_url, callback=self.populate_item, meta={"prop_type": prop_type}
            )

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "span.title2")
        item_loader.add_xpath(
            "description",
            "//table[@class='BodyText']//tr[./td[.='omschrijving :']]/td[2]",
        )
        price = response.xpath(
            "normalize-space(//table[@class='BodyText']//tr[./td[.='prijs :']]/td[2])"
        ).extract_first()
        if price:
            r = unicodedata.normalize("NFKD", price)
            item_loader.add_value("rent", r.split("€")[1].replace(",", ""))
            item_loader.add_value("currency", "EUR")
        item_loader.add_xpath(
            "available_date",
            "normalize-space(//table[@class='BodyText']//tr[./td[.='vrij :']]/td[2])",
        )
        item_loader.add_xpath(
            "energy_label", "//table[@class='BodyText']//tr[./td[.='EPC :']]/td[2]"
        )
        address = response.xpath(
            "normalize-space(//table[@class='BodyText']//tr[./td[.='ligging :']]/td[2])"
        ).extract_first()
        item_loader.add_value("address", address)
        item_loader.add_value("zipcode", split_address(address, "zip"))
        item_loader.add_value("city", split_address(address, "city"))
        # images = response.xpath("//a[@target='Detail_iframe']/img/@src").get()
        images = [
            response.urljoin(x)
            for x in response.xpath("//a[@target='Detail_iframe']/img/@src").extract()
        ]
        item_loader.add_value("images", images)

        item_loader.add_value("property_type", response.meta.get("prop_type"))

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
