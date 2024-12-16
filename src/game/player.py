from models.property import Tile
from models.property_group import PropertyGroup
from typing import List, Dict, Optional

# TODO: Allow player to upgrade/downgrade any number of times
# eg. buy 2 houses on one property and 1 house on another, instead of buying one house per call

class Player:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.name}"
    
    def should_buy_property(self, game_state, property: Tile) -> bool:
        # TODO: Implement the logic to decide if the player should buy the property
        return True
    
    def get_upgrading_suggestions(self, game_state) -> List[PropertyGroup]:
        # TODO: Implement the logic to suggest which properties to upgrade
        return []
    
    def get_mortgaging_suggestions(self, game_state) -> List[Tile]:
        # TODO: Implement the logic to suggest which properties to mortgage
        return []
    
    def get_downgrading_suggestions(self, game_state) -> List[Tile]:
        # TODO: Implement the logic to suggest which properties to downgrade
        return []
    
    def should_pay_get_out_of_jail_fine(self, game_state) -> bool:
        # TODO: Implement the logic to decide if the player should pay the fine to get out of jail
        return True
    
    def should_use_escape_jail_card(self, game_state) -> bool:
        # TODO: Implement the logic to decide if the player should use the get out of jail free card
        return True