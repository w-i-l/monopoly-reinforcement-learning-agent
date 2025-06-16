from enum import Enum
import os
import json

from utils.helper_functions import format_path


class PropertyGroup(Enum):
    """
    Enumeration of Monopoly property color groups with configuration loading.
    
    Each property group represents a color set that players can monopolize for
    increased rent collection. Groups have associated costs for house and hotel
    development, as well as display colors for UI representation.
    
    The class automatically loads group-specific attributes (house costs, hotel costs,
    and colors) from JSON configuration files when first accessed, using lazy loading
    with caching for performance.
    
    Attributes
    ----------
    BROWN : PropertyGroup
        Brown property group (lowest rent tier)
    LIGHT_BLUE : PropertyGroup
        Light blue property group
    PINK : PropertyGroup
        Pink/magenta property group
    ORANGE : PropertyGroup
        Orange property group (high traffic from jail)
    RED : PropertyGroup
        Red property group (high traffic)
    YELLOW : PropertyGroup
        Yellow property group
    GREEN : PropertyGroup
        Green property group (highest rent tier)
    BLUE : PropertyGroup
        Blue property group (highest rent tier)
    """
    BROWN = "brown"
    LIGHT_BLUE = "light_blue"
    PINK = "pink"
    ORANGE = "orange"
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"


    @staticmethod
    def init_from(group: str) -> 'PropertyGroup':
        """
        Create PropertyGroup enum from string value.
        
        Parameters
        ----------
        group : str
            String representation of the property group
            
        Returns
        -------
        PropertyGroup
            Corresponding PropertyGroup enum value
        """
        return {
            'brown': PropertyGroup.BROWN,
            'light_blue': PropertyGroup.LIGHT_BLUE,
            'pink': PropertyGroup.PINK,
            'orange': PropertyGroup.ORANGE,
            'red': PropertyGroup.RED,
            'yellow': PropertyGroup.YELLOW,
            'green': PropertyGroup.GREEN,
            'blue': PropertyGroup.BLUE
        }[group]


    def _load_attributes(self):
        """
        Lazy load group attributes from JSON configuration files.
        
        Loads house costs, hotel costs, and display colors for all property groups
        from their respective JSON files. Results are cached at the class level
        to avoid repeated file I/O operations.
        """
        if not hasattr(self, '_attr_cache'):
            groups_path = '../data/properties/'
            groups = [
                group
                for group in os.listdir(format_path(groups_path)) 
            ]

            attr = {}
            for group in groups:
                with open(format_path(groups_path + group), 'r') as f:
                    data = json.load(f)
                    group = group.replace('.json', '')
                    attr[group] = {
                        'house_cost': data['house_cost'],
                        'hotel_cost': data['hotel_cost'],
                        'color': data['color']
                    }
            type(self)._attr_cache = attr


    def house_cost(self) -> int:
        """
        Get the cost to build one house on properties in this group.
        
        Returns
        -------
        int
            Cost in dollars to build one house
        """
        self._load_attributes()
        return type(self)._attr_cache[self.value]['house_cost']
    

    def hotel_cost(self) -> int:
        """
        Get the cost to build one hotel on properties in this group.
        
        Returns
        -------
        int
            Cost in dollars to build one hotel
        """
        self._load_attributes()
        return type(self)._attr_cache[self.value]['hotel_cost']
    

    def color(self) -> str:
        """
        Get the display color for this property group.
        
        Returns
        -------
        str
            Color name or hex code for UI display
        """
        self._load_attributes()
        return type(self)._attr_cache[self.value]['color']
    

    def __str__(self):
        return self.value
    
    
    def __repr__(self):
        return self.value