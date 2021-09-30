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
import re


class MySpider(Spider):
    name = "lecobel_vaneau_be"
    start_urls = ["https://www.lecobel-vaneau.be/en/list-properties-tenant"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        offset = response.meta.get("offset", 30)

        if offset == 30:
            for item in response.xpath(
                "//div[@class='property property__search-item']"
            ):
                follow_url = response.urljoin(item.xpath(".//a/@href").extract_first())
                prop = (
                    item.xpath("./div//div[contains(@class,'property-name')]/text()")
                    .extract_first()
                    .strip()
                    .split(" - ")[1]
                )
                yield Request(
                    follow_url, callback=self.populate_item, meta={"prop": prop}
                )

            url = f"https://www.lecobel-vaneau.be/en/vaneau-search/search?field_ad_type[eq][]=renting&limit=28&mode=list&offset={offset}&offset_additional=0&search_page_id=580"
            yield Request(url, callback=self.parse, meta={"offset": offset + 28})
        else:

            data = json.loads(response.body)
            content = data["html"]
            sel = Selector(text=content, type="html")

            seen = False
            for item in sel.xpath(
                "//div[contains(@class,'results-items')]//a[contains(@class,'link__property full-link')]/@href"
            ).extract():
                follow_url = response.urljoin(item)
                yield Request(follow_url, callback=self.populate_item)
                seen = True

            if seen:
                url = f"https://www.lecobel-vaneau.be/en/vaneau-search/search?field_ad_type[eq][]=renting&limit=28&mode=list&offset={offset}&offset_additional=0&search_page_id=580"
                yield Request(url, callback=self.parse, meta={"offset": offset + 28})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        prop = response.meta.get("prop")
        item_loader.add_css("title", "h1")
        desc = "".join(response.xpath("//div[@class='description']/text()").extract())
        item_loader.add_value("description", desc.strip())
        item_loader.add_value("currency", "EUR")
        item_loader.add_value("external_link", response.url)
        rent = response.xpath(
            "//div[@class='informations__main']/span[@class='price']/text()[contains(., '€')]"
        ).get()
        if rent:
            item_loader.add_value("rent", rent.split("€")[0].replace(" ", ""))

        if prop is not None:
            item_loader.add_value("property_type", re.sub("\s{2,}", " ", prop))

        item_loader.add_xpath("latitude", "//section[@id='maps']/div/@data-lat")
        item_loader.add_xpath("longtitude", "//section[@id='maps']/div/@data-lng")

        item_loader.add_xpath(
            "external_id",
            "//div[@class='specifications']/div[contains(.,'Reference : ')]/span",
        )
        square = response.xpath(
            "//div[@class='specifications']/div[contains(.,'Surface : ')]/span/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("sq ft")[0])
        item_loader.add_xpath(
            "room_count",
            "//div[@class='specifications']/div[contains(.,'Bedroom(s) : ')]/span/text()",
        )
        floor = "".join(
            response.xpath(
                "normalize-space(//div[@class='specifications']/div[contains(.,'Floor :')]/span/text())"
            ).extract()
        )
        if floor:
            item_loader.add_value("floor", floor.strip())

        terrace = response.xpath(
            "normalize-space(//div[@class='specifications']/div[contains(.,'Terrace : ')]/span/text())"
        ).get()
        if terrace:
            if terrace == "Yes" or terrace == "Oui":
                item_loader.add_value("terrace", True)
            else:
                item_loader.add_value("terrace", False)

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[contains(@class,'background-image')]/picture/source[1]/@srcset"
            ).extract()
        ]
        item_loader.add_value("images", images)

        terrace = response.xpath(
            "normalize-space(//div[@class='specifications']/div[contains(.,'Parking(s) : ')]/span/text())"
        ).get()
        if terrace:
            item_loader.add_value("parking", True)

        terrace = response.xpath(
            "normalize-space(//div[@class='specifications']/div[contains(.,'Elevator :')]/span/text())"
        ).get()
        if terrace:
            if terrace == "Yes" or terrace == "Oui":
                item_loader.add_value("elevator", True)
            else:
                item_loader.add_value("elevator", False)

        phone = response.xpath('//div[@class="phone"]/text()').get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("ph", ""))
        email = response.xpath('//div[@class="agency-mail icon-mail"]/a/@href').get()
        if email:
            item_loader.add_value("landlord_email", email.replace("mailto:", ""))

        item_loader.add_xpath("landlord_name", "//div[@class='name']")

        city = response.xpath(
            "normalize-space(//div[@class='informations__main']/h2/text())"
        ).get()
        if city:
            item_loader.add_value("city", city.split(" ")[0])
            item_loader.add_value("address", city.split(" ")[0])
        yield item_loader.load_item()
