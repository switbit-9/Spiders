import scrapy
import js2xml
from ..helper import remove_white_spaces, format_date, remove_unicode_char, currency_parser,\
    extract_number_only, property_type_lookup
from ..items import ListingItem


def extract_city_zipcode(_address):
    zip_city = _address.split(", ")[1]
    zipcode, city = zip_city.split(" ")
    return zipcode, city


class GetDetailsUpgradeimmoSpider(scrapy.Spider):
    name = 'upgradeimmo'
    allowed_domains = ['upgradeimmo.be']
    start_urls = []
    position = 0

    def start_requests(self):
        start_urls = [
            {'url': 'https://www.upgradeimmo.be/fr/a-louer/appartements',
                'property_type': 'apartment'}
        ]
        for url in start_urls:
            yield scrapy.Request(url=url.get('url'),
                                 callback=self.parse,
                                 meta={'property_type': url.get('property_type')})

    def parse(self, response, **kwargs):
        listings = response.xpath(
            ".//div[@class='property-list']/div[@class='property']")
        for property_item in listings:
            property_url = response.urljoin(property_item.xpath(
                ".//div[@class='meet_info button-link']/a/@href").extract_first())
            yield scrapy.Request(
                url=property_url,
                callback=self.get_property_details,
                meta={'property_type': response.meta.get('property_type')}
            )

        next_page_url = response.xpath(
            ".//div[@class='paging']//a[contains(@class, 'next')]/@href").extract_first()
        if next_page_url:
            yield scrapy.Request(
                url=response.urljoin(next_page_url),
                callback=self.parse,
                meta={'property_type': response.meta.get('property_type')}
                )

    def get_property_details(self, response):
        self.position += 1
        external_link = response.url
        address = ''.join(response.xpath(
            ".//div[@class='top-title']//div[@class='fleft']//text()").extract())
        rent = ''.join(response.xpath(
            ".//div[@class='top-title']//div[@class='fright']//text()").extract())
        description = ''.join(response.xpath(
            ".//div[contains(text(), 'Description')]/following-sibling::div[1]//text()").extract())
        property_type = response.meta.get('property_type')
        square_meters = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Superficie totale')]/following-sibling::div[2]//text()").extract())
        available_date = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Date de disponibilité')]/following-sibling::div[2]//text()").extract())
        floor = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Etage') and not(contains(.//dt//text(), 'Nombre d’etage'))]/following-sibling::div[2]//text()").extract())
        room_count = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Nombre de Chambre(s)')]/following-sibling::div[2]//text()").extract())

        furnished = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Meublé')]/following-sibling::div[2]//text()").extract())
        terrace = ''.join(response.xpath(
            ".//div[contains(.//text(), 'Terrasse')]/following-sibling::div[2]//text()").extract())
        images = response.xpath(".//div[@id='Photos']//li/a/@href").extract()
        external_images_count = len(images)
        js_code = response.xpath(
            "//script[contains(., 'mymap.setView')]/text()").extract_first()
        parsed_js = js2xml.parse(js_code)
        latitude = parsed_js.xpath("//var[@name='marker']//number[1]//@value")
        longitude = parsed_js.xpath("//var[@name='marker']//number[2]//@value")
        landlord_name = 'Upgrade IMMO'
        landlord_email = 'info@upgradeimmo.be'
        landlord_phone = '02 / 673.95.64'
        zipcode, city = extract_city_zipcode(address)

        item = ListingItem()
        item['external_link'] = external_link
        item['address'] = address
        if rent:
            item['rent'] = remove_unicode_char(rent.replace('.', ''))
            item['currency'] = currency_parser(rent)
        item['description'] = remove_white_spaces(description)
        if property_type:
            item['property_type'] = property_type_lookup.get(property_type, None)
        if square_meters:
            item['square_meters'] = extract_number_only(
                remove_unicode_char(square_meters))
        if available_date:
            item['available_date'] = format_date(available_date, '%d/%m/%Y')
        if floor:
            item['floor'] = floor
        item['images'] = images
        item['external_images_count'] = external_images_count
        if furnished:
            item['furnished'] = True
        if terrace:
            item['terrace'] = True
        if latitude:
            item['latitude'] = latitude[0]
        if longitude:
            item['longitude'] = longitude[0]
        if room_count:
            item['room_count'] = extract_number_only(room_count)
        item['landlord_name'] = landlord_name
        item['landlord_email'] = landlord_email
        item['landlord_phone'] = landlord_phone
        item['zipcode'] = zipcode
        item['city'] = city
        item['position'] = self.position
        yield item
