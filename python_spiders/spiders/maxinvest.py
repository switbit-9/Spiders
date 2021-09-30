# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
import json, csv
import re
import html

class MaxinvestSpider(scrapy.Spider):
    name = 'maxinvest'
    allowed_domains = ['maxinvest']
    start_urls = ['http://www.maxinvest.be/']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
            'external_link',
            'external_id',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'title',
            'address',
            'city',
            'zipcode',
            'elevator',
            'images',
            'external_images_count',
            'description',
            'landlord_email',
            'landlord_phone',
            "landlord_name"
        ]
    }
    
    headers = {
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    def start_requests(self):
        
        url = 'http://www.maxinvest.be/a-louer'
        req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True)
        yield req
    
    def parse_first(self, response):
        links = response.xpath('//div[@id="PropertyListRegion"]//div[contains(@class, "items")]//a')
        for link in links:
            url = response.urljoin(link.xpath('./@href').extract_first()) 
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            yield req
    
    def parse_information(self, response):
        external_link = response.url
        external_id = response.xpath('//div[contains(text(), "Code")]/../div[@class="value"]/text()').extract_first('')
        try:
            address = response.xpath('//div[contains(text(), "Adresse")]/../div[@class="value"]/text()').extract_first()
        except:
            address = "60 Rue de la Station Mouscron 7700"
        try:
            square_meters_text = response.xpath('//div[contains(text(), "Superficie totale")]/../div[@class="value"]/text()').extract_first().replace(' ', '').replace(',', '.')
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        rent = response.xpath('//div[contains(text(), "Prix")]/../div[@class="value"]/text()').extract_first().replace('€', '').replace('.', '').replace(',', '')
        rent = int(rent)
        currency = 'EUR'
        title = response.xpath('//div[@id="PropertyRegion"]//h3[contains(@class, "leftside")]/text()').extract_first().replace('\n\t', '')
        description = ''.join(response.xpath('//div[contains(text(), "Description")]/following-sibling::div/div/text()').extract()).replace('\n', '')
        try:
            room_count = response.xpath('//div[contains(text(), "Nombre de Chambre(s)")]/../div[@class="value"]/text()').extract_first().replace('chr', '')
            room_count = int(room_count)
        except:
            room_count = ''
        images = []
        for link in response.xpath('//div[@class="swiper-wrapper"]//img'):
            image_url = link.xpath('./@src').extract_first()
            images.append(image_url)
        
        external_images_count = len(images)
        elevator_xpath = response.xpath('//div[contains(text(), "Ascenseur")]/../div[@class="value"]/text()').extract_first('')
        if 'Oui' in elevator_xpath:
            elevator = eval('True')
        else:
            elevator = eval('False')
        if 'apartment' in title.lower() or 'flat' in title.lower() or 'piso' in title.lower() or 'atico' in title.lower() or 'penthouse' in title.lower() or 'duplex' in title.lower():
            property_type = 'apartment' 
        elif 'hus' in title.lower() or 'huis' in title.lower() or 'chalet' in title.lower() or 'bungalow' in title.lower() or 'maison' in title.lower() or 'house' in title.lower() or 'home' in title.lower() or 'villa' in title.lower():
            property_type = 'house'
        elif 'chambre' in title.lower():
            property_type = 'room'
        elif 'studio' in title.lower():
            property_type = 'studio'
        elif 'property_for_sale' in title.lower():
            property_type = 'property_for_sale'
        elif 'student_apartment' in title.lower():
            property_type = 'student_apartment'
        else:
            property_type = 'other'
        if 'other' not in property_type and room_count and square_meters:
            item = {
                'external_link': external_link,
                'external_id': external_id,
                'property_type': property_type,
                'square_meters': float(square_meters),
                'room_count': int(room_count),
                'rent': int(rent),
                'currency': currency,
                'title': title,
                'address': address,
                'city': "Mouscron",
                'zipcode': "7700",
                'elevator': elevator,
                'images': images,
                'external_images_count': int(external_images_count),
                'description': description,
                'landlord_email': "maxime@maxinvest.be",
                'landlord_phone': "+32 498 51 56 53" ,
                "landlord_name": "MAX'Invest"
            }
            yield item
        