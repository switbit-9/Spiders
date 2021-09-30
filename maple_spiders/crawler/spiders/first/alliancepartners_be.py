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
import unicodedata
import dateparser


class MySpider(Spider):
    name = "alliancepartners_be"
    start_urls = ["http://www.alliance-partners.be/"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        # url ="http://www.alliance-partners.be/item/16447555/appartement-1-chambre-pour-109000-euros"
        # yield Request(url, callback=self.populate_item)
        page = response.meta.get("page", 0)

        seen = False
        for item in response.css("li.item-box > a::attr(href)").extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 0 or seen:
            start = page * 9
            url = f"http://www.alliance-partners.be/common/ajax/get-search-results,action=sw-item-list;type;rent:sw-item-list;pricefrom;0:sw-item-list;priceto;100000000:sw-item-list;matchinggroup;-1:sw-item-list;regionid;-1:sw-item-list;bought;no:sw-item-list;priceorder;ASC:sw-item-list;start;{start}:sw-item-list;count;9,rememberpage=no,state="
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):

        item_loader = MapleLoader(response=response)
        item_loader.add_css("title", "[itemprop=name]")
        item_loader.add_xpath("description", "//div[@class='rte']/p")
        item_loader.add_value("external_link", response.url)

        rent = response.xpath("//dd[@itemprop='price']/text()[contains(.,'€')]").get()
        if rent:
            price = unicodedata.normalize("NFKD", rent)
            rent2 = price.split("€")[0].replace(" ", "")
            if "Faire offre à partir de" in rent2:
                rent2 = price.split("Faire offre à partir de")[1]
        utilities = response.xpath(
            "//dl[@class='content data-list clearfix']/dt[.='Charges locatives']/following-sibling::dd[1]/text()[contains(.,'€')]"
        ).extract_first()
        if utilities:
            item_loader.add_value("utilities", utilities)

            item_loader.add_value("rent", rent2)
            item_loader.add_value("currency", "EUR")
        square = response.xpath(
            "//section[@class='widget item-details']/dl/dd[contains(.,'m²')]/text()"
        ).get()
        if square:
            square = square.split("m²")[0]
            item_loader.add_value("square_meters", square)
        property_type = response.xpath(
            "//dl[@class='content data-list clearfix']/dt[.='Type de bien']/following-sibling::dd[1]/text()"
        ).extract_first()
        item_loader.add_value("property_type", property_type.split("/")[-1])
        room = response.xpath(
            "//dl[@class='content data-list clearfix']/dt[.='Chambre(s)']/following-sibling::dd[1]"
        ).get()
        if room:
            item_loader.add_value("room_count", room)
            images = [
                response.urljoin(x)
                for x in response.xpath(
                    "//li[@class='item']/img/@data-img-big"
                ).extract()
            ]
            item_loader.add_value("images", images)
            energy_label = response.xpath(
                "//dl[@class='content data-list clearfix']/dd/img/@src"
            ).extract_first()
            if energy_label:
                item_loader.add_value(
                    "energy_label", energy_label.split("_")[1].split(".")[0].upper()
                )

            available_date = response.xpath(
                "//dl[@class='content data-list clearfix']/dt[.='Date de disponibilité']/following-sibling::dd[1]/text()"
            ).extract_first()
            if available_date:
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d %B %Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

            address = response.xpath(
                "//section[@class='widget item-module item-location']/a/text()"
            ).extract_first()
            if address:
                item_loader.add_value("address", address)
                item_loader.add_value("zipcode", split_address(address, "zip"))
                item_loader.add_value("city", split_address(address, "city"))
            phone = response.xpath('//div[@class="tel"][1]').get()
            if phone:
                item_loader.add_value("landlord_phone", phone)
            email = response.xpath(
                "//span[@class='email-js']/a[contains(@href, 'mailto:')]/@href"
            ).get()
            if email:
                item_loader.add_value("landlord_email", email.replace("mailto:", " "))

            item_loader.add_xpath(
                "landlord_name", "//div[@class='logo is-img-logo']/a/text()"
            )

            yield item_loader.load_item()


def split_address(address, get):
    if "," in address:
        temp = address.split(",")[0]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp.split(" ")[-2]))
        city = temp.split(" ")[-1]

        if get == "zip":
            return zip_code
        else:
            return city
