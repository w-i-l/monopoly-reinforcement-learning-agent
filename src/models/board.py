import json
import os

from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from models.other_tiles import Jail, Go, GoToJail, FreeParking, Taxes, Chance, CommunityChest
from utils.helper_functions import format_path


class Board:
    """
    Monopoly game board containing all tiles and providing board-related queries.
    
    This class manages the complete Monopoly board by loading all tiles from JSON
    configuration files and providing methods to query board state, find specific
    tiles, and group properties by various criteria.
    
    The board automatically loads and organizes all tile types including properties,
    utilities, railways, and special tiles (taxes, chance, community chest, etc.)
    from their respective data files. All tiles are sorted by their board position
    for consistent gameplay.
    
    Key features:
    - Automatic loading from JSON configuration files
    - Comprehensive tile querying and filtering methods
    - Property grouping by color and type
    - Special tile detection and handling
    - Board position-based tile access

    Attributes
    ----------
    tiles : List[Tile]
        Complete list of all board tiles sorted by position (0-39)
    """


    def __init__(self):
        """
        Initialize the Monopoly board by loading all tiles from configuration files.
        
        Loads properties, utilities, railways, and special tiles from their respective
        JSON files, combines them into a single sorted list by board position.
        """
        self.__load_tiles()


    def __load_tiles(self):
        """
        Load all tile types from JSON files and create the complete board.
        
        Combines properties, utilities, railways, and other special tiles into
        a single list sorted by board position for gameplay consistency.
        """

        properties = self.__load_properties()
        utilities = self.__load_utilities()
        railways = self.__load_railways()
        other_tiles = self.__load_other_tiles()

        self.tiles = properties + utilities + railways + other_tiles
        self.tiles.sort(key=lambda x: x.id)


    def get_jail_id(self) -> int:
        """
        Get the board position of the jail tile.
        
        Returns
        -------
        int
            Board position of the jail tile, or -1 if not found
        """

        for tile in self.tiles:
            if isinstance(tile, Jail):
                return tile.id
        return -1
    

    def has_landed_on_tax(self, position: int) -> None | Taxes:
        """
        Check if a board position contains a tax tile.
        
        Parameters
        ----------
        position : int
            Board position to check (0-39)
            
        Returns
        -------
        None | Taxes
            The tax tile if position contains one, None otherwise
        """

        tile = self.tiles[position]
        if isinstance(tile, Taxes):
            return tile
        return None


    def has_land_on_chance(self, position: int) -> None | Chance:
        """
        Check if a board position contains a chance tile.
        
        Parameters
        ----------
        position : int
            Board position to check (0-39)
            
        Returns
        -------
        None | Chance
            The chance tile if position contains one, None otherwise
        """

        tile = self.tiles[position]
        if isinstance(tile, Chance):
            return tile
        return None
    

    def has_land_on_community_chest(self, position: int) -> None | CommunityChest:
        """
        Check if a board position contains a community chest tile.
        
        Parameters
        ----------
        position : int
            Board position to check (0-39)
            
        Returns
        -------
        None | CommunityChest
            The community chest tile if position contains one, None otherwise
        """

        tile = self.tiles[position]
        if isinstance(tile, CommunityChest):
            return tile
        return None
    

    def has_landed_on_go_to_jail(self, position: int) -> bool:
        """
        Check if a board position is the "Go to Jail" tile.
        
        Parameters
        ----------
        position : int
            Board position to check (0-39)
            
        Returns
        -------
        bool
            True if position is "Go to Jail", False otherwise
        """

        tile = self.tiles[position]
        return isinstance(tile, GoToJail)
    

    def get_properties_by_group(self, group: PropertyGroup) -> list[Property]:
        """
        Get all properties belonging to a specific color group.
        
        Parameters
        ----------
        group : PropertyGroup
            The property color group to filter by
            
        Returns
        -------
        list[Property]
            List of all properties in the specified color group
        """
        return [property for property in self.tiles if isinstance(property, Property) and property.group == group]


    def get_property_by_name(self, name: str) -> Property:
        """
        Find a property by its name.
        
        Parameters
        ----------
        name : str
            Name of the property to find
            
        Returns
        -------
        Property
            The property with matching name, or None if not found
        """

        for tile in self.tiles:
            if isinstance(tile, Property) and tile.name == name:
                return tile
        return None
    

    def get_tile_by_name(self, name: str) -> Tile:
        """
        Find any tile by its name.
        
        Parameters
        ----------
        name : str
            Name of the tile to find
            
        Returns
        -------
        Tile
            The tile with matching name, or None if not found
        """

        for tile in self.tiles:
            if tile.name == name:
                return tile
        return None
    

    def get_utilities(self) -> list[Utility]:
        """
        Get all utility tiles on the board.
        
        Returns
        -------
        list[Utility]
            List of all utility tiles (Electric Company, Water Works)
        """
        return [utility for utility in self.tiles if isinstance(utility, Utility)]
    

    def get_railways(self) -> list[Railway]:
        """
        Get all railway tiles on the board.
        
        Returns
        -------
        list[Railway]
            List of all railway/railroad tiles
        """
        return [railway for railway in self.tiles if isinstance(railway, Railway)]
    

    def get_jail_fine(self) -> int:
        """
        Get the cost to pay the jail fine.
        
        Returns
        -------
        int
            Amount required to pay jail fine, or -1 if jail not found
        """

        for tile in self.tiles:
            if isinstance(tile, Jail):
                return tile.fine
        return -1


    def __load_utilities(self):
        """
        Load utility tiles from utilities.json configuration file.
        
        Returns
        -------
        list[Utility]
            List of utility tiles loaded from configuration
        """
        utilities = []

        with open(format_path("../data/utilities.json"), 'r') as f:
            data = json.load(f)
            for utility in data['properties']:
                id = utility['id']
                name = utility['name']
                utilities.append(Utility(id, name))

        return utilities


    def __load_railways(self):
        """
        Load railway tiles from railway_stations.json configuration file.
        
        Returns
        -------
        list[Railway]
            List of railway tiles loaded from configuration
        """
        railways = []

        with open(format_path("../data/railway_stations.json"), 'r') as f:
            data = json.load(f)
            for railway in data['properties']:
                id = railway['id']
                name = railway['name']
                railways.append(Railway(id, name))

        return railways


    def __load_properties(self):
        """
        Load property tiles from color group JSON files.
        
        Iterates through all PropertyGroup enums and loads properties from their
        respective JSON files, creating Property objects with complete rent and
        pricing information.
        
        Returns
        -------
        list[Property]
            List of all property tiles loaded from configuration files
        """
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
                    mortgage = property['mortgage']
                    buyback_price = property['buyback_price']
                    _properties.append(Property(id, name, group, price, base_rent, full_group_rent, house_rent, hotel_rent, mortgage, buyback_price))

        return _properties
    
    
    def __load_other_tiles(self):
        """
        Load special tiles from others.json configuration file.
        
        Loads and creates all non-property tiles including taxes, chance,
        community chest, and main board tiles (Go, Jail, Free Parking, etc.)
        based on their group classifications in the configuration file.
        
        Returns
        -------
        list[Tile]
            List of all special tiles loaded from configuration
        """
        tiles = []

        with open(format_path("../data/others.json"), 'r') as f:
            data = json.load(f)
            for other in data:
                group = other['group']

                if group == 'taxes':
                    # Load tax tiles with their tax amounts
                    for property in other['properties']:
                        id = property['id']
                        name = property['name']
                        tax = property['tax']
                        tiles.append(Taxes(id, name, tax))

                elif group == 'chance':
                    # Load chance tiles
                    for property in other['properties']:
                        id = property['id']
                        name = property['name']
                        tiles.append(Chance(id, name))

                elif group == 'community_chest':
                    # Load community chest tiles
                    for property in other['properties']:
                        id = property['id']
                        name = property['name']
                        tiles.append(CommunityChest(id, name))

                elif group == 'main_tiles':
                    # Load special main board tiles
                    for property in other['properties']:
                        id = property['id']
                        name = property['name']

                        # Create appropriate tile type based on name
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
    # Test board loading and display all tiles
    board = Board()
    for tile in board.tiles:
        print(tile.id, tile.name, end=" ")
        if hasattr(tile, 'group'):
            print(tile.group.color())
        else:
            print()