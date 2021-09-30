# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import math


class UpworkSamplePipeline:
    def process_item(self, item, spider):
        images = item.get('images', None)
        description = item.get('description', None)
        rent = item.get('rent', None)
        square_meters = item.get('square_meters', None)
        room_count = item.get('room_count', None)
        if images:
            item['external_images_count'] = len(item['images'])
        if description:
            if ' parking ' in description.lower() or ' parkeerplaats ' in description.lower():
                item['parking'] = True
            if ' balcon' in description.lower():
                item['balcony'] = True
            if ' ascenseur ' in description.lower():
                item['elevator'] = True
            if ' terrasse ' in description.lower() or 'terrace' in description.lower():
                item['terrace'] = True
            if ' dishwasher ' in description.lower():
                item['dishwasher'] = True
        if rent:
            item['rent'] = int(rent)
        if square_meters:
            item['square_meters'] = math.ceil(float(square_meters))
        if room_count:
            item['room_count'] = int(room_count)

        return item
