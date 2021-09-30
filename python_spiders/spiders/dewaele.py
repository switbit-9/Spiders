# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
import json, csv
import re
import html
from selenium import webdriver
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
import demjson

class DewaeleSpider(scrapy.Spider):
    name = 'dewaele'
    allowed_domains = ['dewaele']
    start_urls = ['https://www.dewaele.com/nl/te-huur']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
            'external_link',
            'external_id',
            'title',
            'description',
            'terrace',
            'address',
            'zipcode',
            'city',
            'latitude',
            'longitude',
            'property_type',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'available_date',
            'images',
            'external_images_count',
            'landlord_name',
            'landlord_phone',
            'landlord_email'
        ]
    }

    def __init__(self):
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
    }
    def parse(self, response):
        self.driver.get(response.url)
        res = response.replace(body=self.driver.page_source)
        for link in res.xpath('//li[contains(@class, "pand-grid__item")]/div[@class="list-content"]/article/a'):
            url = response.urljoin(link.xpath('./@href').extract_first())
            req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True)
            yield req
        
        if res.xpath('//a[@rel="next"]/@href'):
            next_link = response.urljoin(res.xpath('//a[@rel="next"]/@href').extract_first())
            print(next_link)
            req = Request(url=next_link, callback=self.parse, headers=self.headers, dont_filter=True)
            yield req
    
    def parse_first(self, response):
        external_link = response.url
        compile_text = response.xpath('//script[contains(text(), "dataLayer")]/text()').extract_first().strip().replace('dataLayer = ', '').replace(';', '').replace('[', '').replace(']', '')
        data_complie_text = demjson.decode(compile_text)
        external_id = data_complie_text['id'] 
        property_type_te = data_complie_text['type']
        title = data_complie_text['titel']
        rent = data_complie_text['prijs']
        zipcode = data_complie_text['postcode']
        city = data_complie_text['stad']    
        street = response.xpath('//span[@id="address"]//text()').extract_first()
        address = street + ',' + zipcode + ' ' + city
        currency = 'EUR'
        try:
            room_count = int(response.xpath('//span[@id="bdrms"]/text()').extract_first().strip().replace(' ','').replace('\n', ''))
        except:
            room_count = ''
        try:
            square_meters_text = response.xpath('//span[@id="opp"]/text()').extract_first().strip().replace('\n', '').replace(' ','').replace(',','.')
            square_meters = float(re.findall(r'\d+', square_meters_text)[0])
        except:
            square_meters = ''
        description = ''.join(response.xpath('//div[@id="description"]/p//text()').extract()).replace('\n', '').strip()
        try:
            available_date = response.xpath('//b[contains(text(), "Beschikbaar vanaf")]/../text()').extract_first().replace(' ', '').replace('\n', '').strip()
            if '/' in available_date:
                available_date = ''
        except:
            available_date = ''
        images = []
        image_links = response.xpath('//div[@id="photos"]/div/a')
        for image_link in image_links:
            image_url = image_link.xpath('./img/@src').extract_first()
            images.append(image_url)
        external_images_count = len(images)
        latitude = re.search(r'\"a_geo_lat\":(.*?),', response.text).group(1).replace('\"', '')
        longitude = re.search(r'\"a_geo_lon\":(.*?),', response.text).group(1).replace('\"', '')
        landlord_name = response.xpath('//div[@class="bd"]/h3/text()').extract_first()
        landlord_email = "brugge@dewaele.com"
        landlord_phone = "050444999"
        terrace_xpath = ''.join(response.xpath('//b[contains(text(), "Terras")]/../text()').extract())
        try:
            if '/' in terrace_xpath:
                terrace = eval('False')
            else:
                terrace = eval('True')
        except:
            terrace = eval('False') 
        apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
        house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
        room_types = ['chambre']
        studio_types = ['studio']
        property_for_sale_type = ['property_for_sale']
        student_apartment_type = ['student_apartment']
        if property_type_te.lower() in apartment_types:
            property_type = 'apartment'
        elif property_type_te.lower() in house_types:
            property_type = 'house'
        elif property_type_te.lower() in room_types:
            property_type = 'room'
        elif property_type_te.lower() in studio_types:
            property_type = 'studio'
        elif property_type_te.lower() in property_for_sale_type:
            property_type = 'property_for_sale'
        elif property_type_te.lower() in student_apartment_type:
            property_type = 'student_apartment'
        else:
            property_type = 'other' 
        print("PPPPPPPP=============>", terrace)
        if 'other' not in property_type and room_count and square_meters and available_date:
            item = {
                'external_link': external_link,
                'external_id': external_id,
                'title': title,
                'description': description,
                'terrace': terrace, 
                'address': address,
                'zipcode': zipcode,
                'city': city,
                'latitude': latitude, 
                'longitude': longitude,
                'property_type': property_type,
                'square_meters': square_meters,
                'room_count': room_count,
                'rent': float(rent),
                'currency': currency,
                'available_date': str(available_date),
                'images': images,
                'external_images_count': int(external_images_count),
                'landlord_name': landlord_name,
                'landlord_phone': landlord_phone,
                'landlord_email': 'info@lantmeeters.be'
            }
                
            yield item