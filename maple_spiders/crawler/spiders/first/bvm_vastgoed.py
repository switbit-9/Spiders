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
import dateparser


class MySpider(Spider):
    name = "bvm_vastgoed"
    start_urls = ["https://www.bvm-vastgoed.be/nl/te-huur"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 12)

        seen = False
        for item in response.xpath(
            "//div[@class='property-list-item']/a/@href"
        ).extract():
            yield Request(item, callback=self.populate_item)
            seen = True

        if page == 12 or seen:
            url = f"https://www.bvm-vastgoed.be/nl/?option=com_properties&view=listAjax&count={page}&status=1&goal=1"
            yield Request(url, callback=self.parse, meta={"page": page + 12})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@class='content']//p")

        price = response.xpath(
            "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Prijs:']]/div[@class='value']/text()"
        ).extract_first()
        if price:
            item_loader.add_value("rent", price.split("€ ")[1].strip().replace(",", ""))
            item_loader.add_value("currency", "EUR")

        item_loader.add_xpath("external_id", "//tr[th[.='Reference']]/td")

        square = response.xpath(
            "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Oppervlakte Totaal:']]/div[@class='value']"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        # item_loader.add_xpath("square_meters", "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Oppervlakte Totaal:']]/div[@class='value']")

        property_type = response.xpath(
            "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Type:']]/div[@class='value']/text()"
        ).extract_first()
        if property_type:
            item_loader.add_value("property_type", property_type.split("/")[-1])

        room = response.xpath(
            "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Aantal slaapkamers:']]/div[@class='value']"
        ).get()
        if room:
            item_loader.add_value("room_count", room)

            available_date = response.xpath(
                "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Beschikbaarheid:']]/div[@class='value']/text()"
            ).get()
            if available_date:
                if "Onmiddellijk" not in available_date:
                    date_parsed = dateparser.parse(
                        available_date, date_formats=["%d/%B/%Y"]
                    )
                    date2 = date_parsed.strftime("%Y-%m-%d")
                    item_loader.add_value("available_date", date2)

            terrace = response.xpath(
                "//div[@class='group']//div[@class='field' and ./div[@class='name' and .='Terras:']]/div[@class='value']"
            ).get()
            if terrace:
                item_loader.add_value("terrace", True)

            terrace = response.xpath(
                "//div[@class='content']//div[@class='field' and ./div[.='Garage:']]/div[@class='value']"
            ).get()
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("parking", True)
                else:
                    item_loader.add_value("parking", False)

            terrace = "".join(
                response.xpath(
                    "//div[@class='span4']//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Lift:']]/div[@class='value' and .='Ja']/text()"
                ).extract()
            )
            if terrace:
                if "Ja" in terrace:
                    item_loader.add_value("elevator", True)
                elif "Yes" in terrace:
                    item_loader.add_value("elevator", True)
                elif "No" in terrace:
                    item_loader.add_value("elevator", False)
                else:
                    item_loader.add_value("elevator", False)

            # item_loader.add_xpath("address","//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Adres:']]/div[@class='value']")
            address = " ".join(
                response.xpath(
                    "//div[@class='content']/div[@class='field' and ./div[@class='name' and .='Adres:']]/div[@class='value']/text()"
                ).extract()
            )
            if address:
                item_loader.add_value("address", address)
                item_loader.add_value("zipcode", split_address(address, "zip"))
                item_loader.add_value("city", split_address(address, "city"))
            item_loader.add_value("address", address)

            item_loader.add_xpath(
                "energy_label",
                "normalize-space(//div[@class='content']//div[@class='field' and ./div[.='EPC:']]/div[@class='value'])",
            )

            item_loader.add_xpath(
                "images",
                "//div[@class='swiper-container gallery-top swiper-container-horizontal']/div/div/img/@src",
            )

            item_loader.add_xpath(
                "landlord_name",
                "//div[@class='teammember']//span[@class='teammember-name']",
            )
            phone = response.xpath(
                "//div[@class='teammember']/div[@class='teammember-info']/a/@href[contains(.,'tel:')]"
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

            mail = response.xpath(
                "//div[@class='teammember']/div[@class='teammember-info']/a/@href[contains(.,'mailto:')]"
            ).get()
            if mail:
                item_loader.add_value("landlord_email", mail.replace("mailto:", ""))

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='swiper-wrapper']/div/img/@src"
                ).extract()
            ]
            item_loader.add_value("images", images)

            lat_long = response.xpath(
                "//div[@id='PropertyRegion']//div[@id='detailswitch3']/iframe/@src"
            ).get()
            if lat_long:
                lat_long = lat_long.split("sll=")[1]
                lat = lat_long.split(",")[0]
                longt = lat_long.split(",")[1].split("&")[0]
                item_loader.add_value("latitude", lat)
                item_loader.add_value("longtitude", longt)
            yield item_loader.load_item()


def split_address(address, get):
    temp = address.split(" ")[-2]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
