from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Identity
from crawler.items import CrawlerItem
from w3lib.html import remove_tags
import re


def strip_newlines(x):
    return x.replace("\n", " ").strip().strip("\n").strip()


def get_rent(value):
    return int(value.replace(".", ""))


def get_lower(value):
    return value.lower()


# ["apartment", "house", "room", "property_for_sale", "student_apartment", "studio"].
def property_type(value):

    apartment_list = [
        "service flats",
        "serviceflat",
        "bel-étage",
        "grond",
        "handelsgelijkvloers",
        "gelijkvloers app.",
        "duplex/triplex",
        "cha",
        "mixte",
    ]
    apartment_like_list = [
        "apartment",
        "duplex",
        "triplex",
        "flat",
        "appartement",
        "gelijkvloerse verdieping",
        "eengezinswoning",
        "horecapand",
        "immeuble mixte",
        "ground floor",
        "privée",
        "immeuble",
    ]

    house_list = [
        "herenhuis",
        "maison",
        "rez-de-chaussée",
        "emplacement",
        "maison de plain-pied",
        "loft",
        "huis",
        "penthouse",
        "woning",
        "rijwoning",
        "gemeubelde woning",
        "huis ",
        "résidence prestigieuse",
        "hôtel de maître",
        "maison de maître",
        "flat in charming house",
        "exceptional house",
        "country house",
        "excl villa",
        "benedenwoning",
        "dernier étage",
        "com",
        "meublé",
        "maison unifamiliale",
        "hôtel",
    ]
    house_like_list = [
        "villa",
        "home",
        "house",
        "chambre",
        "étage",
        "rangée",
        "winkelpand",
    ]

    comm_list = [
        "commercieel gelijkvloers",
        "individuele handelszaak",
        "bien",
        "commerce",
        "bureaux",
        "commercial groundfloor",
        "winkelruimte",
        "studentenkamer",
        "parkeerplaats",
        "garage box",
        "garagebox",
        "commercial building",
        "offices",
        "burelen ",
        "showroom ",
        "burelen",
        "commerce individuel",
        "immeuble commercial",
        "showroom",
        "commerciële winkel",
        "shopping center",
        "individual shop",
        "rez commercial",
        "commercial",
        "bedrijfsvastgoed",
        "commercial",
        "local commercial ",
        "commercial",
        "garage / parking",
    ]
    comm_like_list = [
        "handelszaak",
        "commercieel",
        "gebouw",
        "kantoor",
        "opslagplaats",
        "entrepot",
        "opslagruimte",
        "commerciele winkel",
        "commercial groundfloor",
        "handelspand",
        "bureelruimte",
        "met bureel ",
        "bureau",
        "entrepôt",
        "magasin",
        "kmo-unit",
        "baanwinkel",
        "office",
    ]

    if value in apartment_list or str_like(value, apartment_like_list):
        return "apartment"
    elif value in house_list or str_like(value, house_like_list):
        return "house"
    elif str_like(value, ["studio", "atelier"]):
        return "studio"
    elif value in ("room", "kamer"):
        return "room"
    elif value in (
        "gesloten garagebox",
        "buitenstaanplaats",
        "binnenstaanplaats",
        "horeca",
        "closed garage",
        "garage",
        "motorstandplaats",
        "assistentiewoning",
        "autostandplaats",
        "magazijn ",
        "staanplaats",
        "werkplaats ",
        "opslag",
        "inside parking",
        "industriel",
        "imm. mixte bur + rés.",
        "terrain à bâtir",
        "unité pme",
        "parking intérieur",
        "rez-de-ch. avec jardin",
        "gelijkvloerse verd. + tuin",
        "immeuble à usage multiple",
        "hangar (loods)",
        "industrieel",
        "parking/garage/box",
        "parking/boxe de garage",
        "100m2",
        "250m2",
        "parking",
        "non)",
        "industrie",
        "garage/parking",
        "rez de jardin",
        " plant",
        "dépôt",
    ):
        return "other"
    elif value in comm_list or str_like(value, comm_like_list):
        return "commercial"

    raise ValueError(f"Cannot find related property mapping for: {value}")


def str_like(item, keys):

    for key in keys:
        if key in item:
            return True

    return False


def get_int(value):
    return int(re.sub("\D", "", value))


def clean_space(value):
    return re.sub("\s{2,}", " ", value)


class MapleLoader(ItemLoader):
    default_item_class = CrawlerItem
    default_input_processor = MapCompose(remove_tags, strip_newlines)
    default_output_processor = TakeFirst()

    rent_in = MapCompose(get_int)
    property_type_in = MapCompose(get_lower, remove_tags, property_type)

    description_in = MapCompose(clean_space, remove_tags)

    room_count_in = MapCompose(get_int)
    square_meters_in = MapCompose(get_int)
    utilities_in = MapCompose(get_int)
    deposit_in = MapCompose(get_int)
    heating_cost_in = MapCompose(get_int)
    water_cost_in = MapCompose(get_int)
    prepaid_rent_in = MapCompose(get_int)

    furnished_in = Identity()
    floor_in = Identity()
    parking_in = Identity()
    elevator_in = Identity()
    terrace_in = Identity()
    swimming_pool_in = Identity()
    washing_machine_in = Identity()
    dishwasher_in = Identity()
    pets_allowed_in = Identity()

    images_out = Identity()
    floor_plan_images_out = Identity()
    # floor_out = Identity()
    # parking_out = Identity()
    # elevator_out = Identity()
    # terrace_out = Identity()
