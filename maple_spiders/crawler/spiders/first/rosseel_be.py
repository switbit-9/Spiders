# coding=utf-8
#
# This file was created by Maple Software
#
#
# This template is usable for websites that have proper sitemaps
#
# sitemap_urls --> url leading to the sitemap xml (or robots.txt that contains sitemap url)
# sitemap_rules --> regex to filter URLs in the sitemap, if passed then proceeds with the given function
#
from scrapy.loader.processors import TakeFirst, MapCompose
from scrapy.spiders import SitemapSpider
from w3lib.html import remove_tags
from crawler.items import CrawlerItem
from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy.selector import Selector
from crawler.loader import MapleLoader
import json


class MySpider(SitemapSpider):
    name = "rosseel_be"
    sitemap_urls = ["https://www.rosseel.be/sitemap.xml"]
    sitemap_rules = [
        ("/huren/", "populate_item"),
    ]

    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        title = response.css("h1").get()
        if title:
            item_loader.add_value("external_link", response.url)
            item_loader.add_value("title", title)
            # https://www.rosseel.be/huren/gent/appartementen/ruime-ongemeubelde-studio-in-herenhuis-vlakbij-citadelpark
            item_loader.add_xpath("description", "//div[@id='descriptionbox']/p")
            price = response.xpath("//li[@class='price']/span/text()").extract_first()
            if price:
                item_loader.add_value("rent", price)
                item_loader.add_value("currency", "EUR")
            ref = response.xpath("//span[@class='makelaartitle']/text()").get()
            if ref:
                ref = ref.split(":")[1]
                item_loader.add_value("external_id", ref)

            square = response.xpath(
                "(//div[@class='col-md-12 col-lg-6 pandinfo'])[1]/ul/li[./span[.='Bebouwde opp.' or .='Bewoonbare opp.']]/span[@class='value']/text()"
            ).get()
            if square:
                item_loader.add_value("square_meters", square.split("m")[0])
            else:
                item_loader.add_value("square_meters", "1")

            room_count = response.xpath(
                "//div[@class='col-md-12 col-lg-6 pandinfo']/ul/li[./span[.='Badkamers' or .='Slaapkamers']]/span[@class='value']/text()"
            ).get()
            if room_count:
                item_loader.add_value("room_count", room_count)

            floor = response.xpath(
                "//div[@class='col-md-12 col-lg-6 pandinfo'][1]/ul/li[./span[.='Verdieping']]/span[@class='value']/text()"
            ).get()
            if floor:
                item_loader.add_value("floor", floor)
            else:
                floor = response.xpath(
                    "//div[@class='col-md-12 col-lg-6 pandinfo'][2]/ul/li[./span[.='Verdieping']]/span[@class='value']"
                ).get()
                item_loader.add_value("floor", floor)

            terrace = response.xpath(
                "(//div[@class='col-md-12 col-lg-6 pandinfo'])[3]/ul/li[./span[.='Terras']]/span[@class='value']/text()"
            ).get()
            if terrace:
                if terrace != "Nee":
                    item_loader.add_value("terrace", True)
                else:
                    item_loader.add_value("terrace", False)

            terrace = response.xpath(
                "(//div[@class='col-md-12 col-lg-6 pandinfo'])[3]/ul/li[./span[.='Parking']]/span[@class='value']/text()"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("parking", True)
                else:
                    item_loader.add_value("parking", False)

            terrace = response.xpath(
                "//div[@class='col-md-12 col-lg-6 pandinfo']/ul/li[./span[.='Lift']]/span[@class='value']/text()"
            ).get()
            if terrace:
                if terrace == "Ja":
                    item_loader.add_value("elevator", True)
                else:
                    item_loader.add_value("elevator", False)

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//section[@class='center slider']/div/img/@src"
                ).getall()
            ]
            if images:
                item_loader.add_value("images", images)

            address = response.xpath(
                "//div[@class='panel-body']//a[@class='overview']/text()"
            ).extract_first()
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

            latlang = response.xpath("//div[@class='pubmap']")
            if latlang:
                latitude = latlang.xpath("./@data-lat").get()
                longitude = latlang.xpath("./@data-long").get()
                if latitude and longitude:
                    item_loader.add_value("latitude", latitude)
                    item_loader.add_value("longtitude", longitude)

            item_loader.add_xpath(
                "landlord_name", "//div[@class='makelaarCard']//span[@class='naam']"
            )
            item_loader.add_xpath(
                "landlord_phone",
                "//div[@class='makelaarCard']//span[@class='nummer']/text()",
            )

            json_data = response.xpath(
                "//script[@type='application/ld+json'][1]/text()"
            ).extract_first()
            data = json.loads(json_data)
            if "additionalType" in data.keys():
                prop_type = data["additionalType"]
                item_loader.add_value("property_type", prop_type)

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
