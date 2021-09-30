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
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
import json


class MySpider(Spider):
    name = "finomat_be"
    start_urls = ["http://www.finomat.be/loc.html"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 2)

        for item in response.xpath("//img[@class='image']/@src").extract():
            if "Pictures" in item:
                detail_id = item.split("/Pictures/")[1].split("/")[0]
                follow_url = f"http://www.finomat.be/fiche/{detail_id}.html"
                yield Request(follow_url, callback=self.populate_item)

        if page < 12:
            url = f"http://www.finomat.be/loc/{page}.html"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):

        item_loader = MapleLoader(response=response)

        item_loader.add_xpath("title", "//td/span[@class='NormalGrand']/b[2]/text()")
        item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("description", "//span[@class='Normal'][2]")
        rent = response.xpath(
            "//span[@class='NormalGrand']//text()[contains(., '€')]"
        ).get()
        item_loader.add_value("rent", rent.split("€")[0].replace(",", ""))

        item_loader.add_xpath("external_id", "//tr[th[.='Reference']]/td")
        meters = "".join(
            response.xpath(
                "//span[@class='Normal']//text()[contains(., 'Superficie habitable ')]"
            ).extract()
        )
        if meters:
            item_loader.add_value(
                "square_meters",
                meters.replace("Superficie habitable :", "").split("m²")[0],
            )
        property_type = "".join(
            response.xpath(
                "//span[@class='NormalGrand']//text()[not(contains(., '€'))]"
            ).extract()
        )
        if property_type:
            item_loader.add_value(
                "property_type", property_type.strip().split("/")[0].strip()
            )

        room = response.xpath(
            "//span[@class='Normal']//text()[contains(.,'Chambres')]"
        ).get()
        if room:
            room = room.split("Chambres :")[0]
            if room != "":
                item_loader.add_xpath(
                    "room_count", "//tr[th[.='Number of bedrooms']]/td"
                )

        available_date = "".join(
            response.xpath(
                "//span[@class='Normal']//text()[contains(., 'Libre : ')]"
            ).extract()
        )
        if available_date:
            item_loader.add_value(
                "available_date", available_date.replace("Libre :", "")
            )
        utilities = "".join(
            response.xpath(
                "//span[@class='Normal']//text()[(contains(., '-€'))]"
            ).extract()
        )
        if utilities:
            item_loader.add_value(
                "utilities", utilities.replace("Charges:", "").split(",")[0]
            )

        terrace = response.xpath(
            "//span[@class='NormalGrand']//text()[contains(., '/')]"
        ).get()
        if terrace:
            item_loader.add_value("parking", True)
        else:
            item_loader.add_value("parking", False)

        image_url_id = response.url.split("/")[-1].replace(".html", "")
        image_url = f"http://www.finomat.be/include/ajax/agile_carousel_data.php?Id={image_url_id}"
        yield Request(
            image_url,
            callback=self.populate_item_with_image,
            meta={"item": item_loader.load_item()},
        )

    def populate_item_with_image(self, response):
        item_loader = MapleLoader(item=response.meta["item"], response=response)

        data = json.loads(response.body)
        images = []
        for img in data:
            content = img["content"]
            sel = Selector(text=content, type="html")
            images.append(sel.xpath("//img/@src").extract_first())

        if images:
            item_loader.add_value("images", images)

        yield item_loader.load_item()
