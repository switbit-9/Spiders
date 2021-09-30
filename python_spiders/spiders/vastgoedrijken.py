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
import time

class VastgoedrijkenSpider(scrapy.Spider):
    name = 'vastgoedrijken'
    allowed_domains = ['vastgoedrijken']
    start_urls = ['https://www.vastgoedrijken.be/aanbod?spage=1&stype=0&sbuy=0&selector=type&set_place_data=0']
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
            'terras',
            'parking',
            'dishwasher',
            'elevator',
            'floor_plan_images',
            'floor_plan_images_count',
            'external_images_count',
            'landlord_phone',
            'landlord_email',
            'landlord_name'
        ]
    }

    def __init__(self):
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    headers = {
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    }
    def parse(self, response):
        self.driver.get(response.url)
        res = response.replace(body=self.driver.page_source)
        time.sleep(5)
        next_text = res.xpath('//div[contains(@class, "lister-results-text")]/text()').extract_first()
        print("::::::::::::::::",next_text)
        page_numbers = re.search(r'van\s(\d+)\s', next_text, re.S | re.M | re.I).group(1)
        print("KKKKKKKKKKKK:",page_numbers)
        numbers = int(int(page_numbers) / 10) + 1
        for i in range(1, numbers + 1):
            url = "https://www.vastgoedrijken.be/aanbod?spage={}&sbuy=0&smapcenter=51.18722_5.520263".format(i)
            req = Request(url=url, callback=self.parse_links, headers=self.headers, dont_filter=True)
            yield req

    def parse_links(self, response):
        print("+++++++++++++++++++++++", response.url)
        self.driver.get(response.url)
        time.sleep(5)
        res = response.replace(body=self.driver.page_source)
        if res.xpath('//div[@id="lister-container"]//a[@data-immo-id]'):
            for link in res.xpath('//div[@id="lister-container"]//a[@data-immo-id]'):

                url = response.urljoin(link.xpath('./@href').extract_first())
                print("&&&&&&&&&&&&&&&&&&&&&&&&", url)
                req = Request(url=url, callback=self.parse_first, headers=self.headers, dont_filter=True)
                yield req

    
    def parse_first(self, response):
        external_link = response.url
        external_id = str(re.search(r'vro(\d+)', response.url, re.S | re.M | re.I).group(1))
        title = ''.join(response.xpath('//h1//text()').extract())
        try:
            rent_text = ''.join(response.xpath('//div[@class="price"]//text()').extract()).replace(' ', '').replace('.', '').replace(',', '')
            rent = re.findall(r'\d+', rent_text, re.S | re.M | re.I)[0]
        except:
            rent = ''

        try:
            address_texts = response.xpath('//i[contains(@class, "icon-location")]/../text()').extract()
            address_text = []
            for a in address_texts:
                if not a:
                    continue
                a = a.strip()
                address_text.append(a)
            address = ''.join(address_text) 
        except:
            address = "Kaulillerdorp 57 - 3950 Kaulille"
        currency = 'EUR'
        try:
            room_count = int(response.xpath('//td[contains(text(), "Slaapkamers")]/following-sibling::td/text()').extract_first().replace(' ','').replace('\n', ''))
        except:
            room_count = ''
        try:
            square_meters_text = response.xpath('//td[contains(text(), "Bewoonbare oppervlakte")]/following-sibling::td/text()').extract_first().replace(' ','').replace('\n', '').replace(',', '.')
            square_meters = float(re.findall(r'([\d|,|\.]+)', square_meters_text)[0])
        except:
            square_meters = ''
        description = ''.join(response.xpath('//h2[contains(text(), "Beschrijving")]/following-sibling::div/div/p//text()').extract()).replace('\n', '').replace('">', '').strip()
        images = []
        image_links = response.xpath('//div[@class="card"]/div//img[@data-flickity-lazyload]')
        for image_link in image_links:
            image_url = response.urljoin(image_link.xpath('./@data-flickity-lazyload').extract_first())
            images.append(image_url)
        external_images_count = len(images)
        landlord_email = "info@vastgoedrijken.be"
        landlord_phone = " +32 (0)11/60.55.11"
        property_type_te = ''.join(response.xpath('//strong[contains(text(), "Type")]/../text()').extract())
        if 'appartement' in property_type_te.lower() or 'apartment' in property_type_te.lower() or 'flat' in property_type_te.lower() or 'piso' in property_type_te.lower() or 'atico' in property_type_te.lower() or 'penthouse' in property_type_te.lower() or 'duplex' in property_type_te.lower():
            property_type = 'apartment' 
        elif 'hus' in property_type_te.lower() or 'huis' in property_type_te.lower() or 'chalet' in property_type_te.lower() or 'bungalow' in property_type_te.lower() or 'maison' in property_type_te.lower() or 'house' in property_type_te.lower() or 'home' in property_type_te.lower() or 'villa' in property_type_te.lower():
            property_type = 'house'
        elif 'chambre' in property_type_te.lower():
            property_type = 'room'
        elif 'studio' in property_type_te.lower():
            property_type = 'studio'
        elif 'property_for_sale' in property_type_te.lower():
            property_type = 'property_for_sale'
        elif 'student_apartment' in property_type_te.lower():
            property_type = 'student_apartment'
        else:
            property_type = 'other'
        
        try:
            terras_xpath = response.xpath('//td[contains(text(), "Terras")]/following-sibling::td/text()').extract_first()
            if 'overdekt' in terras_xpath.lower():  
                terras = eval('False')
            else:
                terras = eval('True')
        except:
            terras = eval('False')
        parking_xpath = response.xpath('//td[contains(text(), "Autostandplaats")]')
        if parking_xpath:
            parking = eval('True')
        else:
            parking = eval('False')
        if 'vaatwasser' in description:
            dishwasher = eval('True')
        else:
            dishwasher = eval('False')
        if 'lift' in description:
            elevator = eval('True')
        else:
            elevator = eval('False')
        floor_plan_images = []
        floor_plan_imgs = response.xpath('//strong[contains(text(), "Downloads")]/following-sibling::div/a')
        for floor_plan_img in floor_plan_imgs:
            floor_plan_img_v = 'https://www.vastgoedrijken.be' + floor_plan_img.xpath('./@href').extract_first() 
            floor_plan_images.append(floor_plan_img_v)
        floor_plan_images_count = int(len(floor_plan_images))
        print("=============>main vlaues", rent, square_meters, room_count, property_type, external_link)
        if 'other' not in property_type and rent and square_meters and room_count:
            item = {
                'external_link': external_link,
                'external_id': external_id,
                'title': title,
                'description': description,
                'address': address,
                'property_type': property_type,
                'square_meters': square_meters,
                'room_count': room_count,
                'rent': int(rent),
                'currency': currency,
                'images': images,
                'terras': terras,
                'parking': parking,
                'dishwasher': dishwasher,
                'elevator': elevator,
                'floor_plan_images': floor_plan_images,
                'floor_plan_images_count': floor_plan_images_count,
                'external_images_count': int(external_images_count),
                'landlord_phone': landlord_phone,
                'landlord_email': 'info@lantmeeters.be',
                'landlord_name': "Vastgoed Rijken"
            }
                
            yield item