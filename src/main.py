from models.property import Property
from models.property_group import PropertyGroup
import json
from utils.helper_functions import format_path
from models.railway import Railway
from models.utility import Utility
from models.other_tiles import Taxes, Chance, CommunityChest, GoToJail, Jail, FreeParking, Go

tiles = []

for group in PropertyGroup:
    path = format_path(f'../data/properties/{group.value}.json')
    with open(path, 'r') as f:
        data = json.load(f)
        properties = data['properties']
        for property in properties:
            id = property['id']
            name = property['name']
            group = PropertyGroup.init_from(group.value)
            price = property['price']
            base_rent = property['base_rent']
            full_group_rent = property['full_group_rent']
            house_rent = property['house_rent']
            hotel_rent = property['hotel_rent']
            mortgage = property['mortgage']
            buyback_price = property['buyback_price']
            tiles.append(Property(id, name, group, price, base_rent, full_group_rent, house_rent, hotel_rent, mortgage, buyback_price))

with open(format_path("../data/railway_stations.json"), 'r') as f:
    data = json.load(f)
    for railway in data['properties']:
        id = railway['id']
        name = railway['name']
        tiles.append(Railway(id, name))

with open(format_path("../data/utilities.json"), 'r') as f:
    data = json.load(f)
    for utility in data['properties']:
        id = utility['id']
        name = utility['name']
        tiles.append(Utility(id, name))

with open(format_path("../data/others.json"), 'r') as f:
    data = json.load(f)
    for other in data:
        group = other['group']

        if group == 'taxes':
            for property in other['properties']:
                id = property['id']
                name = property['name']
                tax = property['tax']
                tiles.append(Taxes(id, name, tax))
        elif group == 'chance':
            for property in other['properties']:
                id = property['id']
                name = property['name']
                tiles.append(Chance(id, name))
        elif group == 'community_chest':
            for property in other['properties']:
                id = property['id']
                name = property['name']
                tiles.append(CommunityChest(id, name))
        elif group == 'main_tiles':
            for property in other['properties']:
                id = property['id']
                name = property['name']

                if name == 'Start':
                    tiles.append(Go(id, name))
                elif name == 'Inchisoare | Vizita':
                    tiles.append(Jail(id, name))
                elif name == 'Parcare':
                    tiles.append(FreeParking(id, name))
                elif name == 'Du-te la Inchisoare':
                    tiles.append(GoToJail(id, name))

for index, tile in enumerate(tiles):
    print(index, tile)

            