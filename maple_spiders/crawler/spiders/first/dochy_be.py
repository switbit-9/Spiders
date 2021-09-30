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
from crawler.loader import MapleLoader
from scrapy import Request
import unicodedata


class MySpider(Spider):
    name = "dochy_be"
    start_urls = ["https://www.dochy.be/nl/aanbod/te-huur/"]  # LEVEL 1

    # 1. FOLLOWING LEVEL 1
    def parse(self, response):

        for item in response.css("div#raster>ul>li>a::attr(href)").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h1.new_title")
        item_loader.add_xpath("description", "//div[@class='new_text']")
        rent = response.xpath("//strong[@itemprop='price']/text()").get()
        if rent:
            item_loader.add_value("rent", rent.replace(",", ""))
            item_loader.add_value("external_link", response.url)
            item_loader.add_xpath(
                "external_id",
                "//div[@id='cta_white']/ul/li[./span[.='Referentie']]/span[2]",
            )
            item_loader.add_value("currency", "EUR")
            square = response.xpath(
                "//div[@id='cta_white']/ul/li/span[contains(text(),'m²')]/text()"
            ).get()
            if square:
                item_loader.add_value("square_meters", square.split("m²")[0])
                property_type = response.xpath(
                    "//span[@itemprop='name']/text()"
                ).extract_first()
                if property_type:
                    item_loader.add_value(
                        "property_type", property_type.split("/")[-1].split(" - ")[0]
                    )
                item_loader.add_xpath(
                    "room_count",
                    "//div[@class='placeholder p-ends-90']/ul/li/span[contains(.,'Slaapkamers')]/span[not(self::span[@class='bold'])]",
                )
                item_loader.add_xpath(
                    "available_date",
                    "//div[@class='placeholder p-ends-90']/ul/li/span[contains(.,'Beschikbaar')]/span[not(self::span[@class='bold'])]",
                )

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//a[@class='image-grid-element']/@href"
                    ).extract()
                ]
                item_loader.add_value("images", images)

                item_loader.add_xpath(
                    "city", "normalize-space(//span[@itemprop='addressLocality'])"
                )

                item_loader.add_xpath(
                    "address", "normalize-space(//span[@itemprop='addressLocality'])"
                )

                phone = response.xpath(
                    '//div[@class="contactdata"]/a[1]/span[@class="new_text new_text--white"]'
                ).get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

                email = response.xpath(
                    '//div[@class="contactdata"]/a[3]/span[@class="new_text new_text--white"]'
                ).get()
                if email:
                    item_loader.add_value("landlord_email", email)

                yield item_loader.load_item()
