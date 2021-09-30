from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose
from scrapy import Spider
from scrapy.linkextractors import LinkExtractor
from scrapy import Request, FormRequest
from scrapy.selector import Selector
from crawler.loader import MapleLoader
import json


class MySpider(Spider):
    name = "ifaservice"
    download_timeout = 60

    def start_requests(self):
        data = {
            "PropertyGoalId": "4",
            "offset": "0",
        }
        yield FormRequest(
            "https://www.ifacservice.be/loadOnScroll",
            body=json.dumps(data),
            formdata=data,
            dont_filter=True,
            callback=self.parse_listing,
            meta={"offset": 0},
        )

    def parse_listing(self, response):
        data = json.loads(response.body)
        if data:
            for item in data:
                url = item["Url"]
                yield Request(url, callback=self.parse_detail)

            offset = response.meta.get("offset")
            # print(offset)
            offset += 12
            data = {
                "PropertyGoalId": "4",
                "offset": f"{str(offset)}",
            }
            yield FormRequest(
                "https://www.ifacservice.be/loadOnScroll",
                body=json.dumps(data),
                formdata=data,
                dont_filter=True,
                callback=self.parse_listing,
                meta={"offset": offset},
            )

    def parse_detail(self, response):
        item_loader = MapleLoader(response=response)

        item_loader.add_value("external_link", response.url)
        ref = response.xpath("//span[@class='ref']/text()").get()
        ref = ref.split(" ")[1]
        item_loader.add_value("external_id", ref)
        prop_type = response.url.split("https://www.ifacservice.be/")[1].split("/")[2]
        item_loader.add_value("property_type", prop_type)
        item_loader.add_xpath("title", "//div[@class='property']/@title")
        desc = "".join(response.xpath("//div[@class='txt']/p/text()").extract())
        item_loader.add_value("description", desc.rstrip().lstrip())
        price = response.xpath("//span[@class='price']/text()").extract_first()
        if price:
            item_loader.add_value("rent", price.split("€ ")[1].replace("+", ""))
            item_loader.add_value("currency", "EUR")
            address = response.xpath(
                "//div[@class='tab']//div[@class='col']/address/text()"
            ).get()
            item_loader.add_value("address", address.strip())
            item_loader.add_value("zipcode", split_address(address, "zip"))
            item_loader.add_value("city", split_address(address, "city").strip())
            available_date = response.xpath(
                "//div[@id='info']//ul/li[./strong[.='Beschikbaar:']]/text()"
            ).get()

            if available_date != "onmiddellijk":
                item_loader.add_value("available_date", available_date)
            square = response.xpath(
                "//div[@class='grid' and ./div[.='Living:']]/div[2]"
            ).extract_first()
            if square:
                item_loader.add_value(
                    "square_meters", square.split("m²")[0].replace(",", ".")
                )
                floor = response.xpath("//h3[contains(.,'Verdieping')]/text()").get()
                if floor:
                    floor = floor.split(" ")[1]
                    item_loader.add_value("floor", floor)
                room = response.xpath(
                    "//div[@class='col']/h3[.='Algemene informatie']/following-sibling::ul/li[./strong[.='Aantal slaapkamers:']]"
                ).get()
                if room:
                    room = room.split(":")[1]
                    item_loader.add_value("room_count", room)
                    images = [
                        response.urljoin(x)
                        for x in response.xpath(
                            "//div[@class='gallery']//a/img/@src"
                        ).extract()
                    ]
                    if images:
                        item_loader.add_value("images", images)

                    terrace = response.xpath(
                        "//div[@class='col']/ul/li[.//div[.='Terras:']]//strong"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("terrace", True)
                        else:
                            item_loader.add_value("terrace", False)
                    dishwasher = response.xpath(
                        "//div[@id='indeling']//ul/li[.//strong[.='Keuken:']]/div/div[2]/text()[contains(.,'Kookplaat')]"
                    ).get()
                    if dishwasher:
                        item_loader.add_value("dishwasher", True)

                    terrace = response.xpath(
                        "//div[@class='col']/ul/li[.//div[.='Garage:']]//strong"
                    ).get()
                    if terrace:
                        if terrace is not None:
                            item_loader.add_value("parking", True)
                        else:
                            item_loader.add_value("parking", False)

                    elevator = response.xpath(
                        "//div[@id='info']//ul/li[./strong[.='Lift:']]/text()"
                    ).get()
                    if elevator:
                        if elevator == "Ja":
                            item_loader.add_value("elevator", True)
                        else:
                            item_loader.add_value("elevator", False)

                    phone = response.xpath(
                        '//div[@class="col info"]/p/a[contains(@href, "tel:")]/@href'
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_phone", phone.replace("tel:", "")
                        )
                    email = response.xpath(
                        '//div[@class="col info"]/p/a[contains(@href, "mailto:")]/@href'
                    ).get()
                    if phone:
                        item_loader.add_value(
                            "landlord_email", email.replace("mailto:", "")
                        )
                    item_loader.add_value("landlord_name", "IFAC SERVICE BV")

                    script = response.xpath("normalize-space(//script[2]/text())").get()
                    if script:
                        script = script.split("map.setCenter(")[1].split("); }")[0]
                        item_loader.add_value(
                            "latitude", script.split(",")[0].split(" ")[1]
                        )
                        item_loader.add_value(
                            "longtitude",
                            script.split(",")[1].split(" ")[2].split("}")[0],
                        )
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
