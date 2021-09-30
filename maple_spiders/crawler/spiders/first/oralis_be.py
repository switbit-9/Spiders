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
import re
import unicodedata
import dateparser


class MySpider(Spider):
    name = "oralis_be"
    start_urls = [
        "https://www.oralis.be/fr/List/InfiniteScroll?json=%7B%0A%20%20%22SliderList%22%3A%20false,%0A%20%20%22IsProject%22%3A%20false,%0A%20%20%22PageMaximum%22%3A%200,%0A%20%20%22FirstPage%22%3A%20true,%0A%20%20%22CanGetNextPage%22%3A%20false,%0A%20%20%22CMSListType%22%3A%202,%0A%20%20%22SortParameter%22%3A%205,%0A%20%20%22MaxItemsPerPage%22%3A%2012,%0A%20%20%22PageNumber%22%3A%200,%0A%20%20%22EstateSearchParams%22%3A%20%5B%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22StatusIDList%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20%5B%0A%20%20%20%20%20%20%20%201%0A%20%20%20%20%20%20%5D%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22ShowDetails%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20true%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22ShowRepresentatives%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20true%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22CanHaveChildren%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20false%0A%20%20%20%20%7D%0A%20%20%5D,%0A%20%20%22CustomQuery%22%3A%20null,%0A%20%20%22jsonEstateParams%22%3A%20null,%0A%20%20%22BaseEstateID%22%3A%200%0A%7D"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath("//a[@class='estate-card']/@href").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            url = f"https://www.oralis.be/fr/List/InfiniteScroll?json=%7B%0A%20%20%22SliderList%22%3A%20false,%0A%20%20%22IsProject%22%3A%20false,%0A%20%20%22PageMaximum%22%3A%200,%0A%20%20%22FirstPage%22%3A%20false,%0A%20%20%22CanGetNextPage%22%3A%20false,%0A%20%20%22CMSListType%22%3A%202,%0A%20%20%22SortParameter%22%3A%205,%0A%20%20%22MaxItemsPerPage%22%3A%2012,%0A%20%20%22PageNumber%22%3A%20{page},%0A%20%20%22EstateSearchParams%22%3A%20%5B%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22StatusIDList%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20%5B%0A%20%20%20%20%20%20%20%201%0A%20%20%20%20%20%20%5D%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22ShowDetails%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20true%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22ShowRepresentatives%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20true%0A%20%20%20%20%7D,%0A%20%20%20%20%7B%0A%20%20%20%20%20%20%22FieldName%22%3A%20%22CanHaveChildren%22,%0A%20%20%20%20%20%20%22FieldValue%22%3A%20false%0A%20%20%20%20%7D%0A%20%20%5D,%0A%20%20%22CustomQuery%22%3A%20null,%0A%20%20%22jsonEstateParams%22%3A%20null,%0A%20%20%22BaseEstateID%22%3A%200%0A%7D"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(response.xpath("//h1//text()").extract())
        item_loader.add_value("title", re.sub("\s{2,}", " ", title))
        desc = "".join(response.xpath("//div[@class='container']//p/text()").extract())
        item_loader.add_value("description", desc.rstrip().lstrip())

        price = "".join(
            response.xpath(
                "//h1[@class='line-separator-after h2 estate-detail-intro__text']/text()[normalize-space()][contains(., '€')]"
            ).extract()
        )
        if price:
            p = unicodedata.normalize("NFKD", price)
            item_loader.add_value("rent", p.split("€")[0].replace(" ", ""))
            item_loader.add_value("currency", "EUR")

        item_loader.add_xpath(
            "external_id", "//table[@class='estate-table']//tr[./th[.='Référence']]/td"
        )

        square = response.xpath(
            "//table[@class='estate-table']//tr[./th[.='Surface habitable']]/td"
        ).get()
        if square:
            item_loader.add_value("square_meters", square.split("m²")[0])

        address = "".join(
            response.xpath(
                "//span[@class='estate-detail-intro__block-text'][2]/text()"
            ).extract()
        )
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

        available_date = response.xpath(
            "//table[@class='estate-table']//tr[./th[.='Disponibilité']]/td/text()[. != 'immédiatement']"
        ).get()
        if available_date:
            date_parsed = dateparser.parse(available_date, date_formats=["%d/%m/%Y"])
            date2 = date_parsed.strftime("%Y-%m-%d")
            item_loader.add_value("available_date", date2)

        item_loader.add_xpath(
            "property_type",
            "//table[@class='estate-table']//tr[./th[.='Catégorie']]/td",
        )

        utilities = ", ".join(
            response.xpath(
                "//table[@class='estate-table']//tr[./th[contains(.,'Charges')]][1]/td/text()[contains(., '€')]"
            ).extract()
        )
        if utilities:
            item_loader.add_value("utilities", utilities.replace("Charges:", ""))

        room = response.xpath(
            "//table[@class='estate-table']//tr[./th[.='Nombre de chambres']]/td/text()"
        ).get()
        if room:
            item_loader.add_value("room_count", room)

            terrace = response.xpath(
                "//table[@class='estate-table']//tr[./th[.='Terrasse']]/td/text()"
            ).get()
            if terrace:
                if "Oui" in terrace:
                    item_loader.add_value("terrace", True)
                elif "Yes" in terrace:
                    item_loader.add_value("terrace", True)
                elif "No" in terrace:
                    item_loader.add_value("terrace", False)
                else:
                    item_loader.add_value("terrace", False)

            terrace = response.xpath(
                "//table[@class='estate-table']//tr[./th[.='Parking']]/td/text()"
            ).get()
            if terrace:
                if "Oui" in terrace:
                    item_loader.add_value("parking", True)
                elif "Yes" in terrace:
                    item_loader.add_value("parking", True)
                elif "No" in terrace:
                    item_loader.add_value("parking", False)
                else:
                    item_loader.add_value("parking", False)

            terrace = response.xpath(
                "//table[@class='estate-table']//tr[./th[.='Meublé']]/td/text()"
            ).get()
            if terrace:
                if "Oui" in terrace:
                    item_loader.add_value("furnished", True)
                elif "Yes" in terrace:
                    item_loader.add_value("furnished", True)
                elif "No" in terrace:
                    item_loader.add_value("furnished", False)
                else:
                    item_loader.add_value("furnished", False)

            terrace = response.xpath(
                "//table[@class='estate-table']//tr[./th[.='Ascenseur']]/td/text()"
            ).get()
            if terrace:
                if "Oui" in terrace:
                    item_loader.add_value("elevator", True)
                elif "Yes" in terrace:
                    item_loader.add_value("elevator", True)
                elif "No" in terrace:
                    item_loader.add_value("elevator", False)
                else:
                    item_loader.add_value("elevator", False)
            terrace = response.xpath(
                "//table[@class='estate-table']//tr[./th[.='Piscine']]/td/text()"
            ).get()
            if terrace:

                if "Oui" in terrace:
                    item_loader.add_value("swimming_pool", True)
                elif "Yes" in terrace:
                    item_loader.add_value("swimming_pool", True)
                elif "No" in terrace:
                    item_loader.add_value("swimming_pool", False)
                else:
                    item_loader.add_value("swimming_pool", False)

            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//div[@class='owl-estate-photo']/a/img/@src"
                ).extract()
            ]
            if images:
                item_loader.add_value("images", images)

            item_loader.add_xpath(
                "energy_label",
                "//table[@class='estate-table']//tr[./th[contains(.,'PEB (classe)')]]/td/text()",
            )
            phone = response.xpath(
                '//div[@class="box-affix box-affix---agent"]/a[contains(@href, "tel:")]/@href'
            ).get()
            if phone:
                item_loader.add_value("landlord_phone", phone.replace("tel:", ""))
            item_loader.add_value("landlord_email", "info@oralis.be")
            item_loader.add_value("landlord_name", "Oralis")

            yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
