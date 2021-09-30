#
# This file was created by Maple Software
#
#
# This template is usable for ONE-LEVEL DEEP scrapers with pagination.
#
# HOW THE LOOP WORKS:
#
# 1. SCRAPING LEVEL 1: Scrape fields and populate item.
# 2. PAGINATION LEVEL 1: Go to the next page with the "next button" if any.
# 1. ...
#
#

from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose
from scrapy import Spider
from scrapy import Request
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
from crawler.loader import MapleLoader
from datetime import datetime
import dateparser


class MySpider(Spider):
    name = "noare_be"
    start_urls = ["https://www.noa-re.be/en/for-rent/"]  # FIRST LEVEL

    def parse(self, response):
        url = response.xpath("//div[@class='prop-container']/h3/a")
        for item in url:
            url = item.xpath("./@href").extract_first()
            prop = item.xpath("./text()").extract_first()
            yield response.follow(url, self.populate_item, meta={"prop": prop})
        # for item_box in response.css("a.image-container::attr(href)").extract():  # define a "box" which contains the fields for ONE SINGLE item

        # 2. PAGINATION
        next_page_urls = response.css(
            "div.pagination a::attr(href)"
        ).extract()  # pagination("next button") <a> element here
        for next_page_url in next_page_urls:
            yield response.follow(response.urljoin(next_page_url), self.parse)

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        prop = response.meta["prop"]
        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath(
            "description",
            "normalize-space(//div[@id='desc']/div[@itemprop='description']/p/text())",
        )
        price = response.xpath("//span[@itemprop='price']/text()").extract_first()
        if price:
            item_loader.add_value("rent", price.split("€")[0])
            item_loader.add_value("currency", "EUR")

        utilities = response.xpath(
            "normalize-space(//dl/div[dt[.='Costs']]/dd/span/text()[1])"
        ).extract_first()
        if utilities:
            item_loader.add_value(
                "utilities", utilities.split("€")[1].split("monthly")[0]
            )

        ref = response.xpath(
            "//div[@class='container']//h4/span/text()"
        ).extract_first()
        if ref:
            item_loader.add_value("external_id", ref.split("Ref.:")[1])

        square_meters = response.xpath(
            "//div[@class='col-1-3 second']//dl/div[dt[.='Living area']]/dd"
        ).extract_first()
        if square_meters:
            item_loader.add_value("square_meters", square_meters.split("m²")[0])

        address = "".join(
            response.xpath("//div[@id='address']/address/span[2]").extract()
        )
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

        item_loader.add_value("property_type", prop)
        item_loader.add_xpath("room_count", "//div[@class='toolbar']/span[2]/text()")
        available_date = " ".join(
            response.xpath(
                "//div[@class='col-1-3 third']//dl/div[dt[.='Available']]/dd/span/text()[2]"
            ).extract()
        )
        if available_date:
            if (
                available_date != "Tbd with the owner"
                or available_date != "Immediately"
            ):
                date_parsed = dateparser.parse(
                    available_date, date_formats=["%d %B %Y"]
                )
                date2 = date_parsed.strftime("%Y-%m-%d")
                item_loader.add_value("available_date", date2)

        item_loader.add_xpath(
            "energy_label",
            "normalize-space(//div[@class='epc-value epc-b']/span/text())",
        )

        floor = "".join(
            response.xpath(
                "//div[@class='col-1-3 first']//dl/div[dt[.='Floor']]/dd//text()"
            ).extract()
        )
        item_loader.add_value("floor", floor.strip())
        images = [
            response.urljoin(x)
            for x in response.xpath("//div[@id='property-images']//a/@href").extract()
        ]
        item_loader.add_value("images", images)

        terrace = response.xpath(
            "//div[@class='col-1-3 first']//dl/div[dt[.='Terrace 1']]/dd//text()"
        ).get()
        if terrace:
            item_loader.add_value("terrace", True)

        terrace = response.xpath(
            "//div[@class='col-1-3 first']//dl/div[dt[.='Furnished']]/dd//text()[contains(., 'Yes')]"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("furnished", True)
            elif terrace == "No":
                item_loader.add_value("furnished", False)
        desc = " ".join(
            response.xpath("//div[@itemprop='description']//text()").extract()
        ).strip()
        if desc:
            if "dishwasher" in desc:
                item_loader.add_value("dishwasher", True)

        terrace = response.xpath(
            "normalize-space(//div[@class='col-1-3 first']//dl/div[dt[.='Parking inside' or .='Garage']]/dd)"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("parking", True)
            elif terrace == "No":
                item_loader.add_value("parking", False)

        terrace = response.xpath(
            "normalize-space(//div[@class='col-1-3 first']//dl/div[dt[.='Furnished']]/dd)"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("furnished", True)
            elif terrace == "No":
                item_loader.add_value("furnished", False)

        terrace = response.xpath(
            "normalize-space(//div[@class='col-1-3 first']//dl/div[dt[.='Elevator']]/dd)"
        ).get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("elevator", True)
            elif terrace == "No":
                item_loader.add_value("elevator", False)

        phone = response.xpath('//a[@class="no-style"]').get()
        if phone:
            item_loader.add_value("landlord_phone", phone)

        yield item_loader.load_item()


def split_address(address, get):
    # temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), address))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
