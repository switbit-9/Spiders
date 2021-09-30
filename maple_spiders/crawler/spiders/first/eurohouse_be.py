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
from datetime import datetime


class MySpider(Spider):
    name = "eurohouse_be"
    start_urls = [
        "http://www.eurohouse.be/en/List/PartialListEstate?EstatesList=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateListForNavigation=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&Categories=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&MinPrice=0&MaxPriceSlider=10000&ListID=21&SearchType=ToRent&SearchTypeIntValue=0&SelectedCities=System.Collections.Generic.List%601%5BSystem.String%5D&Cities=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SelectedRegion=0&SelectedRegions=System.Collections.Generic.List%601%5BSystem.String%5D&Regions=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SortParameter=None&Furnished=False&InvestmentEstate=False&NewProjects=False&CurrentPage=0&MaxPage=12&EstateCount=147&SoldEstates=False&RemoveSoldRentedOptionEstates=False&List=Webulous.Immo.DD.CMSEntities.EstateListContentObject&Page=Webulous.Immo.DD.CMSEntities.Page&ContentZones=System.Collections.Generic.List%601%5BWebulous.Immo.DD.CMSEntities.ContentZone%5D&DisplayMap=False&MapZipMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapZipMarker%5D&EstateTotalCount=0&isMobileDevice=False&SelectedCountries=System.Collections.Generic.List%601%5BSystem.String%5D&Countries=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&CountrySearch=Undefined"
    ]

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
            url = f"http://www.eurohouse.be/en/List/PartialListEstate?EstatesList=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateListForNavigation=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&Categories=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&MinPrice=0&MaxPriceSlider=10000&ListID=21&SearchType=ToRent&SearchTypeIntValue=0&SelectedCities=System.Collections.Generic.List%601%5BSystem.String%5D&Cities=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SelectedRegion=0&SelectedRegions=System.Collections.Generic.List%601%5BSystem.String%5D&Regions=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SortParameter=Date_Desc&Furnished=False&InvestmentEstate=False&NewProjects=False&CurrentPage={page}&MaxPage=12&EstateCount=147&SoldEstates=False&RemoveSoldRentedOptionEstates=False&List=Webulous.Immo.DD.CMSEntities.EstateListContentObject&Page=Webulous.Immo.DD.CMSEntities.Page&ContentZones=System.Collections.Generic.List%601%5BWebulous.Immo.DD.CMSEntities.ContentZone%5D&DisplayMap=False&MapZipMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapZipMarker%5D&EstateTotalCount=0&isMobileDevice=False&SelectedCountries=System.Collections.Generic.List%601%5BSystem.String%5D&Countries=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&CountrySearch=Undefined"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        title = "".join(
            response.xpath(
                "//div[@class='section-intro estate-detail-intro']/h1//text()"
            ).extract()
        )
        item_loader.add_value("title", re.sub("\s{2,}", " ", title))
        item_loader.add_xpath(
            "description", "normalize-space(//div[h2[.='Description']]/p/text())"
        )
        price = response.xpath("//h1//text()[contains(., '€')]").extract_first().strip()
        if price:
            item_loader.add_value("rent", price.split("€")[0].replace(",", ""))
            item_loader.add_value("currency", "EUR")

            images = [
                response.urljoin(x)
                for x in response.xpath("//div[@class='item']//a/@href").extract()
            ]
            item_loader.add_value("images", images)

            item_loader.add_xpath("external_id", "//tr[th[.='Reference']]/td")
            square = response.xpath(
                "//tr[th[.='Habitable surface']]/td"
            ).extract_first()
            if square:
                item_loader.add_value("square_meters", square.split("m²")[0])
                item_loader.add_xpath("property_type", "//tr[th[.='Category']]/td")
                room = response.xpath("//tr[th[.='Number of bedrooms']]/td").get()
                if room:
                    item_loader.add_value("room_count", room)

                    date = response.xpath(
                        "//tr[th[.='Availability']]/td/text()[contains(.,'/')]"
                    ).extract_first()
                    if date:
                        item_loader.add_value(
                            "available_date",
                            datetime.strptime(date, "%d/%m/%Y").strftime("%Y-%m-%d"),
                        )

                    item_loader.add_xpath(
                        "utilities", "//tr[th[.='Charges (€) (amount)']]/td"
                    )
                    item_loader.add_xpath("floor", "//tr[th[.='Floor']]/td/text()")

                    terrace = response.xpath("//tr[th[.='Terrace']]/td/text()").get()
                    if terrace:
                        if "Yes" in terrace:
                            item_loader.add_value("terrace", True)
                        elif "No" in terrace:
                            item_loader.add_value("terrace", False)

                    terrace = response.xpath("//tr[th[.='Furnished']]/td/text()").get()
                    if terrace:
                        if "Yes" in terrace:
                            item_loader.add_value("furnished", True)
                        elif "No" in terrace:
                            item_loader.add_value("furnished", False)

                    terrace = response.xpath("//tr[th[.='Parking']]/td/text()").get()
                    if terrace:
                        if "Yes" in terrace:
                            item_loader.add_value("parking", True)
                        elif "No" in terrace:
                            item_loader.add_value("parking", False)

                    terrace = response.xpath("//tr[th[.='Elevator']]/td/text()").get()
                    if terrace:
                        if "Yes" in terrace:
                            item_loader.add_value("elevator", True)
                        elif "No" in terrace:
                            item_loader.add_value("elevator", False)

                    # phone = response.xpath('//section[@class="section"]//a[contains(@href, "tel:")]/@href').get()
                    # if phone:
                    item_loader.add_value("landlord_phone", "+32 2 672.05.55")
                    item_loader.add_value("landlord_name", "euroHouse")
                    item_loader.add_value("landlord_email", "info@eurohouse.be")

                    address = response.xpath(
                        "//span[@class='estate-detail-intro__block-text'][2]/text()"
                    ).extract_first()
                    if address:
                        item_loader.add_value("address", address)
                        item_loader.add_value("zipcode", split_address(address, "zip"))
                        item_loader.add_value("city", split_address(address, "city"))

                    yield item_loader.load_item()


def split_address(address, get):
    temp = address.split(" ")[-2]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[-1]

    if get == "zip":
        return zip_code
    else:
        return city
