# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class GroepnsSpider(scrapy.Spider):
    name = 'groepn'
    allowed_domains = ['groepn']
    start_urls = ['https://www.groepn.be/']
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
            'zipcode',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'images',
            'terrace',
            'floor',
            'external_images_count',
            'landlord_email',
            'landlord_phone',
            'landlord_name'
        ]
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    
    def start_requests(self):
        url = 'https://www.groepn.be/te-huur'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        links = response.xpath('//div[contains(@class, "property")]/a')
        for link in links:
            url = link.xpath('./@href').extract_first('')
            property_id = link.xpath('./@id').extract_first().replace('property-', '')
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_id'] = property_id
            yield req

    def parse_information(self, response):
        title = response.xpath('//meta[@property="og:title"]/@content').extract_first('').strip().replace('\n', '')
        description = ''.join(response.xpath('//div[contains(@class, "property-description")]//text()').extract()).replace('\n', '').strip()
        image_links = response.xpath('//div[@class="thumbnails"]/a')
        images = []
        for image_link in image_links:
            image_url = image_link.xpath('./@href').extract_first('') 
            images.append(image_url)
        external_images_count = len(images)
        price_text = html.unescape(response.xpath('//div[@class="price"]/text()').extract_first().replace(',', '').replace('.', '').replace(' ', ''))
        price = re.findall(r'\d+', price_text, re.S | re.M | re.I)[0]
        currency = 'EUR'
        try:
            address = response.xpath('//h3[contains(text(), "Ligging")]/following-sibling::dl/div/dt[contains(text(), "Adres")]/following-sibling::dd/text()').extract_first()
        except:
            address = "Rijksweg 235, 3650 Dilsen-Stokkem"
        city_zipcode = address.split(',')[1]
        zipcode = re.findall(r'\d+', city_zipcode, re.S | re.M | re.I)[0]
        city = re.findall(r'([\w+\-]+)', city_zipcode)[1]
        try:
            square_meters_text = response.xpath('//span[contains(@class, "icon-area")]/following-sibling::p/text()').extract_first().replace(' ', '').replace(',','.')
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        try:
            room_count = response.xpath('//span[contains(@class, "icon-rooms")]/following-sibling::p/text()').extract_first()
        except:
            room_count = ''
        try:
            floor = response.xpath('//dt[contains(text(), "Verdieping")]/following-sibling::dd/text()').extract_first() + 'th floor'
        except:
            floor = "0th floor"
        try:
            terrace = response.xpath('//dt[contains(text(), "Terras")]/following-sibling::dd/text()').extract_first()
            if 'ja' in terrace.lower():
                terrace = eval('True')
            else:
                terrace = eval('False')
        except:
            terrace = eval('False')
        property_type_e = response.xpath('//div[@class="details"]/h1/text()').extract_first()
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
        if square_meters and 'other' not in property_type and room_count:  
            item = {
                'external_link': response.url,
                'external_id': response.meta['property_id'],
                'title': title,
                'description': description,
                'address': address,
                'zipcode': zipcode,
                'city': city,
                'property_type': property_type,
                'square_meters': float(square_meters),
                'room_count': int(room_count),
                'rent': int(price),
                'currency': currency,
                'images': images,
                'terrace': terrace,
                'floor': floor,
                'external_images_count': int(external_images_count),
                'landlord_email': "info@n78vastgoed.be",
                'landlord_phone': "+32 89 86 18 88" ,
                'landlord_name': "Group N"
            }
            
            yield item