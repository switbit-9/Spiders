# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json, csv
import re
import html

class LagenceimmobiliereSpider(scrapy.Spider):
    name = 'lagenceimmobiliere'
    allowed_domains = ['Lagenceimmobiliere']
    start_urls = ['http://www.lagenceimmobiliere.be/']
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
            'terrace',
            'parking',
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
        url = 'http://www.lagenceimmobiliere.be/?page=liste&OxySeleOffr=L&OxyRequete=1&OxySeleOrdre=PRIX+ASC%2CCOMM+ASC+%2CCODE'
        req = Request(url=url, callback=self.parse_lists, headers=self.headers, dont_filter=True)
        yield req

    def parse_lists(self, response):
        
        links = response.xpath('//div[@id="grid"]/a[@class="bien"][contains(@style,"cursor: pointer")]')
        for link in links:
            url = "http://www.lagenceimmobiliere.be/index.php" + link.xpath('./@href').extract_first()
            property_tt = link.xpath('.//b/text()').extract_first()
            city = link.xpath('./div[@class="toHide"]/span/text()').extract_first()
            req = Request(url=url, callback=self.parse_information, headers=self.headers, dont_filter=True)
            req.meta['property_tt'] = property_tt
            req.meta['city'] = city
            yield req

    def parse_information(self, response):
        title = response.xpath('//meta[@property="og:title"]/@content').extract_first('').strip()
        title = re.sub(r'\r\n', '', title)
        external_id = response.xpath('//h1[@class="Titre"]/span[@class="reference_fiche"]/text()').extract_first('').strip()
        description = ''.join(response.xpath('//div[@id="annonce_fiche"]/div/text()').extract()).strip()
        description = re.sub('\n', '', description)
        image_links = response.xpath('//div[@id="galleria"]/img')
        images = []
        for image_link in image_links:
            image_url = image_link.xpath('./@src').extract_first('') 
            images.append(image_url)
        address = "31 Square Marguerite 1000 BRUXELLES"
        external_images_count = len(images)
        try:
            room_count = response.xpath('//div[contains(text(), "Bedrooms")]/following-sibling::div/text()').extract_first('')
        except:
            room_count = ''
        square_meters_text = response.xpath('//div[contains(text(), "Living surface")]/following-sibling::div/text()').extract_first().replace(' ', '').replace(',', '.')
        try:
            square_meters = re.findall(r'([\d|,|\.]+)', square_meters_text, re.S | re.M | re.I)[0]
        except:
            square_meters = ''
        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat','flat/studio', 'aticos', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_type = ['property_for_sale']
        student_apartment_type = ['student_apartment']
        if response.meta['property_tt'].lower() in apartment_types:
            property_type = 'apartment'
        elif response.meta['property_tt'].lower() in house_types:
            property_type = 'home'
        elif response.meta['property_tt'].lower() in room_types:
            property_type = 'room'
        elif response.meta['property_tt'].lower() in studio_types:
            property_type = 'studio'
        elif response.meta['property_tt'].lower() in property_for_sale_type:
            property_type = 'property_for_sale'
        elif response.meta['property_tt'].lower() in student_apartment_type:
            property_type = 'student_apartment'
        else:
            property_type = 'others'
        terrace = response.xpath('//div[contains(text(), "Terrace")]/following-sibling::div/text()').extract_first('')
        if terrace: 
            if 'yes' in terrace.lower():
                terrace = eval('True')
            else:
                terrace = eval('False')
        else:
            terrace = eval('False')
        try:
            parking = response.xpath('//div[contains(text(), "Parking places")]/following-sibling::div/text()').external_first('')
            if parking:
                parking = eval('True')
            else:
                parking = eval('False')
        except:
            parking = eval('False')
        price_text = ' '.join(response.xpath('//h1[@class="Titre"]/text()').extract()).replace(' ', '').replace('.', '').replace(',', '')
        price = re.findall(r'\d+', price_text, re.S | re.I | re.M)[0]
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
                'rent': int(price),
                'currency': currency,
                'terrace': terrace,
                'parking': parking,
                'images': images,
                'external_images_count': int(external_images_count),
                'landlord_email': "info@lagenceimmobiliere.be",
                'landlord_phone': "02/736.10.16 ",
                'landlord_name': "Immobilière sprl"
            }
            
            yield item