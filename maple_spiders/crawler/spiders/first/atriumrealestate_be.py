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
    name = "atriumrealestate_be"
    start_urls = [
        "http://www.atriumrealestate.be/index.php?ctypmandatmeta=l&action=list&reference=&chambre_min=&prix_max="
    ]  # LEVEL 1
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }
    # 1. FOLLOWING LEVEL 1
    rules = (
        Rule(LinkExtractor(restrict_css="div#filters a")),
        Rule(LinkExtractor(restrict_css="div.picture > a"), callback="populate_item"),
    )

    def parse(self, response):

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath("//div[@class='picture']/a/@href").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            url = f"http://www.atriumrealestate.be/index.php?page={page}&ctypmandatmeta=l&action=list&reference=&chambre_min=&prix_max=#toplist"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "div.headline h2")
        desc = "".join(
            response.xpath("normalize-space(//div[@id='desc']/p/text())").extract()
        )
        item_loader.add_value("description", desc)

        price = response.xpath(
            "//div[@id='textbox']/p/text()[contains(., '€')]"
        ).extract_first()
        if price:
            rent = unicodedata.normalize("NFKD", price)
            item_loader.add_value("rent", price.split("€")[0])
            item_loader.add_value("currency", "EUR")
        ref = response.xpath(
            "//div[@id='textbox']/p/text()[contains(., 'Réf')]"
        ).extract_first()
        ref = ref.split(":")[1]
        item_loader.add_value("external_id", ref)
        square = response.xpath(
            "//ul[@class='check_list']/li/text()[contains(., 'Surface habitable')]"
        ).extract_first()
        if square:
            square = square.split(":")[1]
            item_loader.add_value("square_meters", square.split("m²")[0])
            item_loader.add_xpath("property_type", "//tr[th[.='Category']]/td")
            room = response.xpath(
                "//ul[@class='check_list']/li/text()[contains(., 'Chambres')]"
            ).extract_first()
            if room:
                room = room.split(" ")[0]
                item_loader.add_value("room_count", room)
                item_loader.add_xpath("available_date", "//tr[th[.='Availability']]/td")

                a = response.xpath(
                    "//div[@id='desc']/div[@class='headline']/h3/text()"
                ).get()
                if a:
                    property_type = a.split("-")[1].strip()
                    item_loader.add_value("property_type", property_type)
                    furnished = a.split("-")[0]
                    if "non" in furnished:
                        item_loader.add_value("furnished", False)
                    else:
                        item_loader.add_value("furnished", True)
                    city = a.split(property_type)[1].strip().split(" ")[1]
                    item_loader.add_value("city", city)

                # item_loader.add_xpath("utilities", "//tr[th[.='Charges (€) (amount)']]/td")
                utilities = response.xpath(
                    "substring-after(//h4[contains(.,'Charges')]/following-sibling::ul[1]/li[contains(.,'Total:') and not(contains(.,'charges')) and not(contains(.,'tout'))]/text(), 'Total: ')"
                ).extract_first()
                if utilities:
                    u = utilities.split(" ")[0]
                    if len(u) >= 2:
                        item_loader.add_value("utilities", u)

                item_loader.add_xpath("floor", "//tr[th[.='Floor']]/td/text()")
                addres = response.xpath("//div[@id='page-title']//h2/span/text()").get()
                if addres:
                    item_loader.add_value("address", addres.split("-")[1].strip())
                    terrace = response.xpath(
                        "//ul[@class='check_list']/li/text()[contains(., 'Terrasse')]"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("terrace", True)
                        else:
                            item_loader.add_value("terrace", False)

                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//ul[@class='slides']/li/img/@src"
                        ).extract()
                    ]
                    if images:
                        item_loader.add_value("images", images)

                    # phone = response.xpath('//div[@class="sixteen columns"]//ul//li/text()[contains(., "Tél:")]').get()
                    # if phone:
                    item_loader.add_value("landlord_phone", "025361340")
                    # email = response.xpath('//div[@class="sixteen columns"]//ul//li/text()[contains(., "Email:")]').get()
                    # if email:
                    item_loader.add_value("landlord_email", "info@atriumrealestate.be")

                    item_loader.add_value("landlord_name", "Atrium Real Estate")

                    parking = response.xpath(
                        "//ul[@class='check_list']/li/text()[contains(., 'Parking')]"
                    ).extract_first()
                    if parking:
                        item_loader.add_value("parking", True)

                    dishwasher = response.xpath(
                        "//ul[@class='check_list']/li/text()[contains(., 'Lave vaisselle')]"
                    ).extract_first()
                    if dishwasher:
                        item_loader.add_value("dishwasher", True)

                    elevator = response.xpath(
                        "//ul[@class='check_list']/li/text()[contains(., 'Ascenseur')]"
                    ).extract_first()
                    if elevator:
                        item_loader.add_value("elevator", True)

                    yield item_loader.load_item()
