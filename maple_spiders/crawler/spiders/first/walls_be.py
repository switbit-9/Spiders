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
from scrapy import Request
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from crawler.loader import MapleLoader


class MySpiderA(Spider):
    name = "walls_be"
    start_urls = ["https://www.walls.be/wonen/te-huur"]  # LEVEL 1
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }
    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 0)
        seen = False
        for item in response.css("body > a"):
            follow_url = response.urljoin(item.xpath(".//@href").extract_first())
            zip_city = item.xpath(".//div[@class='item--city']/text()").extract_first()
            yield Request(
                follow_url, callback=self.populate_item, meta={"zip_city": zip_city}
            )
            seen = True

        if page == 0 or seen:
            url = f"https://www.walls.be/ajax/{page}?_=1600463139414"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        zip_city = response.meta.get("zip_city")
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("title", "//div[@class='col-sm-6']/h2")
        address = " , ".join(response.css("div.item--street > h1").extract()).strip()
        item_loader.add_value("address", address)

        item_loader.add_xpath(
            "description",
            "normalize-space(//div[contains(@class,'article-wrapper')]/article/div/div[@class='col-sm-12']/text())",
        )
        price = response.xpath(
            "//div[@class='detail-info']/div[@class='price']/div[@class='item--price'][contains(., '€')]"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[1].split("/")[0])
            item_loader.add_value("currency", "EUR")

        item_loader.add_xpath("external_id", "//tr[td[.='Referentie nr.']]/td[2]")
        square = response.xpath("//tr[td[.='Opp.']]/td[2]").extract_first()
        if square:
            item_loader.add_value(
                "square_meters", square.split("ca.")[1].split("m²")[0]
            )
        property_type = "".join(
            response.xpath("//div[@class='col-sm-6']/h2/text()").extract()
        )
        item_loader.add_value("property_type", property_type.split(" te ")[0])
        item_loader.add_xpath("room_count", "//tr[td[.='Slaapkamers']]/td[2]")
        # item_loader.add_xpath("available_date", "//tr[td[.='Beschikbaarheid']]/td[2]")

        item_loader.add_xpath("latitude", "//div[@id='map-canvas']/@data-lat")
        item_loader.add_xpath("longtitude", "//div[@id='map-canvas']/@data-lng")

        floor = response.xpath(
            "normalize-space(//tr[td[.='Verdieping']]/td[2]/text())"
        ).extract_first()
        if floor:
            item_loader.add_value("floor", floor.replace("L", ""))

        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[@class='foto-accordion col-sm-12 estate-detail detail']/ul//a/@href"
            ).extract()
        ]
        if images:
            item_loader.add_value("images", images)

        terrace = response.xpath("//tr[td[.='Terras'  or .='Terras opp.']]/td[2]").get()
        if terrace:
            item_loader.add_value("terrace", True)

        terrace = response.xpath(
            "//tr[td[.='Parkings (binnen)' or .='Garages']]/td[2]/text()"
        ).get()
        if terrace:
            item_loader.add_value("parking", True)

        terrace = response.xpath(
            "normalize-space(//tr[td[.='Lift']]/td[2]/text())"
        ).get()
        if terrace:
            if terrace == "Ja" or terrace == "Oui":
                item_loader.add_value("elevator", True)
            else:
                item_loader.add_value("elevator", False)

        phone = response.xpath(
            '//div[@class="realtor--info"]/p/a[contains(@href, "tel:")]/@href'
        ).get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
        email = response.xpath(
            '//div[@class="realtor--info"]/p/a[contains(@href, "mailto:")]/@href'
        ).get()
        if phone:
            item_loader.add_value("landlord_email", email.replace("mailto:", ""))

        item_loader.add_xpath(
            "landlord_name", "//div[@class='realtor--info']/p[@class='pink']/text()"
        )

        address = response.xpath(
            "normalize-space(//div[@class='item--street']/h1/text())"
        ).extract_first()
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(zip_city, "zip"))
            city = split_address(zip_city, "city")
            if city is not None:
                item_loader.add_value("city", city)

        yield item_loader.load_item()


def split_address(address, get):
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    if len(address.split(zip_code)) > 1:
        city = address.split(zip_code)[1]
    else:
        city = None
    if get == "zip":
        return zip_code
    else:
        return city
