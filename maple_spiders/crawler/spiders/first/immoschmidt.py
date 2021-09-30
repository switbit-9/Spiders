from __future__ import absolute_import
from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy import Request, FormRequest
from lxml import html as lxhtml
import json
from scrapy.linkextractors import LinkExtractor
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from crawler.loader import MapleLoader
import dateparser


class MySpider(Spider):
    name = "immoschmidt"
    # download_timeout = 60
    custom_settings = {
        "PROXY_ON": True,
        "PASSWORD": "wmkpu9fkfzyo",
    }

    def start_requests(self):
        url = "https://www.immoschmidt.be/Search/Appartement%20For%20rent%20/For%20rent/Type-03%7CAppartement/Localisation-/Prix-/Tri-PRIX%20ASC,COMM%20ASC,CODE/"
        yield Request(url, callback=self.parse_listing)

    def parse_listing(self, response):

        urls = [
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017836843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017795843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017914843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE-SAINT-LAMBERT/Code-00018000843/Lang-EN",
            "/fiche/%20for%20rent%20AUDERGHEM/Code-00017942843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017971843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017987843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017799843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017980843/Lang-EN",
            "/fiche/%20for%20rent%20IXELLES/Code-00017952843/Lang-EN",
            "/fiche/%20for%20rent%20ST%20GILLES/Code-00017930843/Lang-EN",
            "/fiche/%20for%20rent%20UCCLE/Code-00017837843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE%20ST%20LAMBERT/Code-00017392843/Lang-EN",
            "/fiche/%20for%20rent%20BRUXELLES/Code-00017902843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE%20ST%20LAMBERT/Code-00017922843/Lang-EN",
            "/fiche/%20for%20rent%20BRUXELLES/Code-00017867843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017851843/Lang-EN",
            "/fiche/%20for%20rent%20EVERE/Code-00017981843/Lang-EN",
            "/fiche/%20for%20rent%20BRUXELLES/Code-00017999843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017850843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017984843/Lang-EN",
            "/fiche/%20for%20rent%20SCHAERBEEK/Code-00017445843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE-SAINT-PIERRE/Code-00017997843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017895843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017967843/Lang-EN",
            "/fiche/%20for%20rent%20EVERE/Code-00017955843/Lang-EN",
            "/fiche/%20for%20rent%20BRUXELLES/Code-00017931843/Lang-EN",
            "/fiche/%20for%20rent%20SAINT-GILLES/Code-00017907843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017977843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017992843/Lang-EN",
            "/fiche/%20for%20rent%20SCHAERBEEK/Code-00017956843/Lang-EN",
            "/fiche/%20for%20rent%20BRUXELLES/Code-00017993843/Lang-EN",
            "/fiche/%20for%20rent%20BXL/Code-00017929843/Lang-EN",
            "/fiche/%20for%20rent%20BXL/Code-00017943843/Lang-EN",
            "/fiche/%20for%20rent%20AUDERGHEM/Code-00017975843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017985843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE%20ST%20LAMBERT/Code-00017773843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE-SAINT-PIERRE/Code-00017974843/Lang-EN",
            "/fiche/%20for%20rent%20BXL/Code-00017877843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017857843/Lang-EN",
            "/fiche/%20for%20rent%20WOLUWE-SAINT-PIERRE/Code-00017946843/Lang-EN",
            "/fiche/%20for%20rent%20SCHAERBEEK/Code-00017959843/Lang-EN",
            "/fiche/%20for%20rent%20SCHAERBEEK/Code-00017960843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017925843/Lang-EN",
            "/fiche/%20for%20rent%20ETTERBEEK/Code-00017979843/Lang-EN",
            "/fiche/%20for%20rent%20LAEKEN/Code-00017995843/Lang-EN",
        ]

        for item in urls:
            # url = response.urljoin(
            #     item.xpath("./a[contains(@class,'zoom-cont2')]/@href").extract_first()
            # )
            url = response.urljoin(item)
            yield Request(url, callback=self.parse_detail)

        # if response.meta.get("pagination", True):
        #     for i in range(2, 4):
        #         pagination = (
        #             f"https://www.immoschmidt.be/Search/Appartement%20For%20rent%20/For%20rent/Type-03%7CAppartement/Localisation-/Prix-/Tri-PRIX%20ASC,COMM%20ASC,CODE/PageNumber-{i}"
        #         )
        #         # print(pagination)
        #         yield Request(
        #             pagination, callback=self.parse_listing, meta={"pagination": False}
        #         )

    def parse_detail(self, response):

        item_loader = MapleLoader(response=response)

        property_type = "apartment"

        item_loader.add_css("title", "h1")
        item_loader.add_xpath("description", "//div[@class='col-md-6']/p")
        rent = response.xpath(
            "//tr[td[.='Price']]/td/text()[contains(., '€')]"
        ).extract_first()
        if rent:
            item_loader.add_value("rent", rent)
        item_loader.add_value("external_link", response.url)
        item_loader.add_value("currency", "EUR")
        item_loader.add_xpath("external_id", "//div[@class='ref-tag']//span/b")

        square = response.xpath(
            "//tr[td[.='Net living area']]/td[2]/text()"
        ).extract_first()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])
            room = response.xpath("//tr[td[.='Bedrooms']]/td[2]/text()").get()
            if room:
                item_loader.add_value("room_count", room)
                date = response.xpath(
                    "//tr[./td[.='Availability']]/td[2]/text()"
                ).extract_first()
                if date:
                    date_parsed = dateparser.parse(date, date_formats=["%d/%m/%Y"])
                    date2 = date_parsed.strftime("%Y-%m-%d")
                    item_loader.add_value("available_date", date2)

                energy_label = response.xpath(
                    "//div[@style='position: absolute; top: 5px; left: 5px;']/img/@src"
                ).get()
                if energy_label:
                    item_loader.add_value(
                        "energy_label",
                        ((energy_label.split("/")[-1]).split(".")[0])
                        .upper()
                        .replace("P", "+")
                        .replace("M", "-"),
                    )

                # property_type = response.xpath("//h1/text()").get()
                item_loader.add_value("property_type", property_type)

                address = response.xpath(
                    "//div[@id='adresse_fiche']/p/text()"
                ).extract_first()
                if address:
                    item_loader.add_value("address", address)
                    item_loader.add_value("zipcode", split_address(address, "zip"))
                    item_loader.add_value("city", split_address(address, "city"))
                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//div[@class='carousel-inner hvr-grow']/div/a/img/@src"
                        ).extract()
                    ]
                    item_loader.add_value("images", images)

                    terrace = response.xpath("//tr[td[.='Terrace']]/td[2]/text()").get()
                    if terrace:
                        if terrace == "Yes":
                            item_loader.add_value("terrace", True)
                        elif terrace == "No":
                            item_loader.add_value("terrace", False)
                        elif "m²" in terrace:
                            item_loader.add_value("terrace", True)

                    terrace = response.xpath(
                        "//tr[td[.='Furnished']]/td[2]/text()"
                    ).get()
                    if terrace:
                        if terrace == "Yes":
                            item_loader.add_value("furnished", True)
                        elif terrace == "No":
                            item_loader.add_value("furnished", False)
                    item_loader.add_value(
                        "landlord_name", "Schmidt Immobilier Etterbeek"
                    )
                    item_loader.add_value("landlord_phone", "+ 32 2 736 77 44")
                    item_loader.add_value("landlord_email", "info@immoschmidt.be")

                    yield item_loader.load_item()


def split_address(address, get):
    if "-" in address:
        temp = address.split("-")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(" ")[1]

        if get == "zip":
            return zip_code
        else:
            return city
