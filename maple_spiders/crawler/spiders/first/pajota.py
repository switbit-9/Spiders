from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request
from scrapy.selector import Selector
from crawler.loader import MapleLoader
import json
import math
import dateparser


class MySpider(Spider):
    name = "pajota"
    download_timeout = 60

    def start_requests(self):
        url = "https://www.pajota.be/nl/te-huur"
        yield Request(url, callback=self.parse_listing)

    def parse_listing(self, response):

        for item in response.xpath(
            "//section[@id='properties__list']/ul[contains(@class,'grid__center')]/li"
        ):
            url = item.xpath(
                "./a[contains(@class,'property-contents')]/@href"
            ).extract_first()

            if "referenties" not in url:
                # print(url)
                yield Request(url, callback=self.parse_detail)

        if response.meta.get("page_count"):
            page_count = response.meta.get("page_count")
        else:
            page_count = 2

        pagination = f"https://www.pajota.be/nl/te-huur/pagina-{page_count}"
        # print(pagination)
        page_count += 1
        if page_count <= 5:
            yield Request(
                pagination, callback=self.parse_listing, meta={"page_count": page_count}
            )

    def parse_detail(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath("title", "//div[@class='property__detail-container']/h1")
        item_loader.add_xpath("property_type", "//div[@class='category']/text()")
        item_loader.add_xpath("description", "//div[@class='property__description']")
        price = "".join(
            response.xpath("//div[@class='price'][contains(., '€')]").extract()
        )
        if price:
            item_loader.add_value(
                "rent", price.split("€")[1].split("p")[0].split(",")[0]
            )
            item_loader.add_value("currency", "EUR")

        item_loader.add_xpath(
            "external_id", "normalize-space(//div[@class='reference']/text())"
        )

        square = response.xpath(
            "//div[@class='details-content']//div[./dt[.='bewoonbare opp.']]/dd"
        ).get()
        if square:
            item_loader.add_value(
                "square_meters", square.split("m²")[0].replace(",", ".")
            )
            room_count = response.xpath(
                "//div[@class='details-content']//div[./dt[.='slaapkamers']]/dd"
            ).get()
            if room_count:
                item_loader.add_value("room_count", room_count)

                address = "".join(
                    response.xpath("//div[@class='address']/text()").extract()
                )
                if address:
                    item_loader.add_value("address", address)
                    item_loader.add_value("zipcode", split_address(address, "zip"))
                    item_loader.add_value(
                        "city", split_address(address, "city").strip()
                    )
                available_date = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='beschikbaarheid']]/dd/text()"
                ).get()
                if available_date:
                    if available_date != "Onmiddellijk":
                        date_parsed = dateparser.parse(
                            available_date, date_formats=["%d %B %Y"]
                        )
                        date2 = date_parsed.strftime("%Y-%m-%d")
                        item_loader.add_value("available_date", date2)

                item_loader.add_xpath(
                    "floor",
                    "//div[@class='details-content']//div[./dt[.='verdieping']]/dd/text()",
                )

                terrace = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='terras']]/dd[.='ja' or 'Ja']"
                ).get()
                if terrace:
                    item_loader.add_value("terrace", True)

                terrace = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='gemeubeld']]/dd[. !='nee']"
                ).get()
                if terrace:
                    if terrace == "Ja":
                        item_loader.add_value("furnished", True)
                    else:
                        item_loader.add_value("furnished", False)
                terrace = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='garages / parking']]/dd//text()"
                ).get()
                if terrace:
                    if terrace == "No":
                        item_loader.add_value("parking", False)
                    else:
                        if response.xpath("//li[@class='garages']/i").get():
                            item_loader.add_value("parking", True)

                terrace = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='lift']]/dd/text()"
                ).get()
                if terrace:
                    if terrace == "ja":
                        item_loader.add_value("elevator", True)
                    elif terrace == "nee":
                        item_loader.add_value("elevator", False)
                terrace = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='zwembad']]/dd[. ='ja']"
                ).get()
                if terrace:
                    if terrace == "Ja":
                        item_loader.add_value("swimming_pool", True)
                    else:
                        item_loader.add_value("swimming_pool", False)

                energy = response.xpath(
                    "//div[@class='details-content']//div[./dt[.='epc']]/dd/span/@class"
                ).get()
                if energy:
                    item_loader.add_value(
                        "energy_label", energy.split(" ")[1].split("_")[1].upper()
                    )
                images = [
                    response.urljoin(x)
                    for x in response.xpath(
                        "//section[@id='property__photos']//picture/source/@srcset"
                    ).extract()
                ]
                if images:
                    item_loader.add_value("images", images)
                phone = response.xpath(
                    "normalize-space(//div[@class='field-name-property-contact-phone field-type-text']//a)"
                ).get()
                if phone:
                    item_loader.add_value("landlord_phone", phone.replace("tel:", ""))

                name = response.xpath("//div[@class='name']//text()").get()
                if name:
                    item_loader.add_value("landlord_name", name)
                item_loader.add_value("landlord_email", "info@pajota.be")
                item_loader.add_value("landlord_phone", "02 466 05 75")
                yield item_loader.load_item()


def split_address(address, get):
    if "," in address:
        temp = address.split(",")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(zip_code)[1]

        if get == "zip":
            return zip_code
        else:
            return city
