import random
from typing import List
import numpy as np

from game.player import Player
from game.game_state import GameState
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from models.trade_offer import TradeOffer
from game.game_validation import GameValidation
from game.bankruptcy_request import BankruptcyRequest


class RandomAgent(Player):
    """
    Random baseline agent for Monopoly that makes decisions using cached random choices.
    
    This agent serves as a baseline for comparison with more sophisticated agents by
    making purely random decisions for all game actions. All decisions are subject to
    game rule validation, with invalid actions being skipped automatically.
    
    The agent uses a pre-generated cache of random boolean values for performance
    optimization, avoiding repeated calls to random number generation during gameplay.

    Attributes
    ----------
    cache_size : int
        Size of the pre-generated random choice cache for performance optimization
    _cache : List[bool]
        Internal cache of pre-generated random boolean values
    """


    def __init__(self, name: str, cache_size: int = 5000):
        """
        Initialize a new RandomAgent with cached random choices.
        
        Parameters
        ----------
        name : str
            Display name for this agent used in games and tournaments
        cache_size : int, default 5000
            Number of random boolean values to pre-generate for performance
        """
        self.cache_size = cache_size
        super().__init__(name)
        self.__populate_cache()


    def __populate_cache(self):
        """
        Generate a cache of random boolean values for decision making.
        
        Creates cache_size random values converted to boolean using 0.5 threshold.
        Called automatically during initialization and when cache is depleted.
        """
        # generating a list of boolean values
        # with a size of cache_size
        self._cache = np.random.rand(self.cache_size)
        # converting the values to boolean
        self._cache = self._cache > 0.5
        self._cache = self._cache.tolist()


    def random_choice(self) -> bool:
        """
        Get the next random boolean choice from the cache.
        
        Returns
        -------
        bool
            Random boolean value, with cache automatically replenished when empty
        """
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
        # filtering only properties
        properties = [tile for tile in properties if isinstance(tile, Property)]
        # filtering out mortgaged properties
        properties = [property for property in properties if not property in game_state.mortgaged_properties]

        suggestions = []

        for property in properties:
            should_mortgage = self.random_choice()

            if error := GameValidation.validate_mortgage_property(game_state, self, property):
                # can t mortgage this property
                continue

            elif should_mortgage:
                suggestions.append(property)

        return suggestions
    
    
    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        # filtering only properties
        properties = [tile for tile in properties if isinstance(tile, Property)]
        # filtering out unmortgaged properties
        properties = [property for property in properties if property in game_state.mortgaged_properties]

        suggestions = []

        for property in properties:
            should_unmortgage = self.random_choice()

            if error := GameValidation.validate_unmortgage_property(game_state, self, property):
                # can t unmortgage this property
                continue

            elif should_unmortgage:
                suggestions.append(property)

        return suggestions
    

    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = game_state.properties[self]
        # filtering only properties
        properties = [property for property in properties if isinstance(property, Property)]
        # grouping properties by their group
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
                        # if we can afford to build a house
                        # and we should upgrade
                        if budget >= price and should_upgrade:
                            suggestions.append(group)
                            budget -= price
                            continue # we can t build a hotel

                    # if we can build a hotel
                    if error := GameValidation.validate_place_hotel(game_state, self, group):
                        pass
                    else:
                        # if we can afford to build a hotel
                        # and we should upgrade
                        price = group.hotel_cost() * group_len
                        if budget >= price and should_upgrade:
                            suggestions.append(group)
                            budget -= price

        return suggestions
    

    def get_downgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = game_state.properties[self]
        # filtering only properties
        properties = [property for property in properties if isinstance(property, Property)]
        # grouping properties by their group
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
    

    def should_accept_trade_offer(self, game_state: GameState, trade_offer: TradeOffer) -> bool:
        if error := GameValidation.validate_trade_offer(game_state, trade_offer):
            return False
        
        return self.random_choice()
    

    def get_trade_offers(self, game_state: GameState) -> List[TradeOffer]:
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
                    pass

                else:
                    trade_offers.append(trade_offer)

        return trade_offers


    def handle_banckruptcy(self, game_state: GameState, amount: int) -> BankruptcyRequest:
        # Quick return if we have enough money
        current_balance = game_state.player_balances[self]
        if current_balance >= amount:
            return BankruptcyRequest([], [], [])
        
        needed_amount = amount - current_balance
        money_raised = 0
        
        # Use sets for faster lookups
        owned_properties = set(game_state.properties[self])
        mortgaged_properties = set(prop for prop in owned_properties if prop in game_state.mortgaged_properties)
        unmortgaged_properties = owned_properties - mortgaged_properties
        
        # Pre-calculate mortgageable properties to avoid redundant checks later
        properties_with_buildings = set()
        downgrade_suggestions = []
        mortgage_suggestions = []
        
        # Fast path: Check if we can raise enough money by just mortgaging properties
        # This avoids the expensive building calculations if possible
        quick_mortgage_value = 0
        mortgageable_props = []
        
        for prop in unmortgaged_properties:
            if not isinstance(prop, Property):
                # Utilities and railroads can always be mortgaged
                mortgageable_props.append(prop)
                quick_mortgage_value += prop.mortgage
        
        # If we can raise enough just with utilities and railroads, do that
        if quick_mortgage_value >= needed_amount:
            for prop in mortgageable_props:
                mortgage_suggestions.append(prop)
                money_raised += prop.mortgage
                if money_raised >= needed_amount:
                    break
            return BankruptcyRequest([], mortgage_suggestions, [])
        
        # We need to consider buildings - identify groups with buildings once
        groups_with_buildings = {}
        for group in PropertyGroup:
            # Skip groups we don't fully own
            group_properties = set(game_state.board.get_properties_by_group(group))
            if not group_properties.issubset(owned_properties):
                continue
            
            # Check for hotels or houses
            hotel_count, hotel_owner = game_state.hotels[group]
            house_count, house_owner = game_state.houses[group]
            
            if (hotel_count > 0 and hotel_owner == self) or (house_count > 0 and house_owner == self):
                # Store the building info for this group
                groups_with_buildings[group] = {
                    'hotel_count': hotel_count if hotel_owner == self else 0,
                    'house_count': house_count if house_owner == self else 0,
                    'prop_count': len(group_properties),
                    'properties': group_properties
                }
                # Mark these properties as having buildings
                properties_with_buildings.update(group_properties)
        
        # STEP 1: Sell buildings (hotels first, then houses)
        for group, info in groups_with_buildings.items():
            if money_raised >= needed_amount:
                break
                
            # Sell hotel if any
            if info['hotel_count'] > 0:
                hotel_value = group.hotel_cost() // 2
                downgrade_suggestions.append(group)
                money_raised += hotel_value
                
                # If selling the hotel is enough, we're done
                if money_raised >= needed_amount:
                    break
            
            # Sell houses if any
            house_count = info['house_count']
            if house_count > 0:
                house_value_per_level = group.house_cost() * info['prop_count'] // 2
                houses_needed = min(house_count, 
                                    (needed_amount - money_raised + house_value_per_level - 1) // house_value_per_level)
                houses_needed = int(houses_needed)
                
                # Add group multiple times based on how many levels we need to sell
                for _ in range(houses_needed):
                    downgrade_suggestions.append(group)
                    money_raised += house_value_per_level
        
        # STEP 2: Mortgage properties if needed
        if money_raised < needed_amount:
            # Add properties that don't have buildings or whose buildings we're removing
            for prop in unmortgaged_properties:
                if money_raised >= needed_amount:
                    break
                    
                can_mortgage = True
                
                if prop in properties_with_buildings:
                    # For properties with buildings, check if we're selling all buildings
                    if isinstance(prop, Property):
                        group = prop.group
                        if group in groups_with_buildings:
                            group_info = groups_with_buildings[group]
                            
                            # Count how many downgrades we're doing for this group
                            downgrade_count = downgrade_suggestions.count(group)
                            
                            # Check if we're removing all buildings
                            if group_info['hotel_count'] > 0:
                                # For hotel, need at least 1 downgrade
                                can_mortgage = downgrade_count >= 1
                            else:
                                # For houses, need enough downgrades to remove all
                                can_mortgage = downgrade_count >= group_info['house_count']
                            can_mortgage = False
                
                if error := GameValidation.validate_mortgage_property(game_state, self, prop):
                    can_mortgage = False
                    
                if can_mortgage:
                    mortgage_suggestions.append(prop)
                    money_raised += prop.mortgage
        
        # If we still haven't raised enough, return empty request (bankruptcy)
        if money_raised < needed_amount:
            return BankruptcyRequest([], [], [])
        
        return BankruptcyRequest(downgrade_suggestions, mortgage_suggestions, [])