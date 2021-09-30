# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class LantmeetersSpider(scrapy.Spider):
    name = 'davidrobin'
    allowed_domains = ['davidrobin']
    start_urls = ['https://www.davidrobin.be/']
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
            'landlord_email',
            'landlord_phone',
            'landlord_name',
            'parking',
            'floor',
            'external_images_count'
        ]
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    
    def start_requests(self):
        url = 'https://www.davidrobin.be/a-louer.php'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        next_links = response.xpath('//div[@class="pagination"]/ul/li')
        for next_link in next_links:
            url = response.urljoin(next_link.xpath('./a/@href').extract_first())
            req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True) 
            yield req

    def parse_first(self, response):
        links = response.xpath('//div[@class="blc-bien"]//div[@class="item"]')
        for link in links:
            url = response.urljoin(link.xpath('.//a/@href').extract_first(''))
            property_ts = link.xpath('.//h3/text()').extract_first().strip()
            city = link.xpath('.//h2[@class="titre"]/text()').extract_first()
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_ts'] = property_ts
            req.meta['city'] = city   
            yield req

    def parse_information(self, response):
        title = html.unescape(response.xpath('//title/text()').extract_first('').strip())
        title = re.sub(r'\r\n', '', title)
        external_id = re.search(r'id=(\d+)', response.url, re.S | re.M | re.I).group(1)
        description = ''.join(response.xpath('//div[contains(@id, "galerie")]/p//text()').extract())
        description = re.sub(r'\n', '', description)
        image_links = response.xpath('//div[@id="slide-galerie"]/div//img')
        images = []
        for image_link in image_links:
            image_url = response.urljoin(image_link.xpath('./@src').extract_first('')) 
            images.append(image_url)
        try:
            address = response.xpath('//div[@class="adresse"]/span/text()').extract_first('')
        except:
            address = "Chaussée de charleroi, 226 - 6220 fleurus"
        external_images_count = len(images)
        try:
            room_count = response.xpath('//span[contains(text(), "chambre(s)")]/following-sibling::span/text()').extract_first()
        except:
            room_count = ''
        try:
            square_meters_text = response.xpath('//span[contains(text(), "Superficie habitable")]/following-sibling::span/text()').extract_first().replace(' ', '').replace(',', '.')
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        
        apartment_types = ['lejligheds', 'appartements', 'apartments', 'pisos', 'flats', 'aticos', 'penthouses', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maisons', 'houses', 'homes', 'villas']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_type = ['property_for_sale']
        student_apartment_type = ['student_apartment']
        if response.meta['property_ts'].lower() in apartment_types:
            property_type = 'apartment'
        elif response.meta['property_ts'].lower() in house_types:
            property_type = 'house'
        elif response.meta['property_ts'].lower() in room_types:
            property_type = 'room'
        elif response.meta['property_ts'].lower() in studio_types:
            property_type = 'studio'
        elif response.meta['property_ts'].lower() in property_for_sale_type:
            property_type = 'property_for_sale'
        elif response.meta['property_ts'].lower() in student_apartment_type:
            property_type = 'student_apartment'
        else:
            property_type = 'others' 
        try:
            parking_xpath = response.xpath('//div[@id="galerie1"]//span[contains(text(), "garage(s)")]/following-sibling::span/text()').extract_first()
            if int(parking_xpath) > 0:
                parking = eval('True')
            else:
                parking = eval('False')
        except:
            parking = eval('True') 
        elevator_xpath = response.xpath('//div[contains(@id, "galerie")]//span[contains(text(), "Ascenseur")]')
        if elevator_xpath:
            elevator = eval('True')
        else:
            elevator = eval('False')
        floor_xpath = response.xpath('//div[contains(@id, "galerie")]//span[contains(text(), "Situé")]/text()')
        if floor_xpath:

            try:
                floor_text = floor_xpath.extract_first()
                floor = str(re.findall(r'\d+', floor_text)[0]) + "th floor"
            except:
                floor = "Oth floor"
        else:
            floor = "Oth floor"

        price_text = html.unescape(response.xpath('//span[@class="offre"]/strong/text()').extract_first('').replace('.', '').replace(',','').replace(' ', ''))
        rent = re.findall(r'\d+', price_text, re.S | re.M | re.I)[0]
        currency = 'EUR'
        if 'others' not in property_type and square_meters and room_count: 
            item = {
                'external_link': response.url,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': address,
                'city': response.meta['city'],
                'property_type': property_type,
                'square_meters': float(square_meters),
                'room_count': int(room_count),
                'rent': int(rent),
                'currency': currency,
                'images': images,
                'landlord_email': "info@davidrobin.be",
                'landlord_phone': "071 / 810 888" ,
                'landlord_name': "david robin",
                'parking': parking,
                'floor': floor,
                'external_images_count': int(external_images_count)
            }
            
            yield item