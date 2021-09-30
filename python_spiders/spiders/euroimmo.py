# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
import json, csv
import re
import html

class EuroimmoSpider(scrapy.Spider):
    name = 'euroimmo'
    allowed_domains = ['euroimmo']
    start_urls = ['https://www.euroimmo.be/']
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
            'zipcode',
            'city',
            'images',
            'external_images_count',
            'description',
            'terrace',
            'furnished',
            'landlord_name',
            'landlord_phone',
            'landlord_email'
        ]
    }
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        'content-type': 'application/json',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
    }
    
    def start_requests(self):
        
        url = 'https://www.euroimmo.be/Modules/ZoekModule/RESTService/SearchService.svc/GetPropertiesJSON/0/0'
        for i in range(1, 5):
            data = {
                "Transaction": "2",
                "Type": "0",
                "City": "0",
                "MinPrice": "0",
                "MaxPrice": "0",
                "MinSurface": "0",
                "MaxSurface": "0",
                "MinSurfaceGround": "0",
                "MaxSurfaceGround": "0",
                "MinBedrooms": "0",
                "MaxBedrooms": "0",
                "Radius": "0",
                "NumResults": "24",
                "StartIndex": "{}".format(i),
                "ExtraSQL": "0",
                "ExtraSQLFilters": "0",
                "NavigationItem": "0",
                "PageName": "0",
                "Language": "NL",
                "CountryInclude": "0",
                "CountryExclude": "0",
                "Token": "NVQRKGBDJNTISRRGABNFMCMPFJDNPHIUYDNIUAADPUHJZIGCZG",
                "SortField": "1",
                "OrderBy": "1",
                "UsePriceClass": "true",
                "PriceClass": "0",
                "SliderItem": "0",
                "SliderStep": "0",
                "CompanyID": "0",
                "SQLType": "3",
                "MediaID": "0",
                "PropertyName": "0",
                "PropertyID": "0",
                "ShowProjects": "false",
                "Region": "0",
                "currentPage": "0",
                "homeSearch": "0",
                "officeID": "0",
                "menuIDUmbraco": "0",
                "investment": "false",
                "useCheckBoxes": "false",
                "CheckedTypes": "0",
                "newbuilding": "false",
                "bedrooms": "0",
                "latitude": "0",
                "longitude": "0",
                "ShowChildrenInsteadOfProject": "false",
                "state": "0",
                "FilterOutTypes": "0"
            }
            req = Request(url=url, callback=self.parse_information, method='POST', body=json.dumps(data), headers=self.headers, dont_filter=True)
            yield req
    
    def parse_information(self, response):
        try:
            datas = json.loads(response.text)
        except:
            datas = ''
        if datas:
            for data in datas:
                if 'Garage' in data['Property_HeadType_Value']:
                    continue 
                external_link = 'https://www.euroimmo.be' + data['Property_URL']
                external_id = data['FortissimmoID']
                title = data['Property_Title']
                description = html.unescape(data['Property_Description'])
                try:
                    square_meters = float(re.findall(r'([\d|,|\.]+)', data['Property_Area_Build'].replace(' ', '').replace(',', '.'), re.S | re.M | re.I)[0])
                except:
                    square_meters = ''
                try:
                    rent = re.findall(r'\d+', data['Property_Price'].replace(',', '').replace('.', '').replace(' ', ''), re.S | re.M | re.I)[0]
                except:
                    rent = ''
                currency = 'EUR'
                latitude = data['Property_Lat']
                longitude = data['Property_Lon']
                zipcode = data['Property_Zip']
                property_types = data['Property_HeadType_Value']
                apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
                house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
                room_types = ['chambre']
                property_for_sale_type = ['property_for_sale']
                studio_types = ['studio']
                student_apartment_type = ['student_apartment']
                if property_types.lower() in apartment_types:
                    property_type = 'apartment'
                elif property_types.lower() in house_types:
                    property_type = 'house'
                elif property_types.lower() in room_types:
                    property_type = 'room'
                elif property_types.lower() in studio_types:
                    property_type = 'studio'
                elif property_types.lower() in property_for_sale_type:
                    property_type = 'property_for_sale'
                elif property_types.lower() in student_apartment_type:
                    property_type = 'student_apartment'
                else:
                    property_type = 'other'        
                room_count = data['bedrooms']
                city = data['Property_City_Value']
                address = zipcode + ' ' + city + ' ' + data['Property_Street'] + ' ' + data['Property_Number']
                req = Request(url=external_link, callback=self.parse_detail, headers=self.headers, dont_filter=True)
                req.meta['external_link'] = external_link
                req.meta['external_id'] = external_id
                req.meta['title'] = title
                req.meta['description'] = description
                req.meta['rent'] = rent
                req.meta['room_count'] = room_count
                req.meta['currency'] = currency
                req.meta['square_meters'] = square_meters
                req.meta['latitude'] = latitude
                req.meta['longitude'] = longitude
                req.meta['zipcode'] = zipcode
                req.meta['property_types'] = property_type
                req.meta['city'] = city
                req.meta['address'] = address
                yield req


    def parse_detail(self, response):
        image_links = response.xpath('//div[@id="galleryDetail"]//img[@class="rsTmb"]')
        images = []
        for image_link in image_links:
            image_url = response.urljoin(image_link.xpath('./@src').extract_first())
            images.append(image_url)
        external_images_count = len(images)
        terrace_xpath = response.xpath('//td[contains(text(), "Terras")]/following-sibling::td/text()').extract_first('')
        try:
            terrace_text = re.findall(r'\d+', terrace_xpath)[0]
        except:
            terrace_text = ''
        if terrace_text and int(terrace_text) > 0:
           terrace = eval('True')
        else:
            terrace = eval('False')
        furnished_xpath = response.xpath('//td[contains(text(), "Bemeubeld")]/following-sibling::td/text()').extract_first('')
        if furnished_xpath and 'Ja' in furnished_xpath:
            furnished = eval('True')
        else:
            furnished = eval('False')
        landlord_name = response.xpath('//div[@class="vertegenwoordiger"]/h3/text()').extract_first()
        landlord_phone = response.xpath('//a[@class="phone-vert"]/@href').extract_first().replace('tel:', '')
        if response.meta['rent'] and response.meta['square_meters'] and response.meta['room_count'] and '0' not in response.meta['room_count']  and 'other' not in response.meta['property_types']:    
            item = {
                'external_link': response.meta['external_link'],
                'external_id': response.meta['external_id'],
                'latitude': str(response.meta['latitude']),
                'longitude': str(response.meta['longitude']),
                'property_type': response.meta['property_types'],
                'square_meters': response.meta['square_meters'],
                'room_count': int(response.meta['room_count']),
                'rent': int(response.meta['rent']),
                'currency': response.meta['currency'],
                'title': response.meta['title'],
                'address': response.meta['address'],
                'zipcode': str(response.meta['zipcode']),
                'city': str(response.meta['city']),
                'images': images,
                'external_images_count': int(external_images_count),
                'description': response.meta['description'],
                'terrace': terrace,
                'furnished': furnished,
                'landlord_name': landlord_name,
                'landlord_phone': landlord_phone ,
                'landlord_email': "info@euroimmo.be"
            }
            yield item


    