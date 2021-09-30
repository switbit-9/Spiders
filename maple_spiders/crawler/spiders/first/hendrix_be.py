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


class MySpider(Spider):
    name = "hendrix_be"
    start_urls = ["http://www.hendrix.be/"]  # LEVEL 1

    # 1. FOLLOWING
    def parse(self, response):
        # url="https://www.hendrix.be/fr/bien/a-vendre/appartement/1435-mont-saint-guibert/4156105"
        # yield Request(url, callback=self.populate_item)

        page = response.meta.get("page", 1)

        seen = False
        for item in response.css("a.estate-thumb::attr(href)").extract():
            follow_url = response.urljoin(item)
            if "a-vendre" in follow_url:
                pass
            else:
                yield Request(follow_url, callback=self.populate_item)
                seen = True

        if page == 1 or seen:
            url = f"https://www.hendrix.be/fr-BE/List/PartialListEstate/7?EstatesList=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateListForNavigation=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.Estate%5D&EstateRef=&SelectedType=System.Collections.Generic.List%601%5BSystem.String%5D&Categories=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&MinPrice=&MaxPrice=&MaxPriceSlider=&Rooms=&ListID=7&SearchType=ToRent&SearchTypeIntValue=0&SelectedCities=&Cities=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SelectedRegion=0&SelectedRegions=&Regions=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&SortParameter=Date_Desc&Furnished=False&InvestmentEstate=False&NewProjects=False&GroundMinArea=&GroundMaxArea=&CurrentPage={page}&MaxPage=5&EstateCount=66&SoldEstates=False&RemoveSoldRentedOptionEstates=False&List=Webulous.Immo.DD.CMSEntities.EstateListContentObject&Page=Webulous.Immo.DD.CMSEntities.Page&ContentZones=System.Collections.Generic.List%601%5BWebulous.Immo.DD.CMSEntities.ContentZone%5D&DisplayMap=False&MapMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapMarker%5D&MapZipMarkers=System.Collections.Generic.List%601%5BWebulous.Immo.DD.WEntities.MapZipMarker%5D&EstateTotalCount=1543&isMobileDevice=False&SelectedCountries=&Countries=System.Collections.Generic.List%601%5BSystem.Web.Mvc.SelectListItem%5D&CountrySearch=Undefined"
            yield Request(url, callback=self.parse, meta={"page": page + 1})

    # 2. SCRAPING level 2
    def populate_item(self, response):
        item_loader = MapleLoader(response=response)
        with open("debug", "wb") as f:
            f.write(response.body)

        item_loader.add_xpath(
            "title", "normalize-space(//div[@id='site-main']//h1/text())"
        )
        item_loader.add_xpath(
            "description",
            "normalize-space(//div[@id='detail_description']/div/p[not(self::p[@class='ptm'])]//text())",
        )
        rent = response.xpath("//span[@class='estate-text-emphasis']/text()").get()
        if rent:
            item_loader.add_value("rent", rent.split("€")[0].strip())
            item_loader.add_value("currency", "EUR")

            item_loader.add_xpath("external_id", "//tr[./th[.='Référence']]/td")
            item_loader.add_value("external_link", response.url)
            square = response.xpath("//tr[./th[.='Surface habitable']]/td").get()
            if square:
                item_loader.add_value("square_meters", square.split("m²")[0])
                item_loader.add_xpath("property_type", "//tr[./th[.='Catégorie']]/td")
                room = response.xpath("//tr[./th[.='Nombre de chambres']]/td").get()
                if room:
                    item_loader.add_value("room_count", room)
                    item_loader.add_xpath(
                        "available_date", "//tr[th[.='Disponibilité']]/td"
                    )
                    item_loader.add_xpath(
                        "utilities", "//tr[./th[.='Charges (€) (amount)']]/td"
                    )
                    item_loader.add_xpath("floor", "//tr[./th[.='Floor']]/td/text()")

                    item_loader.add_xpath(
                        "energy_label",
                        "normalize-space(//tr[./th[.='PEB (classe)']]/td/text())",
                    )
                    lat = " ".join(
                        response.xpath(
                            "//div[@id='content-maps']/script[contains(text(),'var latlng = ')]"
                        ).extract()
                    )

                    item_loader.add_value(
                        "latitude", lat.split("LatLng(")[1].split(");")[0].split(",")[0]
                    )
                    item_loader.add_value(
                        "longtitude",
                        lat.split("LatLng(")[1].split(");")[0].split(",")[1],
                    )
                    item_loader.add_xpath(
                        "floor_plan_images",
                        "//div[@class='estate-files']/ul/li/a/@href",
                    )

                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//div[@class='col-md-8']/div/ul/li/a/@href"
                        ).extract()
                    ]
                    item_loader.add_value("images", images)

                    terrace = response.xpath("//tr[./th[.='Terrasse']]/td/text()").get()
                    if terrace:
                        if terrace == "Oui":
                            item_loader.add_value("terrace", True)
                        elif terrace == "Non":
                            item_loader.add_value("terrace", False)

                    terrace = response.xpath(
                        "//tr[./th[.='Furnished']]/td/text() | //tr[./th[.='Meublé']]/td/text() "
                    ).get()
                    if terrace:
                        if terrace == "Oui":
                            item_loader.add_value("furnished", True)
                        elif terrace == "Non":
                            item_loader.add_value("furnished", False)

                    terrace = response.xpath(
                        "//tr[./th[.='Garage']]/td/text() | //tr[./th[.='Parking']]/td/text()"
                    ).get()
                    if terrace:
                        if terrace == "Oui":
                            item_loader.add_value("parking", True)
                        elif terrace == "Non":
                            item_loader.add_value("parking", False)

                    terrace = response.xpath(
                        "//tr[./th[.='Ascenseur']]/td/text()"
                    ).get()
                    if terrace:
                        if terrace == "Oui":
                            item_loader.add_value("elevator", True)
                        elif terrace == "Non":
                            item_loader.add_value("elevator", False)

                    swimming_pool = response.xpath(
                        "//tr[./th[.='Piscine']]/td/text()"
                    ).get()
                    if swimming_pool:
                        if swimming_pool == "Oui":
                            item_loader.add_value("swimming_pool", True)
                        elif swimming_pool == "Non":
                            item_loader.add_value("swimming_pool", False)
                    phone = response.xpath(
                        '//div[@class="col-md-3 col-xs-12 xs-tac tar"]/p[1]/a/@href'
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_phone", phone.replace("tel:", "")
                        )

                    energy = response.xpath(
                        "//div[@class='estate-feature']/img/@alt"
                    ).get()
                    if energy:
                        item_loader.add_value("energy_label", energy.split(":")[1])

                    address = response.xpath(
                        "normalize-space(//div[@class='col-md-12 page-title']/h1/text())"
                    ).get()
                    if address:
                        if "à louer" in address:
                            address = (
                                address.split("à louer - ")[1].split(" ")[0]
                                + " "
                                + address.split("à louer - ")[1].split(" ")[1]
                            )
                        if "à vendre" in address:
                            address = (
                                address.split("à vendre - ")[1].split(" ")[0]
                                + " "
                                + address.split("à vendre - ")[1].split(" ")[1]
                            )
                        item_loader.add_value("address", address)
                        item_loader.add_value("zipcode", split_address(address, "zip"))
                        item_loader.add_value("city", split_address(address, "city"))

                        email = response.xpath(
                            '//div[@class="division estate-contact"]/p/a/@href'
                        ).get()
                        if email:
                            item_loader.add_value(
                                "landlord_email", email.replace("mailto:", "")
                            )
                        item_loader.add_value("landlord_name", "immobilire Hendrix")
                        item_loader.add_xpath(
                            "city", "normalize-space(//p[@class='fz20']/text()[2])"
                        )
                        yield item_loader.load_item()


def split_address(address, get):
    temp = address.split(" ")[0]
    zip_code = "".join(filter(lambda i: i.isdigit(), temp))
    city = address.split(" ")[1]

    if get == "zip":
        return zip_code
    else:
        return city
