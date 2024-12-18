from game.player import Player
from game.game_state import GameState
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from typing import List, Dict, Set

class StrategicAgent(Player):
    def __init__(self, name):
        super().__init__(name)
        self.property_values = {}  # Cache for property valuations
        
    def calculate_property_value(self, game_state: GameState, property: Tile) -> float:
        """Calculates strategic value of a property based on multiple factors."""
        if property in self.property_values:
            return self.property_values[property]
        
        base_value = property.price
        value_multiplier = 1.0

        if isinstance(property, Property):
            # Value complete color sets higher
            group_properties = game_state.board.get_properties_by_group(property.group)
            owned_in_group = sum(1 for p in group_properties if p in game_state.properties[self])
            total_in_group = len(group_properties)
            
            # High value for completing a set
            if owned_in_group == total_in_group - 1:
                value_multiplier *= 1.5
            
            # Value properties with high rent return
            rent_to_cost = property.hotel_rent / property.price
            value_multiplier *= (1 + rent_to_cost)
            
            # Value properties that others land on frequently
            landing_probability = {
                6: 1.3,  # 6 spaces from Start
                16: 1.2, # Common dice roll sums
                26: 1.2,
                9: 1.1,
                4: 1.1,
                10: 1.1
            }.get(property.id, 1.0)
            value_multiplier *= landing_probability

        elif isinstance(property, Railway):
            owned_railways = sum(1 for p in game_state.properties[self] if isinstance(p, Railway))
            value_multiplier *= (1.2 ** owned_railways)  # Railways become more valuable together

        elif isinstance(property, Utility):
            owned_utilities = sum(1 for p in game_state.properties[self] if isinstance(p, Utility))
            value_multiplier *= (1.5 if owned_utilities == 1 else 1.0)  # Pair of utilities is valuable

        self.property_values[property] = base_value * value_multiplier
        return self.property_values[property]

    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        budget = game_state.player_balances[self]
        price = property.price
        min_safe_balance = 200  # Keep emergency funds

        if budget < price + min_safe_balance:
            return False

        if property in game_state.properties[self] or property in game_state.mortgaged_properties:
            return False

        property_value = self.calculate_property_value(game_state, property)
        return property_value > price * 1.1  # Buy if strategic value exceeds price by 10%

    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = [p for p in game_state.properties[self] if isinstance(p, Property)]
        grouped_properties = {p.group: [] for p in properties}
        for prop in properties:
            grouped_properties[prop.group].append(prop)

        budget = game_state.player_balances[self]
        min_safe_balance = 300
        suggestions = []

        for group, props in grouped_properties.items():
            if len(props) != len(game_state.board.get_properties_by_group(group)):
                continue

            current_houses = game_state.houses[group][0]
            current_hotels = game_state.hotels[group][0]
            
            if current_hotels == 0 and current_houses == 4:
                # Consider hotel upgrade
                cost = group.hotel_cost()
                if budget >= cost + min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=True)
                    if roi > 0.15:  # 15% ROI threshold
                        suggestions.append(group)
                        budget -= cost
            elif current_houses < 4 and current_hotels == 0:
                # Consider house upgrade
                cost = group.house_cost() * len(props)
                if budget >= cost + min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                    if roi > 0.12:  # 12% ROI threshold
                        suggestions.append(group)
                        budget -= cost

        return suggestions

    def _calculate_upgrade_roi(self, game_state: GameState, group: PropertyGroup, is_hotel: bool) -> float:
        """Calculate return on investment for an upgrade."""
        properties = game_state.board.get_properties_by_group(group)
        current_rent = sum(p.house_rent[game_state.houses[group][0] - 1] if game_state.houses[group][0] > 0 
                         else p.base_rent for p in properties)
        
        if is_hotel:
            new_rent = sum(p.hotel_rent for p in properties)
            cost = group.hotel_cost()
        else:
            new_houses = game_state.houses[group][0] + 1
            new_rent = sum(p.house_rent[new_houses - 1] for p in properties)
            cost = group.house_cost() * len(properties)
            
        return (new_rent - current_rent) / cost

    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        budget = game_state.player_balances[self]
        
        if budget > 200:  # Don't mortgage if we have sufficient funds
            return []
            
        mortgage_candidates = []
        for prop in properties:
            if isinstance(prop, Property):
                if game_state.houses[prop.group][0] > 0 or game_state.hotels[prop.group][0] > 0:
                    continue
                    
            if prop not in game_state.mortgaged_properties:
                strategic_value = self.calculate_property_value(game_state, prop)
                mortgage_value = prop.mortgage
                mortgage_candidates.append((prop, strategic_value / mortgage_value))
                
        # Mortgage properties with lowest strategic value relative to mortgage value
        mortgage_candidates.sort(key=lambda x: x[1])
        return [prop for prop, _ in mortgage_candidates[:2]]  # Mortgage up to 2 properties at a time


    def get_downgrading_suggestions(self, game_state: GameState) -> List[Tile]:
        if game_state.player_balances[self] > 300:
            return []  # Don't downgrade if we have sufficient funds
            
        properties = [p for p in game_state.properties[self] if isinstance(p, Property)]
        grouped_properties = {p.group: [] for p in properties}
        for prop in properties:
            grouped_properties[prop.group].append(prop)
            
        suggestions = []
        for group, props in grouped_properties.items():
            if len(props) != len(game_state.board.get_properties_by_group(group)):
                continue
                
            if game_state.hotels[group][0] > 0:
                roi = self._calculate_upgrade_roi(game_state, group, is_hotel=True)
                if roi < 0.1:  # Low ROI
                    suggestions.append(group)
            elif game_state.houses[group][0] > 0:
                roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                if roi < 0.08:  # Even lower ROI threshold for houses
                    suggestions.append(group)
                    
        return suggestions

    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        budget = game_state.player_balances[self]
        fine = game_state.board.get_jail_fine()
        
        if budget < fine * 2:  # Don't pay if we're low on funds
            return False
            
        # Pay to get out if we have property opportunities or good properties
        valuable_properties = sum(1 for p in game_state.properties[self] 
                                if isinstance(p, Property) and 
                                self.calculate_property_value(game_state, p) > p.price * 1.3)
        return valuable_properties > 2

    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        if game_state.escape_jail_cards[self] == 0:
            return False
            
        # Always use card if we have valuable properties generating rent
        valuable_properties = sum(1 for p in game_state.properties[self] 
                                if isinstance(p, Property) and
                                (game_state.houses[p.group][0] > 0 or
                                 game_state.hotels[p.group][0] > 0))
        return valuable_properties > 0