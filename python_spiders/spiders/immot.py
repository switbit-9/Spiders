# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import html
import re

class ImmotSpider(scrapy.Spider):
    name = 'immot'
    allowed_domains = ['immot']
    start_urls = ['https://www.immot.be/']
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
        urls = ['https://www.immot.be/index.php?p=listerBiens&action=L&sector=C', 'https://www.immot.be/index.php?p=listerBiens&action=L&sector=I']
        for url in urls:
            req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True)
            yield req
    
    def parse_first(self, response):
        event_lists = response.xpath('//div[@class="listing"]')
        for event_list in event_lists:
            link = response.urljoin(event_list.xpath('.//a/@href').extract_first())
            city = event_list.xpath('.//div[@class="list-info center-block"]/h4/text()').extract_first()
            req = Request(url=link, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['city'] = city
            yield req

    def parse_information(self, response):
        external_id = response.url.split('=')[-1]
        title = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        title = re.sub(r'\r\n', '', title)
        try:
            square_meters = float(re.findall(r'([\d|,|\.]+)', title.replace(' ','').replace(',', '.'), re.S | re.M | re.I)[0])
        except:
            square_meters = ''
        print("kkkkkkkkkkkkkkkkkkkkk",square_meters)
        description = response.xpath('//meta[@property="og:description"]/@content').extract_first()
        try:
            rent_text = response.xpath('//div[@class="panel-body"]//b[contains(text(), "Loyer")]/text()').extract_first().replace('Loyer:', '').replace(' ', '').replace('.', '').replace(',','')
        except:
            rent_text = response.xpath('//div[@class="panel-body"]//b[contains(text(), "Offre")]/text()').extract_first().replace('Loyer:', '').replace(' ', '').replace('.', '').replace(',','')  
        rent = re.findall(r'\d+', rent_text, re.S | re.M | re.I)[0]
        currency = 'EUR'
        image_lists = response.xpath('//div[@class="panel-fotorama"]/div[@class="fotorama"]/a')
        images = []
        for image_list in image_lists:
            image_url = image_list.xpath('./@href').extract_first()
            images.append(image_url)
        external_images_count = len(images) 
        address = response.xpath('//div[@id="mapid"]/../preceding-sibling::div/b/text()').extract_first('')
        if 'appartement' in description.lower() or 'apartment' in description.lower() or 'flat' in description.lower() or 'piso' in description.lower() or 'atico' in description.lower() or 'penthouse' in description.lower() or 'duplex' in description.lower():
            property_type = 'apartment' 
        elif 'hus' in description.lower() or 'huis' in description.lower() or 'chalet' in description.lower() or 'bungalow' in description.lower() or 'maison' in description.lower() or 'house' in description.lower() or 'home' in description.lower() or 'villa' in description.lower():
            property_type = 'house'
        elif 'chambre' in description.lower():
            property_type = 'room'
        elif 'studio' in description.lower():
            property_type = 'studio'
        elif 'property_for_sale' in description.lower():
            property_type = 'property_for_sale'
        elif 'student_apartment' in description.lower():
            property_type = 'student_apartment'
        else:
            property_type = 'other'
        zipcode = re.findall(r'\d+', response.meta['city'])[0]
        if address and square_meters and 'other' not in property_type:
            item = {
                'external_link': response.url,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': address,
                'city': response.meta['city'],
                'zipcode': zipcode,
                'property_type': property_type,
                'square_meters': square_meters,
                'room_count': int(1),
                'rent': int(rent),
                'currency': currency,
                'images': images,
                'external_images_count': int(external_images_count),
                'landlord_email': "s.collin@immot.be",
                'landlord_phone': "0475 774 016" ,
                'landlord_name': "Stéphane Collin"
            }
            
            yield item