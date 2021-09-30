# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class ImmolegrandSpider(scrapy.Spider):
    name = 'immolegrand'
    allowed_domains = ['immolegrand']
    start_urls = ['https://www.immolegrand.com/']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
            'external_link',
            'external_id',
            'title',
            'description',
            'address',
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
        url = 'https://www.immolegrand.com/a-louer.php'
        req = Request(url=url, callback=self.parse_next, headers=self.headers, dont_filter=True)
        yield req

    def parse_next(self, response):
        pagenations = response.xpath('//div[contains(@class, "pagination")]/a')
        for pagenation in pagenations:
            next_link = response.urljoin(pagenation.xpath('./@href').extract_first())
            link_text = html.unescape(pagenation.xpath('./text()').extract_first())
            if '»' in link_text or '«' in link_text:
                continue
            print(link_text)
            req = Request(url=next_link, callback=self.parse_first, headers=self.headers, dont_filter=True)
            yield req   
    
    def parse_first(self, response):
        links = response.xpath('//div[@class="listing-biens"]//a[@class="infos"]')
        for link in links:
            url = response.urljoin(link.xpath('./@href').extract_first())
            property_te = link.xpath('./p/text()').extract_first()
            address = link.xpath('./span/text()').extract_first('')
            if not address:
                address = "Avenue Mascaux, 460 6001 Marcinelle (Charleroi)"
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_ts'] = property_te
            req.meta['address'] = address 
            yield req
        
    def parse_information(self, response):
        title = response.xpath('//meta[@porperty="og:title"]/@content').extract_first('').strip()
        title = re.sub(r'\r\n', '', title)
        external_id = response.url.split('/')[-1]
        price_v = response.xpath('//h1[@class="titreCap"]/text()').extract_first('').strip().replace('.', '').replace(',', '').replace(' ', '')
        price = re.findall(r'\d+', price_v, re.S | re.M | re.I)[0]
        currency_t = response.xpath('//h1[@class="titreCap"]/span/text()').extract_first('').strip()
        if 'euro' in currency_t.lower():
            currency = 'EUR' 
        
        description = ' '.join(response.xpath('//h3[contains(text(), "Description")]/following-sibling::p/text()').extract())
        try:
            square_meters_text = response.xpath('//span[contains(text(), "Surface habitale")]/../text()').extract_first('').strip().replace(',', '.').replace(' ','')
            square_meters = re.findall(r'([\d|,|\.]+)',square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        try:
            contact_info = re.search(r'renseignements:(.*)', description.lower().replace(' ', ''), re.S | re.M | re.I).group(1)
            landlord_phone = re.findall(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}', contact_info, re.S | re.M | re.I)[0]
            landlord_email = re.findall(r'[\w\.-]+@[\w\.-]+', contact_info, re.S | re.M | re.I)[0]
        except:
            try:
                contact_info = re.search(r'renseignement et visite:(.*)', description.lower().replace(' ', ''), re.S | re.M | re.I).group(1)
                landlord_phone = re.findall(r'\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4}', contact_info, re.S | re.M | re.I)[0]
                landlord_email = re.findall(r'[\w\.-]+@[\w\.-]+', contact_info, re.S | re.M | re.I)[0]
            except:
                landlord_phone = "071 36 21 30"
                landlord_email = "info@immolegrand.com" 
        try:
            room_count_t = response.xpath('//span[contains(text(), "Chambre(s)")]/../text()').extract_first('').strip()
            room_count = re.findall(r'\d+',room_count_t, re.S | re.M | re.I)[0]
        except:
            room_count = ''
        images = []
        image_links = response.xpath('//div[@class="photos animate"]//img')
        for image_link in image_links:
            image_url = image_link.xpath('./@src').extract_first('')
            images.append(image_url)
        external_images_count = len(images)
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
        if 'others' not in property_type and square_meters and room_count: 
            item = {
                'external_link': response.url,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': response.meta['address'],
                'property_type': property_type,
                'square_meters': float(square_meters),
                'room_count': int(room_count),
                'rent': int(price),
                'currency': currency,
                'images': images,
                'external_images_count': int(external_images_count),
                'landlord_email': landlord_email,
                'landlord_phone': landlord_phone,
                'landlord_name': "Immo Legrand"
            }
            
            yield item

         