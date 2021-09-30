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


class MySpider(Spider):
    name = "cabinet069_be"
    start_urls = [
        "http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin=0&regionS=&communeS=&type=Appartement&prixmaxS=&chambreS=&keyword=&viager=&listeLots=",
        "http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin=0&regionS=&communeS=&type=maison/villa&prixmaxS=&chambreS=&keyword=&viager=&listeLots=",
        "http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin=0&regionS=&communeS=&type=Commerces%20et%20bureaux&prixmaxS=&chambreS=&keyword=&viager=&listeLots=",
        "http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin=0&regionS=&communeS=&type=Investisseur&prixmaxS=&chambreS=&keyword=&viager=&listeLots=",
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        if "Appartement" in response.url:
            prop_type = "appartement"
        elif "maison" in response.url:
            prop_type = "house"
        elif "bureaux" in response.url:
            prop_type = "commercial"
        elif "Investisseur" in response.url:
            prop_type = "commercial"

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath(
            "//div[contains(@class,'portfolio-wrapper')]/div[contains(@class,'portfolio-item')]//a[@class='portfolio-link']/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(
                follow_url, callback=self.populate_item, meta={"prop_type": prop_type}
            )
            seen = True

        if page == 1 or seen:
            # url = f"http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin={page}&regionS=&communeS=&type=&prixmaxS=&chambreS=&keyword=&viager=&listeLots="
            if "Appartement" in response.url:
                url = f"http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin={page}&regionS=&communeS=&type=Appartement&prixmaxS=&chambreS=&keyword=&viager=&listeLots="
            elif "maison" in response.url:
                url = f"http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin={page}&regionS=&communeS=&type=maison/villa&prixmaxS=&chambreS=&keyword=&viager=&listeLots="
            elif "bureaux" in response.url:
                url = f"http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin={page}&regionS=&communeS=&type=Commerces%20et%20bureaux&prixmaxS=&chambreS=&keyword=&viager=&listeLots="
            elif "Investisseur" in response.url:
                url = f"http://www.cabinet069.be/Chercher-bien-accueil--L--resultat?pagin={page}&regionS=&communeS=&type=Investisseur&prixmaxS=&chambreS=&keyword=&viager=&listeLots="

            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_css("title", "h1")
        item_loader.add_value("external_link", response.url)
        desc = "".join(
            response.xpath("//div[contains(@class,'col-lg-6')]/p//text()").extract()
        ).strip()
        item_loader.add_value("description", desc)

        rent = response.xpath("//strong/span/text()").get()
        if rent:
            rent = rent.split("€")[0]
            item_loader.add_value("rent", rent.replace(" ", ""))
        item_loader.add_value("currency", "EUR")
        ref = response.xpath("//h2/text()").get()
        item_loader.add_value("external_id", ref.split("REF")[1])
        images = [response.urljoin(x) for x in response.xpath("//img/@src").extract()]
        item_loader.add_value("images", images)
        square_meters = response.xpath(
            "//div[@class='row fontIcon']/div[contains(text(),'habitation')]/text()"
        ).get()

        item_loader.add_value("property_type", response.meta.get("prop_type"))

        if square_meters:
            item_loader.add_value(
                "square_meters", square_meters.split("habitation")[1].split("m")[0]
            )

        room = response.xpath(
            "//div[contains(@class,'row fontIcon')]/div[contains(text(),'chambre(s)')]/text()"
        ).extract_first()
        if room:
            item_loader.add_value("room_count", room)

        # item_loader.add_xpath("available_date", "//div[@class='col-12']/strong[.='Disponibilité :']/following-sibling::text()[1]")

        address = response.xpath(
            "normalize-space(//div[@class='col-12']/p/text())"
        ).extract_first()
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("city", split_address(address, "city"))
        furnished = response.xpath(
            "//div[@class='container-fluid text-center']//div[.='équipée']"
        ).get()
        if furnished:
            item_loader.add_value("furnished", True)

        phone = response.xpath(
            '//div[@class="gallery-img"]//a[contains(@href, "tel:")]/@href'
        ).get()
        if phone:
            item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

        yield item_loader.load_item()


def split_address(address, get):
    city = address.split(" ")[-1]
    return city
