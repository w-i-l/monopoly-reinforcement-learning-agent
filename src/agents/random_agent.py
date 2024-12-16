from game.player import Player
from game.game_state import GameState
from models.tile import Tile
from models.property_group import PropertyGroup
import random
from typing import List
from models.property import Property
from models.utility import Utility
from models.railway import Railway

class RandomAgent(Player):
    def __init__(self, name):
        super().__init__(name)

    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        budget = game_state.player_balances[self]
        price = property.price

        if budget >= price:
            return random.choice([True, False])
        return False
    
    
    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        grouped_properties = {property.group: [] for property in properties if isinstance(property, Property)}

        for property in properties:
            grouped_properties[property.group].append(property)

        budget = game_state.player_balances[self]
        suggestions = []

        for group in grouped_properties:
            group_len = len(game_state.board.get_properties_by_group(group))
            should_upgrade = random.choice([True, False])

            if group_len == len(grouped_properties[group]):
                # if we can build a house
                if game_state.houses[group][0] < 4:
                    price = group.house_cost() * group_len
                    if budget >= price and should_upgrade:
                        suggestions.append(group)
                        budget -= price
                # if we can build a hotel
                elif game_state.hotels[group][0] < 1:
                    price = group.hotel_cost() * group_len
                    if budget >= price and should_upgrade:
                        suggestions.append(group)
                        budget -= price


        return suggestions
    

    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        properties = [property for property in properties if not property in game_state.mortgaged_properties]
        print(properties)
        budget = game_state.player_balances[self]
        suggestions = []

        print("mortgaging suggestions: ", properties)
        for property in properties:
            should_mortgage = random.choice([True, False])
            can_be_mortgaged = not game_state.houses[property.group][0] > 0 and not game_state.hotels[property.group][0] > 0
            if should_mortgage and can_be_mortgaged:
                suggestions.append(property)
                print("mortgaging suggestions: ", suggestions)
        return suggestions
    

    def get_downgrading_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        grouped_properties = {property.group: [] for property in properties if isinstance(property, Property)}

        for property in properties:
            grouped_properties[property.group].append(property)

        budget = game_state.player_balances[self]
        suggestions = []

        for group in grouped_properties:
            group_len = len(game_state.board.get_properties_by_group(group))
            should_downgrade = random.choice([True, False])

            if group_len == len(grouped_properties[group]):
                # if we can sell a house
                if game_state.houses[group][0] > 0:
                    price = group.house_cost() * group_len // 2
                    if should_downgrade:
                        suggestions.append(group)
                        budget += price
                # if we can sell a hotel
                elif game_state.hotels[group][0] > 0:
                    price = group.hotel_cost() * group_len // 2
                    if should_downgrade:
                        suggestions.append(group)
                        budget += price

        return suggestions
    

    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        budget = game_state.player_balances[self]
        fine = game_state.board.get_jail_fine()
        should_pay = random.choice([True, False])
        return budget >= fine and should_pay
    

    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        cards = game_state.escape_jail_cards[self]
        should_use = random.choice([True, False])
        return cards > 0 and should_use
    



    