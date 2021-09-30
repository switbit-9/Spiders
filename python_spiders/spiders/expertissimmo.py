# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class ExpertissimmoSpider(scrapy.Spider):
    name = 'expertissimmo'
    allowed_domains = ['expertissimmo']
    start_urls = ['https://www.expertissimmo.be/']
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
            'latitude',
            'longitude',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'images',
            'external_images_count',
            'furnished',
            'parking',
            'terrace',
            'washing_machine',
            'elevator',
            'dishwasher',
            'floor',
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
        url = 'https://www.expertissimmo.eu/en-GB/search/to-rent'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        links = response.xpath('//div[@class="estate-list"]//div[@class="estate-list__item"]')
        for link in links:
            f_url = link.xpath('./a/@href').extract_first('')
            if f_url:
                url = response.urljoin(f_url)
                price_text = html.unescape(link.xpath('.//span[@class="smaller"]/text()').extract_first('').replace('.', '').replace(',', '').replace(' ', ''))
                price = int(re.findall(r'\d+', price_text, re.S | re.M | re.I)[0])
                req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
                req.meta['price'] = price  
                yield req

    def parse_information(self, response):
        external_link = response.url
        title = ''.join(response.xpath('//h1[contains(@class, "title")]//text()').extract()).replace(' ', '')
        title = re.sub(r'\r\n', '', title, re.S | re.M | re.I)
        description = ' '.join(response.xpath('//head/meta[@property="og:description"]/@content').extract())
        external_id = response.url.split('/')[-1]
        address = "Avenue des Cerisiers, 212 - 1200 Brussel"
        currency = 'EUR'
        image_links = response.xpath('//div[@class="estate-detail__photo"]//img[@class="estate-detail__thumb-hidden"]')
        images = []
        for image_link in image_links:
            image_url = image_link.xpath('./@src').extract_first('') 
            images.append(image_url)
        external_images_count = int(len(images))
        try:
            room_count = int(response.xpath('//th[contains(text(), "Number of bedrooms")]/following-sibling::td/text()').extract_first(''))
        except:
            room_count = ''
        square_meters_text = response.xpath('//th[contains(text(), "Habitable surface")]/following-sibling::td/text()').extract_first().replace(' ','').replace(',','.')
        try:
            square_meters = float(re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0])
        except:
            square_meters = ''
        try:
            furnished = response.xpath('//th[contains(text(), "Furnished")]/following-sibling::td/text()').extract_first('')
        except:
            furnished = eval("False")
        if 'yes' in furnished.lower():
            furnished = eval("True")
        else:
            furnished = eval("False")
        try:
            parking = response.xpath('//th[contains(text(), "Parking")]/following-sibling::td/text()').extract_first('')
        except:
            parking = eval("False")
        if 'yes' in parking.lower():
            parking = eval("True")
        else:
            parking = eval("False")       
        try:
            terrace = response.xpath('//th[contains(text(), "Terrace")]/following-sibling::td/text()').extract_first('')
        except:
            terrace = eval("False")
        if 'yes' in terrace.lower():
            terrace = eval("True")
        else:
            terrace = eval("False")
        try:
            dishwasher = response.xpath('//th[contains(text(), "Dishwasher")]/following-sibling::td/text()').extract_first('')
            if 'yes' in dishwasher.lower():
                dishwasher = eval("True")
            else:
                dishwasher = eval("False")
        except:
            dishwasher = eval("False")
        try:
            washing_machine = response.xpath('//th[contains(text(), "Washing machine")]/following-sibling::td/text()').extract_first('')
            if 'yes' in washing_machine.lower():
                washing_machine = eval("True")
            else:
                washing_machine = eval("False")
        except:
            washing_machine = eval("False")
        try:
            elevator = response.xpath('//th[contains(text(), "Elevator")]/following-sibling::td/text()').extract_first('')
            if 'yes' in elevator.lower():
                elevator = eval("True")
            else:
                elevator = eval("False")
        except:
            elevator = eval("False")

        try:
            floor = response.xpath('//th[contains(text(), "Floors (number)")]/following-sibling::td/text()').extract_first('') + "th floor"
            if not floor:
                floor = "0th floor"
        except:
            floor = "0th floor"
        category = response.xpath('//th[contains(text(), "All categories")]/following-sibling::td/text()').extract_first('')

        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_types = ['property_for_sale']
        student_apartment_types = ['student_apartment']
        if category.lower() in apartment_types:
            property_type = 'apartment'
        elif category.lower() in house_types:
            property_type = 'house'
        elif category.lower() in room_types:
            property_type = 'studio'
        elif category.lower() in property_for_sale_types:
            property_type = ['property_for_sale']
        elif category.lower() in property_for_sale_types:
            property_type = ['student_apartment'] 
        else:
            property_type = 'other'
        if room_count and square_meters and 'other' not in property_type and response.meta['price']:
            item = {
                'external_link': external_link,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': address,
                'city': "Brussels",
                'zipcode': "1200",
                'latitude': "50.85045", 
                'longitude': "4.34878",
                'property_type': property_type,
                'square_meters': square_meters,
                'room_count': room_count,
                'rent': response.meta['price'],
                'currency': currency,
                'images': images,
                'external_images_count': external_images_count,
                'furnished': furnished,
                'parking': parking,
                'terrace': terrace,
                'washing_machine': washing_machine,
                'elevator': elevator,
                'dishwasher': dishwasher,
                'floor': floor,
                'landlord_email': "info@expertissimmo.eu",
                'landlord_phone': "02 / 736 67 92",
                'landlord_name': "expertissimmo"
            }
            
            yield item
