from enum import Enum
import os
from utils.helper_functions import format_path
import json

class PropertyGroup(Enum):
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
        self._load_attributes()
        return type(self)._attr_cache[self.value]['house_cost']
    
    def hotel_cost(self) -> int:
        self._load_attributes()
        return type(self)._attr_cache[self.value]['hotel_cost']
    
    def color(self) -> str:
        self._load_attributes()
        return type(self)._attr_cache[self.value]['color']
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return self.value