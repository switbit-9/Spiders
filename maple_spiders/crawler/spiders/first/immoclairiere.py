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


class MySpider(Spider):
    name = "immoclairiere"
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }
    start_urls = [
        "http://bruxelles.immoclairiere.be/index.php?ctypmandatmeta=l&action=list&cbien=&qchambres=&mprixmin=&mprixmax=",
        "http://braine.immoclairiere.be/index.php?ctypmandatmeta=l&action=list&cbien=&qchambres=&mprixmin=&mprixmax=",
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath("//div[@class='post']//h2//@href").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            if "bruxelles.immoclairiere" in response.url:
                url = f"http://bruxelles.immoclairiere.be/index.php?page={page}&ctypmandatmeta=l&action=list&cbien=&qchambres=&mprixmin=&mprixmax=#toplist"
            else:
                url = f"http://braine.immoclairiere.be/index.php?page={page}&ctypmandatmeta=l&action=list&cbien=&qchambres=&mprixmin=&mprixmax=#toplist"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath(
            "title", "normalize-space(//div[@id='page-title']/h2/text())"
        )
        item_loader.add_xpath("description", "//div[@id='desc']/p")
        price = response.xpath(
            "//div[@id='textbox']/p[1][contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€ ")[0])
            item_loader.add_value("currency", "EUR")

            deposit = response.xpath(
                "//ul[@class='check_list']/li[contains(.,'Précompte:')]"
            ).get()
            if deposit:
                deposit = deposit.split(":")[1]
                item_loader.add_value("deposit", deposit)
            ref = response.xpath("//div[@id='textbox']/p[2]").get()
            # ref = ref.split(":")[1]
            item_loader.add_value("external_id", ref.split("Réf.:")[1])
            square = response.xpath(
                "//ul[@class='check_list']/li[contains(.,'Surface habitable:')]"
            ).get()
            if square:
                square = square.split(":")[1]
                item_loader.add_value("square_meters", square.split("m²")[0])

                utility = response.xpath(
                    "//ul[@class='check_list']/li[contains(.,'Charges:')]"
                ).get()
                if utility:
                    utility = utility.split(":")[1]
                    item_loader.add_value("utilities", utility.split("€ ")[0])
                item_loader.add_xpath(
                    "floor",
                    "//div[@class='group']//div[@class='field' and ./div[@class='name' and .='Etage']]/div[@class='value']/text()",
                )
                room = response.xpath(
                    "//div[@id='desc']//ul[@class='check_list']/li[contains(.,'Chambre')]/text()"
                ).get()
                if room:
                    room = room.split(" ")[0]
                    item_loader.add_value("room_count", room)
                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//ul[@class='slides']/li/img/@src"
                        ).extract()
                    ]
                    if images:
                        item_loader.add_value("images", images)
                    property_type = response.xpath(
                        "//div[@id='desc']/div[@class='headline']/h3/text()"
                    ).get()
                    item_loader.add_value(
                        "property_type", property_type.split("-")[1].strip()
                    )
                    item_loader.add_value("address", property_type.split("-")[2])
                    terrace = response.xpath(
                        "//div[@class='tabs-container']/div[@id='details']//h4[.='Equipements de Cuisine']"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("furnished", True)
                        else:
                            item_loader.add_value("furnished", False)

                    terrace = response.xpath(
                        "//div[@class='tabs-container']/div[@id='details']//ul/li[contains(.,'Parking')]"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("parking", True)
                        else:
                            item_loader.add_value("parking", False)

                    terrace = response.xpath(
                        "//div[@id='details']//ul/li[contains(.,' Ascenseur')]"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("elevator", True)
                        else:
                            item_loader.add_value("elevator", False)
                    phone = response.xpath(
                        '//div[@class="five columns"]/ul/li[contains(., "Tél:")]'
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_phone", phone.replace("Tél:", "")
                        )
                    yield item_loader.load_item()
