from game.player import Player
from game.game_state import GameState
from models.tile import Tile
from models.property_group import PropertyGroup
import random
from typing import List
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from models.trade_offer import TradeOffer

class RandomAgent(Player):
    def __init__(self, name):
        super().__init__(name)

    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        budget = game_state.player_balances[self]
        price = property.price

        if budget >= price\
            and not property in game_state.properties[self]\
            and not property in game_state.mortgaged_properties:
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

            for property in grouped_properties[group]:
                if property in game_state.mortgaged_properties:
                    should_upgrade = False
                    break
                
            if group_len == len(grouped_properties[group]):
                # if we can build a house
                if game_state.houses[group][0] < 4 and game_state.hotels[group][0] == 0:
                    price = group.house_cost() * group_len
                    if budget >= price and should_upgrade:
                        suggestions.append(group)
                        budget -= price
                # if we can build a hotel
                elif game_state.hotels[group][0] < 1 and game_state.houses[group][0] == 4:
                    price = group.hotel_cost() * group_len
                    if budget >= price and should_upgrade:
                        suggestions.append(group)
                        budget -= price


        return suggestions
    

    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        properties = [property for property in properties if not property in game_state.mortgaged_properties]
        suggestions = []

        for property in properties:
            should_mortgage = random.choice([True, False])
            can_be_mortgaged = not game_state.houses[property.group][0] > 0 and not game_state.hotels[property.group][0] > 0
            if should_mortgage and can_be_mortgaged:
                suggestions.append(property)
        return suggestions
    
    
    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        properties = [property for property in properties if property in game_state.mortgaged_properties]
        suggestions = []

        for property in properties:
            should_unmortgage = random.choice([True, False])
            if should_unmortgage:
                suggestions.append(property)
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
    

    def should_accept_trade_offer(self, game_state, trade_offer):
        return random.choice([True, False])
    

    def get_trade_offers(self, game_state) -> List[TradeOffer]:
        trade_offers = []

        for player in game_state.players:
            if player != self and random.choice([True, False]):
                properties_offered = []
                properties_requested = []
                money_offered = random.randint(0, game_state.player_balances[self])
                money_requested = random.randint(0, game_state.player_balances[player])
                jail_cards_offered = random.randint(0, game_state.escape_jail_cards[self])
                jail_cards_requested = random.randint(0, game_state.escape_jail_cards[player])

                for property in game_state.properties[self]:
                    if random.choice([True, False]) and\
                        not property in game_state.mortgaged_properties and\
                        (isinstance(property, Property) and game_state.houses[property.group][0] == 0 and game_state.hotels[property.group][0] == 0):
                        properties_offered.append(property)

                for property in game_state.properties[player]:
                    if random.choice([True, False]) and\
                        not property in game_state.mortgaged_properties and\
                        (isinstance(property, Property) and game_state.houses[property.group][0] == 0 and game_state.hotels[property.group][0] == 0):
                        properties_requested.append(property)

                if properties_offered == [] and properties_requested == [] and\
                    jail_cards_offered == 0 and jail_cards_requested == 0:
                    continue

                trade_offer = TradeOffer(
                    self,
                    player,
                    properties_offered,
                    money_offered,
                    jail_cards_offered,
                    properties_requested,
                    money_requested,
                    jail_cards_requested
                )
                trade_offers.append(trade_offer)

        return trade_offers




    