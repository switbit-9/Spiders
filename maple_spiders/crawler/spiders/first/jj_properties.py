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
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from scrapy import Request
from crawler.loader import MapleLoader
import dateparser


class MySpider(Spider):
    name = "jj_properties"
    start_urls = ["https://www.jj-properties.be/fr/a-louer"]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        page = response.meta.get("page", 2)

        for item in response.xpath(
            "//div[@id='search_results__list']/ul/li/div[@class='property_card']/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

        if page <= 5:
            url = f"https://www.jj-properties.be/fr/a-louer/page-{page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h1")
        desc = " ".join(
            response.xpath(
                "//div[@class='detail_desc']//text()[not(parent::h3)]"
            ).extract()
        ).strip()
        item_loader.add_value("description", desc)
        item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("description", desc)

        rent = response.xpath(
            "//div[@class='detail_meta']/p/text()[contains(., '€')]"
        ).extract_first()
        if rent:
            item_loader.add_value("rent", rent.split("p/m")[0].split(" ")[1])

        ref = response.xpath(
            "//section[@class='container container--s margin-v']/p/text()"
        ).get()
        if ref:
            item_loader.add_value("external_id", ref.split(" ")[1])

        square = response.xpath("//div[dt[.='Surface habitable:']]/dd/text()").get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

        room = response.xpath(
            "//ul/li[1]/span[@class='icon icon_feature-l icon_bedrooms text']"
        ).get()
        if room:
            item_loader.add_value("room_count", room)

            available_date = response.xpath(
                "//div[dt[.='Disponibilité:']]/dd/text()[2]"
            ).extract_first()
            if available_date:
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d %B %Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

            item_loader.add_xpath("floor", "//div[dt[.='Etage:']]/dd/text()")

            images = response.xpath("//ul[@id='detail_slider']/li/a/@href").extract()
            for x in range(1, len(images)):
                item_loader.add_value("images", response.urljoin(images[x]))

            property_type = response.xpath(
                "//h1[@class='detail_title']/span/text()"
            ).get()
            if property_type:
                item_loader.add_value(
                    "property_type", property_type.split("à louer")[0].strip()
                )

            terrace = response.xpath("//div[dt[.='Terrasse:']]/dd/text()").get()
            if terrace:
                item_loader.add_value("terrace", True)

            terrace = response.xpath("//div[dt[.='Ascenseur:']]/dd/text()").get()
            if terrace:
                if "Oui" in terrace:
                    item_loader.add_value("elevator", True)
                elif "Non" in terrace:
                    item_loader.add_value("elevator", False)
                elif "Yes" in terrace:
                    item_loader.add_value("elevator", True)
                elif "No" in terrace:
                    item_loader.add_value("elevator", False)

            parking = response.xpath(
                "//li/span[@class='icon icon_feature-l icon_garages text']"
            ).get()
            if parking:
                item_loader.add_value("parking", True)
            phone = response.xpath(
                "//div[@class='representative representative--small']//p[@class='representative__phone']/span[@class='icon icon_phone text']/text()"
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone)
            landlord_name = response.xpath(
                "//div[@class='representative representative--small']//p[@class='representative__name']/text()"
            ).get()
            if landlord_name:
                item_loader.add_value("landlord_name", landlord_name)
            item_loader.add_xpath(
                "city", "//label[@class='detail_meta__address']/span/text()"
            )

            address = response.xpath("//p[@class='detail_meta__title']/text()").get()
            if address:
                item_loader.add_value("address", address)
            yield item_loader.load_item()
