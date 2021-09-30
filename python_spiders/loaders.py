from scrapy.loader import ItemLoader
from itemloaders.processors import Join, MapCompose
from .items import ListingItem

def filter_empty(_s):
    return _s or None

class ListingLoader(ItemLoader):
    default_item_class = ListingItem
    description_in = MapCompose(str.strip, filter_empty)
    description_out = Join(' ')

    title_out = Join()
    room_count_out = Join()

    rent_in = MapCompose(str.strip, filter_empty)
    rent_out = Join()

    external_link_out = Join()
    external_source_out = Join()
    address_out = Join()
    city_out = Join()
    zipcode_out = Join()

    def __init__(self, response):
        super(ListingLoader, self).__init__(response=response)
        self.images_in = MapCompose(response.urljoin)
