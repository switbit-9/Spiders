# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class LantmeetersSpider(scrapy.Spider):
    name = 'lantmeeters'
    allowed_domains = ['lantmeeters']
    start_urls = ['https://www.lantmeeters.be/']
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
            'pets_allowed',
            'elevator',
            'parking',
            'floor',
            'floor_plan_images',
            'floor_plan_images_count',
            'landlord_name',
            'landlord_phone',
            'landlord_email'
        ]
    }
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    
    def start_requests(self):
        url = 'https://www.lantmeeters.be/residentieel/te-huur'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        links = response.xpath('//section[@id="properties__list"]/ul/li')
        for link in links:
            url = link.xpath('./a[contains(@class, "property-properties")][contains(@id, "property")]/@href').extract_first('')
            try:
                property_types = link.xpath('.//div[@class="category"]/text()').extract_first().replace('-','').replace(' ', '')
            except:
                continue
            city = link.xpath('.//div[@class="property-information"]/div[@class="category"]/span/text()').extract_first().lower()
            if 'referenties' in url or not url:
                continue
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_types'] = property_types
            req.meta['city'] = city
            yield req

    def parse_information(self, response):
        title = response.xpath('//title/text()').extract_first('').strip().replace('\n', '').replace('\t', '')
        address = response.xpath('//div[@class="location"]/text()').extract_first()
        descriptions = response.xpath('//section[@id="property-description"]/div/text()').extract()
        desc = []
        for des in descriptions:
            des = des.replace('\n', '')
            if des !='' and des !=' ':
                desc.append(des)
        description = ''.join(desc).replace('\n', '').replace('\r', '')
        external_id = response.url.split('/')[-1]
        external_link = response.url
        image_links = response.xpath('//section[@id="property-photos"]/ul/li')
        images = []
        for image_link in image_links:
            image_url = image_link.xpath('.//img/@src').extract_first('') 
            images.append(image_url)
        address = response.xpath('//div[@class="location"]/text()').extract_first()
        external_images_count = len(images)
        try:
            room_count = response.xpath('//dt[contains(text(), "Slaapkamers")]/following-sibling::dd/text()').extract_first()
        except:
            room_count = ''
        price_text = response.xpath('//div[@class="price"]/text()').extract_first().replace(' ', '').replace(',', '').replace('.', '')
        price = re.findall(r'([\d|,|\.]+)', price_text, re.S | re.M | re.I)[0]
        currency = 'EUR'
        square_meters_text = response.xpath('//dt[contains(text(), "Bewoonbare opp")]/following-sibling::dd/text()').extract_first().replace(',', '.').replace(' ', '')
        try:
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        try:
            pets_allowed_text = response.xpath('//dt[contains(text(), "Huisdieren toegelaten")]/following-sibling::dd/text()').extract_first()
            if pets_allowed_text:
                if 'ja' in pets_allowed_text.lower():
                    pets_allowed = eval('True')
                else:
                    pets_allowed = eval('False')
            else:
                pets_allowed = eval('False')
        except:
            pets_allowed = eval('False')
        try:
            elevator_text = response.xpath('//dt[contains(text(), "Lift")]/following-sibling::dd/text()').extract_first()
            if elevator_text:  
                if 'ja' in elevator_text.lower():
                    elevator = eval('True')
                else:
                    elevator = eval('False')
            else:
                elevator = eval('False')
        except:
            elevator = eval('False')
        try:
            floor = response.xpath('//dt[contains(text(), "Aantal verdiepingen")]/following-sibling::dd/text()').extract_first() + "th floor"
        except:
            floor = "0th floor"
        parking_xpath = response.xpath('//dt[contains(text(), "Parking")]/following-sibling::dd/text()').extract_first('')
        if parking_xpath and int(parking_xpath):
            parking = eval('True')
        else:
            parking = eval('False')
        floor_plan_images = []
        floor_plan_imgs = response.xpath('//a[contains(text(), "Plan")]|//a[contains(text(), "plan")]')
        for floor_plan_img in floor_plan_imgs:
            floor_plan_img_v = floor_plan_img.xpath('./@href').extract_first() 
            floor_plan_images.append(floor_plan_img_v)
        floor_plan_images_count = int(len(floor_plan_images))
        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_type = ['property_for_sale']
        student_apartment_type = ['student_apartment']
        if response.meta['property_types'].lower() in apartment_types:
            property_type = 'apartment'
        elif response.meta['property_types'].lower() in house_types:
            property_type = 'house'
        elif response.meta['property_types'].lower() in room_types:
            property_type = 'room'
        elif response.meta['property_types'].lower() in studio_types:
            property_type = 'studio'
        elif response.meta['property_types'].lower() in property_for_sale_type:
            property_type = 'property_for_sale'
        elif response.meta['property_types'].lower() in student_apartment_type:
            property_type = 'student_apartment'
        else:
            property_type = 'other' 
        landlord_name = response.xpath('//div[@class="name"]/text()').extract_first()
        landlord_phone =response.xpath('//div[@class="name"]/following-sibling::a/text()').extract_first()
        zipcode_text = address.replace(' ', '').split(',')[1]
        zipcode = ''.join(re.findall(r'\d+', zipcode_text, re.S | re.M | re.I))
        if 'other' not in property_type and square_meters and room_count:
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
                'rent': float(price),
                'currency': currency,
                'images': images,
                'external_images_count': int(external_images_count),
                'pets_allowed': pets_allowed,
                'elevator': elevator,
                'parking': parking,
                'floor': floor,
                'zipcode': zipcode,
                'floor_plan_images': floor_plan_images,
                'floor_plan_images_count': floor_plan_images_count,
                'landlord_name': landlord_name,
                'landlord_phone': landlord_phone,
                'landlord_email': 'info@lantmeeters.be'
            }
            
            yield item