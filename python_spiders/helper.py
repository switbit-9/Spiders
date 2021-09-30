import re
from datetime import datetime


def remove_white_spaces(input_string):
    """
    Removes continuous spaces in the input string
    :param input_string:
    """
    return re.sub(r'\s+', ' ', input_string).strip()


def remove_unicode_char(input_string):
    return (''.join([i if ord(i) < 128 else ' ' for i in input_string])).strip()
    # return input_string.encode('ascii', 'ignore')


def extract_number_only(input_string):
    return (''.join(filter(lambda i: i.isdigit(), remove_white_spaces(input_string)))).strip()


def currency_parser(input_string):
    currency = None
    if u'\u20ac' in input_string:
        currency = 'EUR'
    elif u'\xa3' in input_string:
        currency = 'GBP'
    elif '$' in input_string:
        currency = 'USD'
    return currency


def format_date(input_string, date_format="%m/%d/%Y"):
    try:
        return datetime.strptime(input_string, date_format).strftime("%Y-%m-%d")
    except Exception as e:
        print(e)
        return input_string


property_type_lookup = {
    'Appartements': 'apartment',
    'apartment': 'apartment',
    'Appartement': 'apartment',
    'Huis': 'house',
    'Woning': 'house'
}
