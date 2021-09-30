# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import time

class BrusselsrealestateSpider(scrapy.Spider):
    name = 'brusselsrealestate'
    allowed_domains = ['brusselsrealestate']
    start_urls = ['https://brusselsrealestate.eu/']
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
            'furnished',
            'elevator',
            'images',
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
        url = 'https://brusselsrealestate.eu/fr/a-louer/'
        req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True)
        yield req

    def parse_first(self, response):
        links = response.xpath('//div[@class="msimmo-property-list"]/a')
        for link in links:
            url = link.xpath('./@href').extract_first()
            city = ''.join(link.xpath('.//div[@class="msimmo-property-list-item-info-city"]//text()').extract()).replace(' ', '').replace('\t', '').replace('\n', '')
            property_ts = link.xpath('.//div[@class="msimmo-property-list-item-info-type"]/text()').extract_first().strip().replace(' ', '')
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_ts'] = property_ts
            req.meta['city'] = city
            yield req

    def parse_information(self, response):
        external_id = response.url.split('/')[-2]
        title = ' '.join(response.xpath('//div[@class="msimmo-slide-caption-text"]//text()').extract()).replace('\t', '')
        title = re.sub(r'\r\n', '', title, re.S | re.M | re.I)
        description = ' '.join(response.xpath('//div[@class="msimmo-property-details-description"]/span//text()').extract())
        images = []
        image_links = response.xpath('//div[contains(@class, "msimmo-property-slides")]')
        for image_link in image_links:
            image_url_st = image_link.xpath('./@style').extract_first()
            image_url = re.search(r'background-image:url\((.*?)\)', image_url_st, re.S|re.M|re.I).group(1) 
            images.append(image_url)
        external_images_count = len(images)
        try:
            price_text = re.search(r'Prix:\s(.*?)<br />', response.text, re.S|re.M|re.I).group(1).replace('.', '').replace(',', '').replace(' ', '')
            price = re.findall(r'\d+', price_text, re.S | re.M | re.I)[0]
        except:
            price = ''
        currency = 'EUR'
        try:
            room_count = re.search(r'Nombre de chambre\(s\):\s(.*?)<br />', response.text, re.S|re.M|re.I).group(1)
        except:
            room_count = ''
        try:
            finished = re.search(r'Meublé:\s(.*?)<br />', response.text, re.S|re.M|re.I).group(1)
            if 'Oui' in finished:
                furnished = eval('True') 
            else:
                furnished = eval('False')
        except:
            furnished = eval('False')
        try:
            address = re.search(r'Adresse:\s(.*?)<br />', response.text, re.S|re.M|re.I).group(1)
        except:
            address = ''
        try:
            square_meters_text = re.search(r'Superficie habitable:\s(.*?)<br />', response.text, re.S|re.M|re.I).group(1).replace(',', '.').replace(' ', '')
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        elevator_texts = response.xpath('//div[@class="msimmo-property-details-confort"]//text()').extract()
        for elevator_text in elevator_texts:
            if 'Ascenseur: Oui' in elevator_text:
                elevator = eval('True')
            else:
                elevator = eval('False')
        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
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
        if 'others' not in property_type and address and square_meters and room_count: 
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
                'rent': int(price),
                'currency': currency,
                'furnished': furnished,
                'elevator': elevator,
                'images': images,
                'external_images_count': int(external_images_count),
                'landlord_email': "info@brusselsrealestate.eu",
                'landlord_phone': "+32 (0) 2 534 24 52" ,
                'landlord_name': "Brussels"

            }
            
            yield item



         