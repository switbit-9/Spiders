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
from scrapy import Request, FormRequest
from scrapy.selector import Selector

# from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
import json


class MySpider(Spider):
    name = "trevi_be"
    start_urls = ["http://www.trevi.be"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        url = "https://www.trevi.be/fr/residentiel/louer-bien-immobilier"

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        data = {
            "property-type": "",
            "property-address": "",
            # 'property-ref': '',
            "property-prix--min": "",
            "property-prix--max": "",
            "property-chambre": "",
            "search": "1",
            "check": "",
            "target": "3",
        }

        yield FormRequest(
            url,
            body=json.dumps(data),
            headers=headers,
            formdata=data,
            dont_filter=True,
            callback=self.jump_first,
        )

    def jump_first(self, response):
        url = "https://www.trevi.be/fr/residentiel/louer-bien-immobilier/tous-nos-biens"
        yield response.follow(url, self.jump)

    def jump(self, response):

        seen = False
        for card in response.xpath('//a[@class="card bien"]/@href').extract():
            url = response.urljoin(card)
            yield response.follow(url, self.populate_item)
            seen = True

        headers = {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            # 'Cookie': 'PHPSESSID=t5ocns8esq2apg2l1gner2cslf; PHPSESSID=oe4rjpqpt1m249qanqtgm1e8rh',
        }
        page = response.meta.get("page", 1)
        data = {
            "limit1": "12",
            "limit2": str(page * 12),
            "serie": str(page),
            "filtre": "filtre_cp",
            "market": "",
            "lang": "fr",
            "type": "all",
            "goal": "1",
            "goal": "1",
            "search": "1",
        }
        if seen:
            yield FormRequest(
                "https://www.trevi.be/Connections/request/xhr/infinite_projects.php",
                # body=json.dumps(data),
                headers=headers,
                formdata=data,
                dont_filter=True,
                callback=self.jump,
                meta={"page": page + 1},
            )

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("title", "//div[contains(@class,'content-intro')]/h2")
        item_loader.add_xpath("external_id", "//p[contains(.,'Référence :')]/b/text()")
        item_loader.add_xpath(
            "description", "//div[@class='bien__content']//p[2]/text()"
        )
        price = response.xpath(
            "//tr[contains(.,'Loyer / mois')]/td[2]/text()[contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[0])
            item_loader.add_value("currency", "EUR")

        utilities = response.xpath(
            "//tr[contains(.,'Charges / mois')]/td[2]/text()[contains(., '€')]"
        ).extract_first()
        if utilities:
            item_loader.add_value("utilities", utilities.split("€")[0])

        address = "".join(
            response.xpath("//tr[contains(.,'Adress')]/td[2]/text()").extract()
        )
        if address:

            item_loader.add_value("address", address)
            zip_code = response.xpath(
                "//tr[contains(.,'Code postal')]/td[2]/text()"
            ).extract_first()
            if zip_code:
                item_loader.add_value("zipcode", zip_code.split("-")[0])
                item_loader.add_value("city", zip_code.split("-")[1])
        else:
            address2 = response.xpath(
                "//tr[contains(.,'Code postal')]/td[2]/text()"
            ).extract_first()
            if address2:
                item_loader.add_value("address", address2)
                item_loader.add_value("zipcode", address2.split("-")[0])
                item_loader.add_value("city", address2.split("-")[1])
        property_type = response.xpath(
            "//tr[contains(.,'Type de bien')]/td[2]/text()"
        ).extract_first()
        if property_type:
            item_loader.add_value("property_type", property_type.split(" ")[-1].strip())
        item_loader.add_xpath(
            "room_count", "//tr[contains(.,'Nbre de chambres')]/td[2]/text()"
        )

        s_meter = response.xpath(
            "//tr[contains(.,'Superficie habitable')or contains( .,'Superficie' )]/td[2]/text()"
        ).extract_first()
        if s_meter is not None:
            item_loader.add_value("square_meters", s_meter.replace("m²", ""))

        floor = response.xpath("//tr[contains(.,'Etage')]/td[2]/text()").extract_first()
        if floor:
            item_loader.add_value("floor", floor)

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[@class='slider slider-bien--details h-100']//div/a/@href"
            ).extract()
        ]
        item_loader.add_value("images", images)

        terrace = response.xpath(
            "//tr[contains(.,'Parking(s)')or contains( .,'Garage(s)')]/td[2]/text()"
        ).get()
        if terrace:
            if terrace == "1":
                item_loader.add_value("parking", True)
            elif terrace == "0":
                item_loader.add_value("parking", False)

        terrace = response.xpath("//tr[contains(.,'Meublé')]/td[2]/text()").get()
        if terrace:
            if terrace == "Yes" or terrace == "Oui":
                item_loader.add_value("furnished", True)

        phone = response.xpath('//div[contains(@class,"tel")]/span/a/@href').get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
        item_loader.add_value("landlord_email", "info@treviorta.be")
        item_loader.add_value("landlord_name", "TREVI Orta")

        yield item_loader.load_item()
