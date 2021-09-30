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
    name = "goimmobilier_be"
    sitemap_urls = ["https://www.goimmobilier.be/sitemap.xml"]
    sitemap_rules = [
        ("/a-louer/", "parse"),
    ]

    def parse(self, response):

        script = response.xpath('//script[contains(.,"window.dataPath")]/text()').get()
        url = (
            "https://www.goimmobilier.be/static/d/"
            + script.split('window.dataPath="')[-1].split('";')[0]
            + ".json"
        )
        yield response.follow(url, self.populate_item, dont_filter=True)

    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        prop = json.loads(response.body)["pageContext"]["data"]["contentRow"][0]
        if "property" not in prop.keys():
            return
        prop = prop["property"]
        # print("aaa= ", prop)
        # sitede react var, https://www.goimmobilier.be/static/d/972/path---fr-a-louer-louvainlaneuve-quartier-bruyeres-bureau-4120-bf-0-fea-hASv5BITJLkop0t3CnwH9P2OPDg.json
        # ustteki linkle bu url doluyor, https://www.goimmobilier.be/fr/a-louer/louvainlaneuve/quartier-bruyeres--bureau/4120/
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("zipcode", prop.get("Zip"))
        item_loader.add_value("title", prop.get("TypeDescription"))
        item_loader.add_value("city", prop.get("City"))
        item_loader.add_value("description", prop.get("DescriptionA"))
        price = str(prop.get("Price"))
        if price:
            item_loader.add_value("rent", price)
            item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_id", str(prop.get("ID")))
        item_loader.add_value("square_meters", str(prop.get("SurfaceLiving")))
        propert_type = prop.get("WebIDName")
        if propert_type:
            item_loader.add_value("property_type", prop.get("WebIDName"))
            item_loader.add_value(
                "available_date", str(prop.get("DateFree")).split(" ")[0]
            )
            item_loader.add_value("room_count", str(prop.get("NumberOfBedRooms")))
            # item_loader.add_value("energy_label", str(prop.get('EnergyPerformance')))
            item_loader.add_value("latitude", str(prop.get("GoogleX")))
            item_loader.add_value("longtitude", str(prop.get("GoogleY")))

            terrace = prop.get("NumberOfGarages")
            if terrace:
                if terrace == 1:
                    item_loader.add_value("parking", True)
                elif terrace == 0:
                    item_loader.add_value("parking", False)

            item_loader.add_value("elevator", prop.get("HasLift"))
            images = [response.urljoin(x) for x in prop.get("SmallPictures")]
            if images:
                item_loader.add_value("images", images)
            item_loader.add_value("landlord_name", prop.get("ManagerName"))
            item_loader.add_value("landlord_email", prop.get("ManagerEmail"))
            item_loader.add_value("landlord_phone", prop.get("ManagerMobilePhone"))
            item_loader.add_value("zipcode", prop.get("Zip"))
            item_loader.add_value("address", (prop.get("Zip") + " " + prop.get("City")))

        yield item_loader.load_item()
