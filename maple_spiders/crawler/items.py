# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class CrawlerItem(scrapy.Item):
    external_link = Field()
    external_id = Field()
    title = Field()
    description = Field()
    city = Field()
    zipcode = Field()
    address = Field()
    latitude = Field()
    longtitude = Field()
    property_type = Field()
    square_meters = Field()
    room_count = Field()
    available_date = Field()
    images = Field()
    floor_plan_images = Field()
    external_images_count = Field()
    rent = Field()
    currency = Field()
    deposit = Field()
    prepaid_rent = Field()
    utilities = Field()
    water_cost = Field()
    heating_cost = Field()
    energy_label = Field()
    pets_allowed = Field()
    furnished = Field()
    floor = Field()
    parking = Field()
    elevator = Field()
    balcony = Field()
    terrace = Field()
    swimming_pool = Field()
    washing_machine = Field()
    dishwasher = Field()
    landlord_name = Field()
    landlord_email = Field()
    landlord_phone = Field()
    position = Field()


# title - string - title of the listing
# description - text - the description of the listing (use html_to_text method always)
# city - string - city
# zipcode - string - zipcode if present
# address - string - the full address including zipcode and city of present(often not)
# property_type - enum - either “apartment”, “house” or “studio”. If not present, leave blank
# square_meters - integer - number of m2. Make sure to exclude “m2” so its only the number
# room_count - integer - number of room, typically called bedrooms
# available_date - date - the date this property is available to move into(needs to be parsed to a date. So if its written as “6th december 19” or any other format, parse it with Date.strftime)
# images - array - list of images in the highest resolution possible
# rent - integer - the rent per month. So you need to make “€ 200 / month” to “200”
# deposit - integer - if a security deposit is listed, add the amount of the deposit
# prepaid_rent - integer - amount needed to be paid before moving in(mostly not present)
# utilities - integer - if a total cost of water, heating and other utilities are present
# water_cost - integer - if a seperate price of water per month is listed
# heating_cost - integer - if a seperate price for heating is listed
# energy_label - string - if an energy label is stated. Not important, so only add if easy
# pets_allowed - boolean - true if pets are allowed, false if specifically not permitted.
# furnished - boolean - true if the property is furnished. They typically write if it is.
# floor - string - if its written that the apartment is located on ex. “3th floor”
# parking - boolean - true if parking is available, false if specified that its not
# elevator - boolean - true if elevator is present, false if specified not
# balcony - boolean - true if there's balcony, false if not
# terrace - boolean - true if there's terrace, false if not
# swimming_pool - boolean - true if there's swimming pool, false if not
# external_id - string - If the website lists a “reference” or some other ID for the user to note

# landlord_name - string - name of the real estate company(most often) or landlord to contact
# landlord_email - string - email of the real estate company(most often) or landlord to contact
# landlord_phone - string - phone of the real estate company(most often) or landlord to contact
