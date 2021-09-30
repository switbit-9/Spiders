# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request, FormRequest
import json, csv
import re
import html

class CarlmartensSpider(scrapy.Spider):
    name = 'carlmartens'
    allowed_domains = ['carlmartens']
    start_urls = ['https://www.carlmartens.be/']
    custom_settings = {
        'FEED_URI': '{}.json'.format(name),
        'FEED_FORMAT': 'json',
        'FEED_EXPORT_FIELDS' : [
            'external_link',
            'external_id',
            'title',
            'property_types',
            'square_meters',
            'room_count',
            'rent',
            'currency',
            'address',
            'city',
            'latitude',
            'longitude',
            'zipcode',
            'images',
            'external_images_count',
            'description',
            'furnished',
            'elevator',
            'terrace',
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
        
        url = 'https://www.carlmartens.be/Modules/ZoekModule/RESTService/SearchService.svc/GetPropertiesJSON/0/0'
        for i in range(1, 3):
            data = {
                "Transaction":"2",
                "Type":"0",
                "City":"0",
                "MinPrice":"0",
                "MaxPrice":"0",
                "MinSurface":"0",
                "MaxSurface":"0",
                "MinSurfaceGround":"0",
                "MaxSurfaceGround":"0",
                "MinBedrooms":"0",
                "MaxBedrooms":"0",
                "Radius":"0",
                "NumResults":"30",
                "StartIndex":"{}".format(i),
                "ExtraSQL":"0",
                "ExtraSQLFilters":"0",
                "NavigationItem":"0",
                "PageName":"0",
                "Language":"NL",
                "CountryInclude":"0",
                "CountryExclude":"0",
                "Token":"ITMCCVIQENBBUJUKBFDOVRTBRHYWKFRFICQPXNYOUEQVEIXMXN",
                "SortField":"1",
                "OrderBy":"1",
                "UsePriceClass": "false",
                "PriceClass":"0",
                "SliderItem":"0",
                "SliderStep":"0",
                "CompanyID":"0",
                "SQLType":"3",
                "MediaID":"0",
                "PropertyName":"0",
                "PropertyID":"0",
                "ShowProjects": "false",
                "Region":"0",
                "currentPage":"0",
                "homeSearch":"0",
                "officeID":"0",
                "menuIDUmbraco":"0",
                "investment":"false",
                "useCheckBoxes":"false",
                "CheckedTypes":"0",
                "newbuilding":"false",
                "bedrooms":"0",
                "latitude":"0",
                "longitude":"0",
                "ShowChildrenInsteadOfProject":"false",
                "state":"0",
                "FilterOutTypes":""
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
                external_link = 'https://www.carlmartens.be/nl' + data['Property_URL']
                external_id = data['FortissimmoID']
                title = data['Property_Title']
                description = html.unescape(data['Property_Description']).replace('\n', '')
                description = re.sub('<[^>]*>', '', description)

                try:
                    square_meters = float(re.findall(r'([\d|,|\.]+)', data['Property_Area_Build'].replace(' ', '').replace(',', '.'), re.S | re.M | re.I)[0])
                except:
                    square_meters = ''
                try:
                    rent = int(re.findall(r'\d+', data['Property_Price'].replace(',', '').replace('.', '').replace(' ', ''), re.S | re.M | re.I)[0])
                except:
                    rent = ''
                currency = 'EUR'
                latitude = data['Property_Lat']
                longitude = data['Property_Lon']
                zipcode = data['Property_Zip']
                property_type_e = data['Property_HeadType_Value']
                apartment_types = ['lejlighed', 'appartement', 'apartment', 'piso', 'flat', 'atico', 'penthouse', 'duplex', 't1', 't2', 't3', 't4', 't5', 't6']
                house_types = ['hus', 'huis', 'chalet', 'bungalow', 'maison', 'house', 'home', 'villa']
                room_types = ['chambre']
                studio_types = ['studio']
                property_for_sale_type = ['property_for_sale']
                student_apartment_type = ['student_apartment']
                if property_type_e.lower() in apartment_types:
                    property_type = 'apartment'
                elif property_type_e.lower() in house_types:
                    property_type = 'house'
                elif property_type_e.lower() in room_types:
                    property_type = 'room'
                elif property_type_e.lower() in studio_types:
                    property_type = 'studio'
                elif property_type_e.lower() in property_for_sale_type:
                    property_type = 'property_for_sale'
                elif property_type_e.lower() in student_apartment_type:
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
        
        image_links = response.xpath('//script[contains(text(), "arrImages")]/text()').extract_first()
        image_links_regex = re.findall(r'arrImages\.push\(\{src\:.*', image_links)
        images = []
        for image_link_regex in image_links_regex:
            image_url = 'https://www.carlmartens.be' + str(re.search(r'arrImages\.push\(\{src\:(.*?)}', image_link_regex).group(1).replace("'", '').replace(' ',''))
            images.append(image_url)
        external_images_count = len(images)
        try:
            furnished_text = ''.join(response.xpath('//td[contains(text(), "Bemeubeld")]/following-sibling::td/text()').extract()).replace(' ', '')
        except:
            furnished_text = ''
        if furnished_text and 'Ja' in furnished_text:
            furnished = eval('True')
        else:
            furnished = eval('False')
        try:
            elevator_text = ''.join(response.xpath('//td[contains(text(), "Certificaat elektriciteit")]/following-sibling::td/text()').extract()).replace(' ', '')
        except:
            elevator_text = ''
        if elevator_text and 'Ja' in elevator_text:
            elevator = eval('True')
        else:
            elevator = eval('False')
        try:
            terrace_text = response.xpath('//th[contains(text(), " Terras")]/following-sibling::td/text()').extract_first().replace(' ', '')
        except:
            terrace_text = '0'
        if int(terrace_text) > 0:
            terrace = eval('True')
        else:
            terrace = eval('False')
        landlord_name = response.xpath('//div[@class="info"]/span/text()').extract_first()
        landlord_phone = response.xpath('//div[@class="info"]/a/text()').extract_first()
        if response.meta['square_meters'] and 'other' not in response.meta['property_types'] and response.meta['rent']:
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
                'title': response.meta['title'],
                'address': response.meta['address'],
                'images': images,
                'external_images_count': int(external_images_count),
                'description': response.meta['description'],
                'zipcode': response.meta['zipcode'],
                'city': response.meta['city'],
                'furnished': furnished,
                'elevator': elevator,
                'terrace': terrace,
                'landlord_name': str(landlord_name),
                'landlord_phone': str(landlord_phone),
                'landlord_email': "immo@carlmartens.be" 
            }
            
            yield item


    