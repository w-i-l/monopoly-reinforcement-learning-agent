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
import numpy as np
from game.game_validation import GameValidation

class RandomAgent(Player):
    def __init__(self, name, cache_size=5000):
        self.cache_size = cache_size
        super().__init__(name)
        self.__populate_cache()


    def __populate_cache(self):
        # generating a list of boolean values
        # with a size of cache_size

        self._cache = np.random.rand(self.cache_size)
        # converting the values to boolean
        self._cache = self._cache > 0.5
        self._cache = self._cache.tolist()


    def random_choice(self) -> bool:
        if len(self._cache) == 0:
            self.__populate_cache()

        choice = self._cache.pop()
        return choice
        

    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        if error := GameValidation.validate_buy_property(game_state, self, property):
            return False
        
        return self.random_choice()
    

    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        properties = [property for property in properties if not property in game_state.mortgaged_properties]

        suggestions = []

        for property in properties:
            should_mortgage = self.random_choice()

            if error := GameValidation.validate_mortgage_property(game_state, self, property):
                # can t mortgage this property
                continue

            if should_mortgage:
                suggestions.append(property)

        return suggestions
    
    
    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        properties = [property for property in properties if property in game_state.mortgaged_properties]

        suggestions = []

        for property in properties:
            should_unmortgage = self.random_choice()

            if error := GameValidation.validate_unmortgage_property(game_state, self, property):
                # can t unmortgage this property
                continue

            if should_unmortgage:
                suggestions.append(property)

        return suggestions
    

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
            should_upgrade = self.random_choice

            for property in grouped_properties[group]:
                if property in game_state.mortgaged_properties:
                    # can t upgrade this group
                    break

            # if we can upgrade this group
            else :
                if group_len == len(grouped_properties[group]):
                    # if we can build a house
                    if error := GameValidation.validate_place_house(game_state, self, group):
                        pass
                    else:
                        price = group.house_cost() * group_len
                        if budget >= price and should_upgrade:
                            suggestions.append(group)
                            budget -= price
                            continue # we can t build a hotel

                    # if we can build a hotel
                    if error := GameValidation.validate_place_hotel(game_state, self, group):
                        pass
                    else:
                        price = group.hotel_cost() * group_len
                        if budget >= price and should_upgrade:
                            suggestions.append(group)
                            budget -= price

        return suggestions
    

    def get_downgrading_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        properties = [property for property in properties if isinstance(property, Property)]
        grouped_properties = {property.group: [] for property in properties if isinstance(property, Property)}

        for property in properties:
            grouped_properties[property.group].append(property)

        suggestions = []

        for group in grouped_properties:
            group_len = len(game_state.board.get_properties_by_group(group))
            should_downgrade = self.random_choice()

            for property in grouped_properties[group]:
                if property in game_state.mortgaged_properties:
                    # can t downgrade this group
                    break

            else: #if we can downgrade this group
                if group_len == len(grouped_properties[group]):
                    # if we can sell a house
                    if error := GameValidation.validate_sell_house(game_state, self, group):
                        pass
                    else:
                        if should_downgrade:
                            suggestions.append(group)
                            continue # we can t sell a hotel

                    # if we can sell a hotel
                    if error := GameValidation.validate_sell_hotel(game_state, self, group):
                        pass
                    else:
                        if should_downgrade:
                            suggestions.append(group)

        return suggestions
    

    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        budget = game_state.player_balances[self]
        fine = game_state.board.get_jail_fine()

        should_pay = self.random_choice()
        return budget >= fine and should_pay
    

    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        cards = game_state.escape_jail_cards[self]
        should_use = self.random_choice()
        return cards > 0 and should_use
    

    def should_accept_trade_offer(self, game_state, trade_offer):
        if error := GameValidation.validate_trade_offer(game_state, trade_offer):
            return False
        
        return self.random_choice()
    

    def get_trade_offers(self, game_state) -> List[TradeOffer]:
        trade_offers = []

        for player in game_state.players:
            if player != self and self.random_choice():
                # Generate a random trade offer
                properties_offered = []
                properties_requested = []

                player_balance = game_state.player_balances[player]
                money_offered = random.randint(0, player_balance) if player_balance > 0 else 0
                money_requested = random.randint(0, player_balance) if player_balance > 0 else 0

                jail_cards = game_state.escape_jail_cards
                jail_cards_offered = random.randint(0, jail_cards[self]) if jail_cards[self] > 0 else 0
                jail_cards_requested = random.randint(0, jail_cards[player]) if jail_cards[player] > 0 else 0

                for property in game_state.properties[self]:
                    if error := GameValidation.validate_property_in_trade_offer(game_state, property, self):
                        # can t offer this property
                        continue
                    elif self.random_choice():
                        properties_offered.append(property)

                for property in game_state.properties[player]:
                    if error := GameValidation.validate_property_in_trade_offer(game_state, property, player):
                        # can t request this property
                        continue
                    elif self.random_choice():
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

                if error := GameValidation.validate_trade_offer(game_state, trade_offer):
                    # can t make this trade offer
                    continue

                trade_offers.append(trade_offer)

        return trade_offers




    