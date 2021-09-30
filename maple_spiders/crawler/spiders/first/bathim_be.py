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
from datetime import datetime


class MySpider(Spider):
    name = "bathim_be"
    start_urls = [
        "https://www.bathim.be/en/List/PartialListEstate?EstatesList=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateListForNavigation=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&Categories=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&MinPrice=0&MaxPriceSlider=10000&ListID=21&SearchType=ToRent&SearchTypeIntValue=0&SelectedCities=System.Collections.Generic.List%601%5BSystem.String%5D&Cities=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SelectedRegion=0&SelectedRegions=System.Collections.Generic.List%601%5BSystem.String%5D&Regions=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SortParameter=None&Furnished=False&InvestmentEstate=False&NewProjects=False&CurrentPage=0&MaxPage=7&EstateCount=89&SoldEstates=False&RemoveSoldRentedOptionEstates=False&List=Webulous.Immo.DD.CMSEntities.EstateListContentObject&Page=Webulous.Immo.DD.CMSEntities.Page&ContentZones=System.Collections.Generic.List%601%5BWebulous.Immo.DD.CMSEntities.ContentZone%5D&DisplayMap=False&MapZipMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapZipMarker%5D&EstateTotalCount=0&isMobileDevice=False&CountrySearch=Undefined"
    ]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):

        page = response.meta.get("page", 1)

        seen = False
        for item in response.xpath(
            "//div[@class='estate-list__item']/a/@href"
        ).extract():
            follow_url = response.urljoin(item)
            yield Request(follow_url, callback=self.populate_item)
            seen = True

        if page == 1 or seen:
            url = f"https://www.bathim.be/en/List/PartialListEstate?EstatesList=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateListForNavigation=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&Categories=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&MinPrice=0&MaxPriceSlider=10000&ListID=21&SearchType=ToRent&SearchTypeIntValue=0&SelectedCities=System.Collections.Generic.List%601%5BSystem.String%5D&Cities=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SelectedRegion=0&SelectedRegions=System.Collections.Generic.List%601%5BSystem.String%5D&Regions=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SortParameter=None&Furnished=False&InvestmentEstate=False&NewProjects=False&CurrentPage={page}&MaxPage=7&EstateCount=89&SoldEstates=False&RemoveSoldRentedOptionEstates=False&List=Webulous.Immo.DD.CMSEntities.EstateListContentObject&Page=Webulous.Immo.DD.CMSEntities.Page&ContentZones=System.Collections.Generic.List%601%5BWebulous.Immo.DD.CMSEntities.ContentZone%5D&DisplayMap=False&MapZipMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapZipMarker%5D&EstateTotalCount=0&isMobileDevice=False&CountrySearch=Undefined"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        title = "".join(
            response.xpath("//h1/span/text()[normalize-space()]").extract()
        ).strip()
        item_loader.add_value(
            "title", title.replace("\r\n                    ", " ").rstrip("-")
        )
        item_loader.add_value("external_link", response.url)
        item_loader.add_xpath(
            "description", "normalize-space(//div[h2[.='Description']]/p[1]/text())"
        )

        rent = response.xpath("normalize-space(//h1//text()[contains(., '€')])").get()
        if rent:
            rent = rent.split(" ")[0]
            item_loader.add_value("rent", rent.replace(",", ""))
        item_loader.add_value("currency", "EUR")
        item_loader.add_xpath("external_id", "//tr[./th[.='Reference']]/td")

        square = response.xpath("//tr[./th[.='Habitable surface']]/td/text()").get()
        if square:
            square = square.split(" ")[0]
            item_loader.add_value("square_meters", square)
        item_loader.add_xpath("property_type", "//tr[./th[.='Category']]/td")
        item_loader.add_xpath("room_count", "//tr[./th[.='Number of bedrooms']]/td")

        date = response.xpath(
            "//tr[./th[.='Availability']]/td/text()[contains(.,'/')]"
        ).extract_first()
        if date:
            item_loader.add_value(
                "available_date",
                datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d"),
            )

        item_loader.add_xpath("utilities", "//tr[./th[.='Charges (€) (amount)']]/td")
        item_loader.add_xpath("floor", "//tr[./th[.='Floors (number)']]/td/text()")
        images = [
            response.urljoin(x)
            for x in response.xpath(
                "//div[@class='owl-estate-photo']/a/@href"
            ).extract()
        ]
        item_loader.add_value("images", images)

        address = response.xpath("//div[h2[.='Description']]/p[2]").extract_first()
        if address:
            item_loader.add_value("address", address)
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city"))

        terrace = response.xpath("//tr[th[.='Terrace']]/td[.='Yes']").get()
        if terrace:
            item_loader.add_value("terrace", True)
        else:
            item_loader.add_value("terrace", False)

        terrace = response.xpath("//tr[th[.='Furnished']]/td").get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("furnished", True)
            elif terrace == "No":
                item_loader.add_value("furnished", False)

        terrace = response.xpath("//tr[th[.='Parking']]/td").get()
        if terrace:
            if terrace == "Yes":
                item_loader.add_value("parking", True)
            elif terrace == "No":
                item_loader.add_value("parking", False)

        elevator = response.xpath("//tr[th[.='Elevator']]/td/text()").extract_first()
        if elevator:
            if "Yes" in elevator:
                item_loader.add_value("elevator", True)
            elif "No" in elevator:
                item_loader.add_value("elevator", False)

        pool = response.xpath("//tr[@id='detail_322']/td/text()").extract_first()
        if pool:
            if "Yes" in pool:
                item_loader.add_value("swimming_pool", True)
            elif "No" in pool:
                item_loader.add_value("swimming_pool", False)

        energy_label = response.xpath(
            "//span/img[@class='estate-facts__peb']/@src"
        ).extract_first()
        if energy_label:
            item_loader.add_value(
                "energy_label", energy_label.split("-")[1].split(".")[0].upper()
            )

        item_loader.add_value("landlord_name", "BATHIM & CO.")
        # phone = response.xpath('//li[@class="tel"]/a[contains(@href, "tel:")]/@href').get()
        # if phone:
        item_loader.add_value("landlord_phone", "+32 (0)2 733 00 00")
        # mail = response.xpath('//li[@class="mail"]/a[contains(@href, "mailto")]/@href').get()
        # if mail:
        item_loader.add_value("landlord_email", "lth@bathim.be")

        yield item_loader.load_item()


def split_address(address, get):
    if "-" in address:
        temp = address.split(" - ")[1]
        zip_code = "".join(filter(lambda i: i.isdigit(), temp))
        city = temp.split(zip_code)[1]

        if get == "zip":
            return zip_code
        else:
            return city
