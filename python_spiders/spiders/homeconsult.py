# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class HomeconsultSpider(scrapy.Spider):
    name = 'homeconsult'
    allowed_domains = ['home-consult']
    start_urls = ['https://www.home-consult.be/']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
            'external_link',
            'external_id',
            'latitude',
            'longitude',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'title',
            'address',
            'city',
            'images',
            'external_images_count',
            'description',
            'furnished',
            'elevator',
            'parking',
            'terrace',
            'available_date',
            'landlord_name',
            'landlord_phone',
            'landlord_email'
        ]
    }
    headers = {
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'XMLHttpRequest',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    }
    gheaders = {
        'Connection': 'keep-alive',   
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    def start_requests(self):
        url = 'https://www.home-consult.be/en/ajax_all_properties/'
        data = {
          'purpose': '2',
          'min_rooms': '',
          'min_price': '0',
          'max_price': '0'
        }

        req = Request(url=url, callback=self.parse_information, method='POST', body=json.dumps(data), headers=self.headers, dont_filter=True)
        yield req

    def parse_information(self, response):
        datas = json.loads(response.text)
        for key, data in datas.items():
            external_link = data['url']
            external_id = key 
            latitude = data['lat']
            longitude = data['lon']
            apartment_types = ['lejligheds', 'appartements', 'apartments', 'pisos', 'flats', 'aticos', 'penthouses', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
            house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maisons', 'houses', 'homes', 'villas']
            room_types = ['chambre']
            studio_types = ['studio']
            property_for_sale_type = ['property_for_sale']
            student_apartment_type = ['student_apartment']
            studio_types = ['studio']
            if data['category'].lower() in apartment_types:
                property_type = 'apartment'
            elif data['category'].lower() in house_types:
                property_type = 'house'
            elif data['category'].lower() in room_types:
                property_type = 'room'
            elif data['category'].lower() in studio_types:
                property_type = 'studio'
            elif data['category'].lower() in property_for_sale_type:
                property_type = 'property_for_sale'
            elif data['category'].lower() in student_apartment_type:
                property_type = 'student_apartment'
            else:
                property_type = 'others' 
            try:
                square_meters = float(re.findall(r'([\d|,|\.]+)', data['area'].replace(' ', '').replace(',','.'), re.S | re.M | re.I)[0])
            except:
                try:
                    square_meters = int(data['area'].replace(' ', '').replace(',','.'))
                except:
                    square_meters = ''
            room_count = int(data['rooms'])
            rent = int(re.findall(r'\d+', data['price'].replace('.', '').replace(',',''), re.S | re.M | re.I)[0])
            currency = 'EUR' 
            req = Request(url=external_link, callback=self.parse_detail, headers=self.gheaders, dont_filter=True)
            req.meta['external_link'] = external_link
            req.meta['external_id'] = external_id
            req.meta['latitude'] = latitude
            req.meta['longitude'] = longitude
            req.meta['property_types'] = property_type
            req.meta['square_meters'] = square_meters
            req.meta['room_count'] = room_count
            req.meta['rent'] = rent
            req.meta['currency'] = currency 
            yield req
    def parse_detail(self, response): 
        title = response.xpath('//div[@id="detail"]//h1/text()').extract_first('').strip()
        address = ''.join(response.xpath('//div[@id="address"]//address//text()').extract()).replace('\n', '').replace('\t', '')
        images = []
        image_links = response.xpath('//ul[@id="images"]/li//img')
        for i, image_link in enumerate(image_links):
            image_url = image_link.xpath('./@src').extract_first()
            images.append(image_url)
        external_images_count = len(images)
        description = ''.join(response.xpath('//div[@id="description"]//text()').extract()).replace('\n', '').replace('\t', '')
        try:
            furnished_text = ''.join(response.xpath('//dt[contains(text(), "Furnished")]/following-sibling::dd//text()').extract())
            furnished = eval('False')
            if 'yes' in furnished_text.lower(): 
                furnished = eval('True')
        except:
            furnished = eval('False')
        try:
            elevator_text = ''.join(response.xpath('//dt[contains(text(), "Elevator")]/following-sibling::dd//text()').extract())
            elevator = eval('False')
            if 'yes' in elevator_text.lower():
                elevator = eval('True')
        except:
            elevator = eval('False')
        try:
            parking_text = ''.join(response.xpath('//dt[contains(text(), "Garages")]/following-sibling::dd//text()').extract())
            if int(parking_text) > 0:           
                parking = eval('True')
            else:
                parking = eval('False')
        except:
            parking = eval('False')
        
        try:
            terrace_xpath = response.xpath('//dt[contains(text(), "Terrace")]')
        except:
            terrace = eval('False')
        if terrace_xpath:
            terrace = eval('True') 
        else:
            terrace = eval('False')
        city = title.split('in')[1]
        landlord_name = response.xpath('//div[@class="member"]/span/text()').extract_first()
        landlord_phone= response.xpath('//div[@class="member"]/span/following-sibling::a/text()').extract_first()
        if response.meta['square_meters'] and response.meta['room_count'] and 'other' not in response.meta['property_types']:     
            item = {
                'external_link': response.meta['external_link'],
                'external_id': response.meta['external_id'],
                'latitude': str(response.meta['latitude']),
                'longitude': str(response.meta['longitude']),
                'property_types': response.meta['property_types'],
                'square_meters': response.meta['square_meters'],
                'room_count': int(response.meta['room_count']),
                'rent': int(response.meta['rent']),
                'currency': response.meta['currency'],
                'title': title,
                'address': address,
                'city': city,
                'images': images,
                'external_images_count': int(external_images_count),
                'description': description,
                'furnished': furnished,
                'elevator': elevator,
                'parking': parking,
                'terrace': terrace,
                'landlord_name': landlord_name,
                'landlord_phone': landlord_phone,
                'landlord_email': "immo@home-consult.be"       
            }
            yield item
        


