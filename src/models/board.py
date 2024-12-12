from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from models.other_tiles import Jail, Go, GoToJail, FreeParking, Taxes, Chance, CommunityChest
import json
import os
from utils.helper_functions import format_path

class Board:
    def __init__(self):
        self.__load_tiles()

    def __load_tiles(self):
        properties = self.__load_properties()
        utilities = self.__load_utilities()
        railways = self.__load_railways()
        other_tiles = self.__load_other_tiles()

        self.tiles = properties + utilities + railways + other_tiles
        self.tiles.sort(key=lambda x: x.id)


    def get_jail_id(self) -> int:
        for tile in self.tiles:
            if isinstance(tile, Jail):
                return tile.id
        return -1
    
    def has_landed_on_tax(self, position: int) -> None | Taxes:
        tile = self.tiles[position]
        if isinstance(tile, Taxes):
            return tile
        return None


    def has_land_on_chance(self, position: int) -> None | Chance:
        tile = self.tiles[position]
        if isinstance(tile, Chance):
            return tile
        return None
    

    def has_land_on_community_chest(self, position: int) -> None | CommunityChest:
        tile = self.tiles[position]
        if isinstance(tile, CommunityChest):
            return tile
        return None
    

    def has_landed_on_go_to_jail(self, position: int) -> bool:
        tile = self.tiles[position]
        return isinstance(tile, GoToJail)
    

    def get_properties_by_group(self, group: PropertyGroup) -> list[Property]:
        return [property for property in self.tiles if isinstance(property, Property) and property.group == group]


    def get_property_by_name(self, name: str) -> Property:
        for tile in self.tiles:
            if isinstance(tile, Property) and tile.name == name:
                return tile
        return None

    def __load_utilities(self):
        utilities = []

        with open(format_path("../data/utilities.json"), 'r') as f:
            data = json.load(f)
            for utility in data['properties']:
                id = utility['id']
                name = utility['name']
                utilities.append(Utility(id, name))

        return utilities


    def __load_railways(self):
        railways = []

        with open(format_path("../data/railway_stations.json"), 'r') as f:
            data = json.load(f)
            for railway in data['properties']:
                id = railway['id']
                name = railway['name']
                railways.append(Railway(id, name))

        return railways

    def __load_properties(self):
        _properties = []

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
                    mortage = property['mortage']
                    buyback_price = property['buyback_price']
                    _properties.append(Property(id, name, group, price, base_rent, full_group_rent, house_rent, hotel_rent, mortage, buyback_price))

        return _properties
    

    def __load_other_tiles(self):
        tiles = []

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

        return tiles
    

if __name__ == "__main__":
    board = Board()
    for tile in board.tiles:
        print(tile.id, tile.name, end=" ")
        if hasattr(tile, 'group'):
            print(tile.group.color())
        else:
            print()

