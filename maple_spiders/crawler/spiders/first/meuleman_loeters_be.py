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
import dateparser


class MySpider(Spider):
    name = "meuleman_loeters_be"
    start_urls = ["https://www.meuleman-loeters.be/te-huur"]

    # 1. FOLLOWING
    def parse(self, response):
        # url = "https://www.meuleman-loeters.be/te-huur/oostkamp/woning/detail/5390350?dosearch=True&pageindex=1&pagesize=15&rentedperiod=30&searchpage=ForRent&sortdirection=DESC&sortfield=PUBLICATION_CREATED%20&transactiontype=Rent"
        # yield Request(url, callback=self.populate_item)
        page = response.meta.get("page", 2)

        seen = False
        for item in response.xpath(
            "//div[contains(@class,'switch-view-container')]/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 2 or seen:
            url = f"https://www.meuleman-loeters.be/te-huur?pageindex={page}"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        title = response.xpath("//h1[@class='col-md-6']/text()").extract_first().strip()
        item_loader.add_value("title", title)
        desc = "".join(
            response.xpath("//div[@class='row tab description']/div/p").extract()
        )
        item_loader.add_value("description", desc.strip())
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("currency", "EUR")
        rent = response.xpath("//tr[td[.='Prijs:']]/td[2]/text()").extract_first()
        if rent:
            item_loader.add_value("rent", rent.split("/")[0].split("€")[1])

        item_loader.add_xpath("external_id", "//tr[td[.='Referentie:']]/td[2]")
        square = response.xpath(
            "//tr[td[.='Bewoonbare opp.:' or .='Perceeloppervlakte:']]/td[2]/text()"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
        item_loader.add_xpath("property_type", "//tr[td[.='Type:']]/td[2]")
        item_loader.add_xpath("room_count", "//tr[./td[.='Slaapkamers:']]/td[2]")

        available_date = response.xpath(
            "//tr[td[.='Beschikbaar vanaf:']]/td[2]/text()"
        ).extract_first()
        if available_date:
            if available_date != "Onmiddellijk":
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d %B %Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

        latlong = response.xpath(
            "//script[@type='application/ld+json'][1]/text()"
        ).extract_first()
        if latlong:
            item_loader.add_value(
                "latitude", latlong.split('{"latitude":"')[1].split('","')[0]
            )
            item_loader.add_value(
                "longtitude", latlong.split('"longitude":"')[1].split('","')[0]
            )

        item_loader.add_xpath("utilities", "//tr[th[.='Charges (€) (amount)']]/td")
        item_loader.add_xpath("floor", "//tr[td[.='Op verdieping:']]/td[2]/text()")
        address = " ".join(
            response.xpath("//tr[td[.='Adres:']]/td[2]/text()").extract()
        )
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))
        item_loader.add_xpath(
            "energy_label", "//tr[@class='energyClass energyClassE']/td[2]/text()"
        )
        images = [
            response.urljoin(x)
            for x in response.xpath("//div[@class='owl-carousel']//a/@href").extract()
        ]
        item_loader.add_value("images", images)

        terrace = response.xpath(
            "//tr[td[.='Terras:']]/td[2]/text() | //tr[td[.='Balkon:']]/td[2]/text()"
        ).get()
        if terrace:
            if terrace == "Ja" or terrace == "Oui":
                item_loader.add_value("terrace", True)
            elif terrace == "Non":
                item_loader.add_value("terrace", False)

        terrace = response.xpath("//tr[td[.='Parking:']]/td[2]/text()").get()
        if terrace:
            if terrace == "Ja":
                item_loader.add_value("parking", True)
            elif terrace == "Neen":
                item_loader.add_value("parking", False)
        terrace = response.xpath("//tr[td[.='Lift:']]/td[2]/text()").get()
        if terrace:
            if terrace == "Ja":
                item_loader.add_value("elevator", True)
            elif terrace == "Neen":
                item_loader.add_value("elevator", False)

        phone = response.xpath(
            '//div[@class="row large"]/div/a[contains(@href, "tel:")]/@href'
        ).get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

        email = response.xpath(
            '//div[@class="row large"]/div/a[contains(@href, "mailto:")]/text()'
        ).get()
        if email:
            item_loader.add_value("landlord_email", email)

        item_loader.add_value("landlord_name", "Meuleman Loeters")

        yield item_loader.load_item()


def split_address(address, get):
    temp = address.split(" ")[-2]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
