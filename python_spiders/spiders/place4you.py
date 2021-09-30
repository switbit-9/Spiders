# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class Place4youSpider(scrapy.Spider):
    name = 'place4you'
    allowed_domains = ['place4you']
    start_urls = ['http://www.place4you.be/']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
           'external_link',
            'external_id',
            'title',
            'description',
            'address',
            'city',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'images',
            'external_images_count',
            'furnished',
            'parking',
            'elevator',
            'terrace',
            'dishwasher',
            'washing_machine',
            'floor',
            'landlord_email',
            'landlord_phone',
            'landlord_name'
        ]
    }
    headers = {
        'Connection': 'keep-alive',   
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    
    def start_requests(self):
        url = 'http://www.place4you.be/en-GB/List/21'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        # print()
        links = response.xpath('//div[contains(@class, "estate-thumb-container")]')
        for link in links:
            url = response.urljoin(link.xpath('./a/@href').extract_first(''))
            price_text = html.unescape(link.xpath('.//span[@class="estate-text-emphasis"]').extract_first('').replace('.', '').replace(',', ''))
            price = re.findall(r'\d+', price_text, re.S | re.M | re.I)[0]
            city = link.xpath('./span[@class="estate-thumb-description"]/h3/span/text()').extract_first()
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['city'] = city
            req.meta['price'] = price  
            yield req
        if response.xpath('//a[contains(text(), "next page")]/@href'):
            next_link = response.urljoin(response.xpath('//a[contains(text(), "next page")]/@href').extract_first())
            req = Request(url=next_link, callback=self.parse_lists, headers=self.headers, dont_filter=True)
            yield req

    def parse_information(self, response):
        external_link = response.url
        external_id = response.url.split('/')[-1]
        title = response.xpath('//head/meta[@property="og:title"]/@content').extract_first()
        description = ''.join(response.xpath('//head/meta[@property="og:description"]/@content').extract()).replace('\n', '')
        currency = 'EUR'
        image_links = response.xpath('//img[@class="img-slider-main"]')
        images = []
        for image_link in image_links:
            image_url = image_link.xpath('./@src').extract_first('') 
            images.append(image_url)
        address = 'Drève de Limauges 11bis 1470 Bousval'
        external_images_count = len(images)
        try:
            room_count = response.xpath('//th[contains(text(), "Number of bedrooms")]/following-sibling::td/text()').extract_first()
        except:
            room_count = ''
        square_meters_text = response.xpath('//th[contains(text(), "Habitable surface")]/following-sibling::td/text()').extract_first().replace(' ', '').replace(',', '.')
        try:
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        try:
            furnished = response.xpath('//th[contains(text(), "Furnished")]/following-sibling::td/text()').extract_first()
            if 'yes' in furnished.lower():
                furnished = eval('True')
            else:
                furnished = eval('False')
        except:
            furnished = eval('False')
        try:
            parking = response.xpath('//th[contains(text(), "Parking")]/following-sibling::td/text()').extract_first()
            if 'yes' in parking.lower():
                parking = eval('True')
            else:
                parking = eval('False')
        except:
               parking = eval('False')
        try:
            elevator = response.xpath('//th[contains(text(), "Elevator")]/following-sibling::td/text()').extract_first()
            if 'yes' in elevator.lower():
                elevator = eval('True')
            else:
                elevator = eval('False')
        except:
            elevator = eval('False')
        try:
            terrace = response.xpath('//th[contains(text(), "Terrace")]/following-sibling::td/text()').extract_first()
            if 'yes' in terrace.lower():
                terrace = eval('True')
            else:
                terrace = eval('False')
        except:
            terrace = eval('False')
        try:
            floor = response.xpath('//th[contains(text(), "Floors (number)")]/following-sibling::td/text()').extract_first() + "th floor"
        except:
            floor = "0th floor"
        try:
            dishwasher = response.xpath('//th[contains(text(), "Dishwasher")]/following-sibling::td/text()').extract_first()
            if 'yes' in dishwasher.lower():
                dishwasher = eval('True')
            else:
                dishwasher = eval('False')
        except:
            dishwasher = eval('False')
        try:
            washing_machine = response.xpath('//th[contains(text(), "Washing machine")]/following-sibling::td/text()').extract_first()
            if 'yes' in washing_machine.lower():
                washing_machine = eval('True')
            else:
                washing_machine = eval('False')
        except:
            washing_machine = eval('False')
        property_type_e = response.xpath('//th[contains(text(), "Category")]/following-sibling::td/text()').extract_first()
        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_type = ['property_for_sale']
        student_apartment_type = ['student_apartment']
        if property_type_e.lower() in apartment_types:
            property_type = 'apartment'
        elif property_type_e.lower() in house_types:
            property_type = 'house'
        elif property_type_e.lower() in room_types:
            property_type = 'room'
        elif property_type_e.lower() in studio_types:
            property_type = 'studio'
        elif property_type_e.lower() in property_for_sale_type:
            property_type = 'property_for_sale'
        elif property_type_e.lower() in student_apartment_type:
            property_type = 'student_apartment'
        else:
            property_type = 'other' 
        if 'other' not in property_type and room_count and square_meters: 
            item = {
                'external_link': external_link,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': address,
                'city': response.meta['city'],
                'property_type': property_type,
                'square_meters': float(square_meters),
                'room_count': int(room_count),
                'rent': int(response.meta['price']),
                'currency': currency,
                'images': images,
                'external_images_count': int(external_images_count),
                'furnished': furnished,
                'parking': parking,
                'elevator': elevator,
                'terrace': terrace,
                'dishwasher': dishwasher,
                'washing_machine': washing_machine,
                'floor': floor,
                'landlord_email': "info@place4you.be",
                'landlord_phone': "0495 53 41 10",
                'landlord_name': "Isabelle Sandbergen",
                'city': 'Bousval',
                'zipcode': '1470',
                'latitude': '50.6167',
                'longitude': '4.5'
            }
            yield item