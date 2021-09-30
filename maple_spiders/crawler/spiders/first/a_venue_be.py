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
import re


class MySpider(Spider):
    name = "a_venue_be"
    start_urls = ["https://start.a-venue.be/nl/te-huur/"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        for item in response.css("div.spotlight__image > a::attr(href)").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(response.xpath("//h1//text()").extract())
        item_loader.add_value("title", re.sub("\s{2,}", " ", title))
        item_loader.add_xpath(
            "description", "//div[@class='property__details__block__description']"
        )
        rent = response.xpath(
            "//table[@class='financial detail-fields property__details__block__table']//td[@class='value']/text()"
        ).extract_first()
        if rent:
            price = rent.split("€ ")[1].split(",")[0]
            item_loader.add_value("rent", price)
            item_loader.add_value("currency", "EUR")

        ref = response.xpath("//div[@class='property__header-block__ref']").get()
        if ref:
            ref = ref.split(":")[1]
            item_loader.add_value("external_id", ref)
        square_meters = response.xpath(
            "//tr[./td[.='Woonoppervlakte']]/td[@class='value']/text()"
        ).extract_first()
        if square_meters:
            item_loader.add_value("square_meters", square_meters.split("m²")[0])
            room = response.xpath(
                "//tr[./td[.='Aantal slaapkamers']]/td[@class='value']"
            ).get()
            if room:
                item_loader.add_value("room_count", room)
                item_loader.add_xpath(
                    "floor",
                    "//table[@class='construction property__details__block__table']//tr[./td[.='Verdieping']]/td[@class='value']/text()",
                )
                address = response.xpath(
                    "normalize-space(//div[@class='property__header-block__adress__street'])"
                ).extract_first()
                item_loader.add_value("address", address)
                item_loader.add_value("zipcode", split_address(address, "zip"))
                item_loader.add_value("city", split_address(address, "city"))
                prop = response.xpath(
                    "normalize-space(//h2[@class='property__sub-title']/text())"
                ).get()
                item_loader.add_value("property_type", prop.split(" ")[0])

                item_loader.add_xpath(
                    "latitude",
                    "//div[@class='gmap-wrapper shadowed small']/div/@data-geolat",
                )
                item_loader.add_xpath(
                    "longtitude",
                    "//div[@class='gmap-wrapper shadowed small']/div/@data-geolong",
                )

                terrace = "".join(
                    response.xpath(
                        "//table[@class='indeling detail-fields property__details__block__table']//tr[./td[.='Terras']]/td[@class='value description']/text()"
                    ).extract()
                )
                if terrace:
                    if terrace == "":
                        item_loader.add_value("terrace", True)
                    elif terrace == "No":
                        item_loader.add_value("terrace", False)

                # item_loader.add_xpath("energy_label", "normalize-space(//table[@class='epc detail-fields property__details__block__table']//tr[./td[.='EPC waarde']]/td[@class='value'])")

                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//a[@class='picture-lightbox']/@href"
                    ).extract()
                ]
                if images:
                    item_loader.add_value("images", images)
                email = response.xpath(
                    '//div[@class="footer__div"]/strong//text()'
                ).get()
                if email:
                    item_loader.add_value("landlord_email", email)
                phone = response.xpath(
                    "//div[@class='footer__div']//text()[contains(., '+')]"
                ).extract_first()
                if phone:
                    item_loader.add_value("landlord_phone", phone)
                item_loader.add_xpath(
                    "landlord_name", "//div[@class='flex-cell vcard']/h4//text()"
                )

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
