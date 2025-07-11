from typing import List, Dict, Optional, Set, Tuple
import random
import math
from collections import defaultdict

from game.player import Player
from game.game_state import GameState
from game.game_validation import GameValidation
from game.bankruptcy_request import BankruptcyRequest
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.trade_offer import TradeOffer


class StrategicAgent(Player):
    """
    A strategic Monopoly agent that makes intelligent decisions based on
    configurable parameters and game state analysis.
    """
    

    def __init__(self, name: str, strategy_params: Optional[Dict] = None, can_be_referenced: bool = False):
        """
        Initialize the strategic agent with optional custom parameters.
        
        Args:
            name: The player's name
            strategy_params: Optional dictionary of strategy parameters that will override defaults
        """

        super().__init__(name, can_be_referenced=can_be_referenced)

        self.strategy_params = self._get_default_params()
        # Override with any provided parameters
        if strategy_params:
            self.strategy_params.update(strategy_params)
        
        # Initialize cached property valuations
        self._property_values = {}
        self._property_group_completion = {}
        self._last_valuation_turn = -1
        self._current_turn = 0
            

    def _get_default_params(self) -> Dict:
        """
        Default strategy parameters that define the agent's behavior.
        
        Returns:
            Dictionary of default strategy parameters
        """

        return {
            # Property acquisition
            "min_cash_reserve": 150,  # Minimum cash to keep on hand
            "property_value_multiplier": 1.2,  # Buy if expected value > price * multiplier
            "complete_set_bonus": 0.4,  # Additional value for completing a set
            "railway_value_multiplier": 1.3,  # Value multiplier for railways
            "utility_value_multiplier": 1.1,  # Value multiplier for utilities
            "first_property_eagerness": 0.8,  # Discount for first property in a group (0-1)
            
            # Development strategy
            "min_cash_for_houses": 400,  # Minimum cash before considering house builds
            "house_build_threshold": 0.15,  # Build if cost < portfolio_value * threshold
            "min_houses_before_hotel": 3,  # Minimum houses on all properties before considering hotel
            "hotel_roi_threshold": 1.4,  # ROI threshold for upgrading to hotels
            
            # Cash management
            "mortgage_emergency_threshold": 150,  # Mortgage in emergency if cash < threshold
            "mortgage_property_threshold": 0.7,  # Mortgage properties with ROI < threshold * average
            "unmortgage_threshold": 500,  # Unmortgage if cash > threshold
            "unmortgage_roi_threshold": 1.2,  # Unmortgage if ROI > threshold
            
            # Trading strategy
            "trade_eagerness": 0.5,  # Higher values (0-1) mean more eager to trade
            "trade_profit_threshold": 1.2,  # Only offer trades with expected value gain > threshold
            "trade_monopoly_bonus": 300,  # Extra value for trades that complete monopolies
            
            # Jail strategy
            "jail_stay_threshold": 0.6,  # Stay in jail if board danger > threshold (0-1)
            "use_jail_card_threshold": 0.4,  # Use jail card if board danger < threshold (0-1)
            
            # Bankruptcy strategy
            "bankruptcy_mortgage_first": True,  # If True, mortgage properties before selling houses
            "bankruptcy_property_value_weight": 1.3,  # Weight for property value in bankruptcy decisions
            "bankruptcy_group_completion_weight": 1.5,  # Weight for group completion in bankruptcy
            
            # Property valuation
            "early_game_turns": 15,  # Number of turns considered "early game"
            "orange_red_property_bonus": 1.2,  # Value multiplier for orange/red properties
            "green_blue_property_bonus": 1.1,  # Value multiplier for green/blue properties
            "jail_adjacent_bonus": 1.15,  # Value multiplier for properties after jail
            
            # Risk assessment
            "risk_tolerance": 0.6,  # Higher values (0-1) mean more risk-tolerant
            "danger_zone_weight": 1.2,  # Weight for dangerous zones (7-9 spaces after jail)
        }
    

    def _update_turn_counter(self, game_state: GameState) -> None:
        """
        Update the internal turn counter based on the game state.
        """

        # Approximate turn calculation based on properties owned
        total_properties = sum(len(props) for props in game_state.properties.values())
        self._current_turn = max(self._current_turn, total_properties // len(game_state.players) + 1)
    

    def _calculate_property_values(self, game_state: GameState) -> Dict[Tile, float]:
        """
        Calculate the strategic value of all properties on the board.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary mapping tiles to their calculated values
        """

        # Check if we need to recalculate values (only do once per turn for efficiency)
        self._update_turn_counter(game_state)
        if self._current_turn == self._last_valuation_turn and self._property_values:
            return self._property_values
        
        self._last_valuation_turn = self._current_turn
        values = {}
        
        # Calculate group completion states
        self._property_group_completion = self._analyze_property_groups(game_state)
        
        # Calculate values for all properties
        for tile in game_state.board.tiles:
            if isinstance(tile, Property):
                values[tile] = self._calculate_property_value(game_state, tile)
            elif isinstance(tile, Railway):
                values[tile] = self._calculate_railway_value(game_state, tile)
            elif isinstance(tile, Utility):
                values[tile] = self._calculate_utility_value(game_state, tile)
        
        self._property_values = values
        return values
    

    def _analyze_property_groups(self, game_state: GameState) -> Dict[PropertyGroup, Dict]:
        """
        Analyze the completion status of all property groups.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary mapping property groups to their completion info
        """

        result = {}
        
        for group in PropertyGroup:
            group_properties = game_state.board.get_properties_by_group(group)
            total_props = len(group_properties)
            
            # Count how many properties in this group this agent owns
            self_owned = sum(1 for prop in group_properties if prop in game_state.properties[self])
            
            # Count how many properties in this group are owned by opponents
            opponent_owned = sum(1 for prop in group_properties 
                                if prop in game_state.is_owned and prop not in game_state.properties[self])
            
            # Count how many properties are still available to purchase
            available = total_props - self_owned - opponent_owned
            
            # Calculate completion percentage for this agent
            completion_pct = self_owned / total_props
            
            # Determine if monopoly is still achievable
            can_complete = (self_owned + available) == total_props
            
            # How many more properties needed to complete the set
            remaining_needed = total_props - self_owned
            
            result[group] = {
                "total": total_props,
                "self_owned": self_owned,
                "opponent_owned": opponent_owned,
                "available": available,
                "completion_pct": completion_pct,
                "can_complete": can_complete,
                "remaining_needed": remaining_needed,
                "is_monopoly": self_owned == total_props
            }
            
        return result
    

    def _calculate_property_value(self, game_state: GameState, property: Property) -> float:
        """
        Calculate the strategic value of a property.
        
        Args:
            game_state: Current game state
            property: The property to evaluate
            
        Returns:
            Calculated property value
        """
        # Base value starts with the property price
        base_value = property.price
        
        # Value based on rent return
        rent_value = property.full_group_rent * 10  # Approximate 10 rent payments
        
        # Add house/hotel potential
        development_value = sum(property.house_rent) / 4 + property.hotel_rent / 5
        
        # Group completion value
        group_info = self._property_group_completion[property.group]
        
        # Apply multiplier based on how close we are to completing the monopoly
        completion_multiplier = 1.0
        if group_info["is_monopoly"]:
            completion_multiplier = 1.0 + self.strategy_params["complete_set_bonus"]
        elif group_info["can_complete"]:
            # Higher value if we can still complete this set
            completion_multiplier = 1.0 + (self.strategy_params["complete_set_bonus"] * 
                                          group_info["completion_pct"])
        
        # Value location-based properties
        location_multiplier = 1.0
        
        # Orange and red properties (high chance of being landed on from jail)
        if property.group in [PropertyGroup.ORANGE, PropertyGroup.RED]:
            location_multiplier *= self.strategy_params["orange_red_property_bonus"]
        
        # Green and blue properties (high rents)
        elif property.group in [PropertyGroup.GREEN, PropertyGroup.BLUE]:
            location_multiplier *= self.strategy_params["green_blue_property_bonus"]
        
        # Properties 6-9 spaces after jail (high frequency)
        jail_position = game_state.board.get_jail_id()
        distance_from_jail = (property.id - jail_position) % 40
        if 6 <= distance_from_jail <= 9:
            location_multiplier *= self.strategy_params["jail_adjacent_bonus"]
        
        # First property in a group discount/bonus
        if group_info["self_owned"] == 0:
            early_game_factor = max(0, self.strategy_params["early_game_turns"] - self._current_turn) / self.strategy_params["early_game_turns"]
            first_property_factor = self.strategy_params["first_property_eagerness"] * (1 + early_game_factor)
            completion_multiplier *= first_property_factor
        
        # Calculate final value
        value = (base_value + rent_value + development_value) * completion_multiplier * location_multiplier
        
        return value
    
    
    def _calculate_railway_value(self, game_state: GameState, railway: Railway) -> float:
        """
        Calculate the strategic value of a railway.
        
        Args:
            game_state: Current game state
            railway: The railway to evaluate
            
        Returns:
            Calculated railway value
        """

        base_value = railway.price
        
        # Count how many railways we already own
        owned_railways = sum(1 for r in game_state.board.get_railways() if r in game_state.properties[self])
        
        # Calculate expected rent based on how many we already own
        # The more we have, the more valuable each additional one becomes
        if owned_railways == 0:
            rent_value = railway.rent[0] * 10  # Approximate 10 rent payments
        elif owned_railways == 1:
            rent_value = railway.rent[1] * 10
        elif owned_railways == 2:
            rent_value = railway.rent[2] * 10
        else:  # 3 railways owned
            rent_value = railway.rent[3] * 10
        
        # Apply railway multiplier from strategy params
        value = (base_value + rent_value) * self.strategy_params["railway_value_multiplier"]
        
        return value
    
    
    def _calculate_utility_value(self, game_state: GameState, utility: Utility) -> float:
        """
        Calculate the strategic value of a utility.
        
        Args:
            game_state: Current game state
            utility: The utility to evaluate
            
        Returns:
            Calculated utility value
        """

        base_value = utility.price
        
        # Count how many utilities we already own
        owned_utilities = sum(1 for u in game_state.board.get_utilities() if u in game_state.properties[self])
        
        # Calculate expected rent (approximately)
        # Average dice roll is 7
        if owned_utilities == 0:
            rent_value = 4 * 7 * 8  # Approximate 8 rent payments
        else:  # 1 utility owned
            rent_value = 10 * 7 * 8
        
        # Apply utility multiplier from strategy params
        value = (base_value + rent_value) * self.strategy_params["utility_value_multiplier"]
        
        return value
    
    
    def _calculate_property_roi(self, game_state: GameState, property: Property) -> float:
        """
        Calculate return on investment for a property.
        
        Args:
            game_state: Current game state
            property: The property to evaluate
            
        Returns:
            ROI value (higher is better)
        """
        if property.price == 0:  # Avoid division by zero
            return 0
            
        property_value = self._calculate_property_value(game_state, property)
        return property_value / property.price
    

    def _calculate_development_roi(self, game_state: GameState, group: PropertyGroup) -> float:
        """
        Calculate the ROI for developing houses/hotels on a property group.
        
        Args:
            game_state: Current game state
            group: The property group to evaluate
            
        Returns:
            ROI value (higher is better)
        """
        properties = game_state.board.get_properties_by_group(group)
        
        # Check if we own all properties in the group
        if not all(prop in game_state.properties[self] for prop in properties):
            return 0
            
        # Check if any properties are mortgaged
        if any(prop in game_state.mortgaged_properties for prop in properties):
            return 0
            
        # Get current houses and determine next development step
        houses_count = game_state.houses[group][0]
        hotels_count = game_state.hotels[group][0]
        
        # If we already have hotels, no more development possible
        if hotels_count > 0:
            return 0
            
        # Calculate cost of next development step
        if houses_count < 4:
            # Build next house
            cost = group.house_cost() * len(properties)
            
            # Calculate increase in rent from adding another house
            rent_before = 0
            rent_after = 0
            
            for prop in properties:
                if houses_count == 0:
                    rent_before += prop.full_group_rent
                    rent_after += prop.house_rent[0]
                else:
                    rent_before += prop.house_rent[houses_count - 1]
                    rent_after += prop.house_rent[houses_count]
            
            rent_increase = rent_after - rent_before
            
            # Calculate ROI
            return rent_increase / cost if cost > 0 else 0
            
        else:  # houses_count == 4, consider hotel
            cost = group.hotel_cost() * len(properties)
            
            # Calculate increase in rent from adding a hotel
            rent_before = 0
            rent_after = 0
            
            for prop in properties:
                rent_before += prop.house_rent[3]  # 4th house rent
                rent_after += prop.hotel_rent
                
            rent_increase = rent_after - rent_before
            
            # Calculate ROI
            return rent_increase / cost if cost > 0 else 0
    

    def _assess_board_danger(self, game_state: GameState) -> float:
        """
        Assess how dangerous the board currently is for this player.
        
        Args:
            game_state: Current game state
            
        Returns:
            Danger score between 0-1 (higher means more dangerous)
        """
        current_position = game_state.player_positions[self]
        
        danger_score = 0
        max_danger = 0
        
        # Check all possible landing spots in the next move (2-12 spaces ahead)
        for steps in range(2, 13):
            # Calculate probability of rolling this number with two dice
            if steps <= 7:
                probability = (steps - 1) / 36
            else:
                probability = (13 - steps) / 36
                
            # Calculate the position after moving
            next_position = (current_position + steps) % 40
            tile = game_state.board.tiles[next_position]
            
            tile_danger = 0
            
            # Assess danger based on tile type
            if isinstance(tile, Property) and tile in game_state.is_owned and tile not in game_state.properties[self]:
                # Property owned by opponent
                for player in game_state.players:
                    if player != self and tile in game_state.properties[player]:
                        # Calculate approximate rent
                        if tile.group in game_state.houses and game_state.houses[tile.group][0] > 0:
                            # Has houses
                            houses = game_state.houses[tile.group][0]
                            rent = tile.house_rent[houses - 1]
                        elif tile.group in game_state.hotels and game_state.hotels[tile.group][0] > 0:
                            # Has hotel
                            rent = tile.hotel_rent
                        else:
                            # No houses/hotels
                            group_properties = game_state.board.get_properties_by_group(tile.group)
                            if all(p in game_state.properties[player] for p in group_properties):
                                rent = tile.full_group_rent
                            else:
                                rent = tile.base_rent
                                
                        # Calculate danger based on rent relative to our cash
                        cash = game_state.player_balances[self]
                        tile_danger = min(1.0, rent / (cash + 1))  # Avoid division by zero
                        break
                        
            elif isinstance(tile, Railway) and tile in game_state.is_owned and tile not in game_state.properties[self]:
                # Railway owned by opponent
                for player in game_state.players:
                    if player != self and tile in game_state.properties[player]:
                        # Count railways owned by opponent
                        railway_count = sum(1 for r in game_state.board.get_railways() if r in game_state.properties[player])
                        rent = tile.rent[railway_count - 1]
                        
                        # Calculate danger
                        cash = game_state.player_balances[self]
                        tile_danger = min(1.0, rent / (cash + 1))
                        break
                        
            elif isinstance(tile, Utility) and tile in game_state.is_owned and tile not in game_state.properties[self]:
                # Utility owned by opponent
                for player in game_state.players:
                    if player != self and tile in game_state.properties[player]:
                        # Count utilities owned by opponent
                        utility_count = sum(1 for u in game_state.board.get_utilities() if u in game_state.properties[player])
                        # Approximate average dice roll of 7
                        rent = 4 * 7 if utility_count == 1 else 10 * 7
                        
                        # Calculate danger
                        cash = game_state.player_balances[self]
                        tile_danger = min(1.0, rent / (cash + 1))
                        break
            
            # Apply the danger zone weight for spaces 7-9 after jail (high frequency)
            jail_position = game_state.board.get_jail_id()
            distance_from_jail = (next_position - jail_position) % 40
            if 6 <= distance_from_jail <= 9:
                tile_danger *= self.strategy_params["danger_zone_weight"]
                
            # Weighted danger by probability of landing
            danger_score += tile_danger * probability
            max_danger += probability
        
        # Normalize danger score
        if max_danger > 0:
            danger_score /= max_danger
            
        return danger_score
    

    def _can_afford(self, game_state: GameState, cost: int) -> bool:
        """
        Check if the agent can afford a cost while maintaining minimum cash reserve.
        
        Args:
            game_state: Current game state
            cost: The cost to check
            
        Returns:
            True if the agent can afford the cost, False otherwise
        """

        cash = game_state.player_balances[self]
        return cash - cost >= self.strategy_params["min_cash_reserve"]
    

    def _emergency_can_afford(self, game_state: GameState, cost: int) -> bool:
        """
        Check if the agent can afford a cost in an emergency situation.
        
        Args:
            game_state: Current game state
            cost: The cost to check
            
        Returns:
            True if the agent can afford the cost, False otherwise
        """
        cash = game_state.player_balances[self]
        return cash >= cost
    
    
    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        # Validate property purchase
        if error := GameValidation.validate_buy_property(game_state, self, property):
            return False
            
        # Skip if not a purchasable property type
        if not (isinstance(property, Property) or isinstance(property, Railway) or isinstance(property, Utility)):
            return False
            
        # Calculate property value
        property_values = self._calculate_property_values(game_state)
        if property not in property_values:
            return False
            
        property_value = property_values[property]
        
        # Check if the property's value exceeds the price by the threshold multiplier
        value_threshold = property.price * self.strategy_params["property_value_multiplier"]
        is_good_value = property_value >= value_threshold
        
        # Check if we can afford it while maintaining minimum cash reserve
        can_afford = self._can_afford(game_state, property.price)
        
        # Early game or late game assessment
        is_early_game = self._current_turn <= self.strategy_params["early_game_turns"]
        
        # In early game, be more aggressive with purchases
        if is_early_game:
            # We're less concerned about value threshold in early game
            return can_afford
            
        # In emergency situations, use a more aggressive strategy
        cash = game_state.player_balances[self]
        if cash > self.strategy_params["min_cash_reserve"] * 3:
            # We have plenty of cash, buy if it's a good value
            return is_good_value and can_afford
            
        # Otherwise, be more selective
        return is_good_value and can_afford and property_value > property.price * 1.3
    

    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        suggestions = []
        cash = game_state.player_balances[self]
        
        # Don't consider development if cash is below threshold
        if cash < self.strategy_params["min_cash_for_houses"]:
            return []
            
        # Calculate ROI for each property group
        roi_by_group = {}
        for group in PropertyGroup:
            roi = self._calculate_development_roi(game_state, group)
            if roi > 0:
                roi_by_group[group] = roi
                
        # No valid groups for development
        if not roi_by_group:
            return []
            
        # Sort groups by ROI (highest first)
        sorted_groups = sorted(roi_by_group.keys(), key=lambda g: roi_by_group[g], reverse=True)
        
        remaining_cash = cash
        
        # Consider each group in order of ROI
        for group in sorted_groups:
            houses = game_state.houses[group][0]
            hotels = game_state.hotels[group][0]
            properties = game_state.board.get_properties_by_group(group)
            
            # Determine cost of next development step
            if hotels > 0:
                # Already have hotel(s), skip
                continue
                
            if houses < 4:
                # Next step is to add a house
                cost = group.house_cost() * len(properties)
                
                # Check if we can afford it and maintain minimum reserve
                if remaining_cash - cost >= self.strategy_params["min_cash_reserve"]:
                    # Validate development
                    if not GameValidation.validate_place_house(game_state, self, group):
                        suggestions.append(group)
                        remaining_cash -= cost
            else:
                # Next step is to add a hotel
                cost = group.hotel_cost() * len(properties)
                
                # Check if we can afford it and maintain minimum reserve
                if remaining_cash - cost >= self.strategy_params["min_cash_reserve"]:
                    # Check ROI threshold for hotel upgrades
                    if roi_by_group[group] >= self.strategy_params["hotel_roi_threshold"]:
                        # Validate development
                        if not GameValidation.validate_place_hotel(game_state, self, group):
                            suggestions.append(group)
                            remaining_cash -= cost
                            
        return suggestions
    
    
    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        cash = game_state.player_balances[self]
        emergency = cash < self.strategy_params["mortgage_emergency_threshold"]
        suggestions = []
        
        # Don't mortgage unless in emergency or cash is very low
        if not emergency and cash > self.strategy_params["min_cash_reserve"]:
            return []
            
        # Get all properties we own that aren't mortgaged
        properties = [p for p in game_state.properties[self] if p not in game_state.mortgaged_properties]
        
        # Filter out properties with houses/hotels
        properties = [p for p in properties if not (
            isinstance(p, Property) and 
            p.group in game_state.houses and
            (game_state.houses[p.group][0] > 0 or 
             (p.group in game_state.hotels and game_state.hotels[p.group][0] > 0))
        )]
        
        # Calculate ROI for each property
        property_roi = {}
        for prop in properties:
            if isinstance(prop, Property):
                roi = self._calculate_property_roi(game_state, prop)
                # Check if this would break a monopoly
                group_info = self._property_group_completion[prop.group]
                if group_info["is_monopoly"]:
                    # Penalize mortgaging monopoly properties
                    roi *= 1.5
                property_roi[prop] = roi
            elif isinstance(prop, Railway):
                # Calculate railway ROI based on how many we own
                owned_railways = sum(1 for r in game_state.board.get_railways() if r in game_state.properties[self])
                property_roi[prop] = owned_railways * 0.25 + 0.5  # Simple scaling
            elif isinstance(prop, Utility):
                # Calculate utility ROI based on how many we own
                owned_utilities = sum(1 for u in game_state.board.get_utilities() if u in game_state.properties[self])
                property_roi[prop] = owned_utilities * 0.5 + 0.5  # Simple scaling
                
        # If no valid properties to mortgage
        if not property_roi:
            return []
            
        # Sort properties by ROI (lowest first, as these are best to mortgage)
        sorted_properties = sorted(property_roi.keys(), key=lambda p: property_roi[p])
        
        # In emergency, mortgage more aggressively
        if emergency:
            for prop in sorted_properties:
                # Validate mortgaging
                if not GameValidation.validate_mortgage_property(game_state, self, prop):
                    suggestions.append(prop)
                    cash += prop.mortgage
                    # Stop once we have enough cash
                    if cash >= self.strategy_params["min_cash_reserve"]:
                        break
        else:
            # Only mortgage properties with low ROI relative to average
            avg_roi = sum(property_roi.values()) / len(property_roi) if property_roi else 0
            threshold = avg_roi * self.strategy_params["mortgage_property_threshold"]
            
            for prop in sorted_properties:
                if property_roi[prop] <= threshold:
                    # Validate mortgaging
                    if not GameValidation.validate_mortgage_property(game_state, self, prop):
                        suggestions.append(prop)
                        cash += prop.mortgage
                        # Stop once we have enough cash
                        if cash >= self.strategy_params["min_cash_reserve"]:
                            break
                            
        return suggestions
    
    
    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        cash = game_state.player_balances[self]
        
        # Don't unmortgage if cash is below threshold
        if cash < self.strategy_params["unmortgage_threshold"]:
            return []
            
        suggestions = []
        
        # Get all properties we own that are mortgaged
        mortgaged_properties = [p for p in game_state.properties[self] if p in game_state.mortgaged_properties]
        
        # Calculate ROI for each property
        property_values = self._calculate_property_values(game_state)
        property_roi = {}
        
        for prop in mortgaged_properties:
            if prop in property_values:
                value = property_values[prop]
                # Avoid division by zero
                roi = value / prop.buyback_price if prop.buyback_price > 0 else 0
                
                # Boost ROI for properties that would complete a monopoly
                if isinstance(prop, Property):
                    group_info = self._property_group_completion[prop.group]
                    if group_info["self_owned"] == group_info["total"] - 1:
                        roi *= 1.5
                        
                property_roi[prop] = roi
                
        # If no valid properties to unmortgage
        if not property_roi:
            return []
            
        # Sort properties by ROI (highest first, as these are best to unmortgage)
        sorted_properties = sorted(property_roi.keys(), key=lambda p: property_roi[p], reverse=True)
        
        remaining_cash = cash
        
        # Consider each property for unmortgaging
        for prop in sorted_properties:
            # Check if ROI is above threshold
            if property_roi[prop] >= self.strategy_params["unmortgage_roi_threshold"]:
                # Check if we can afford it and maintain minimum reserve
                if remaining_cash - prop.buyback_price >= self.strategy_params["min_cash_reserve"]:
                    # Validate unmortgaging
                    if not GameValidation.validate_unmortgage_property(game_state, self, prop):
                        suggestions.append(prop)
                        remaining_cash -= prop.buyback_price
                        
        return suggestions
    
    
    def get_downgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        cash = game_state.player_balances[self]
        emergency = cash < self.strategy_params["mortgage_emergency_threshold"]
        
        # Don't downgrade unless in emergency or cash is very low
        if not emergency and cash > self.strategy_params["min_cash_reserve"]:
            return []
            
        suggestions = []
        
        # Calculate ROI for each property group with houses/hotels
        group_roi = {}
        for group in PropertyGroup:
            # Skip if group doesn't exist in houses or hotels dictionaries
            if group not in game_state.houses or group not in game_state.hotels:
                continue
                
            houses = game_state.houses[group][0]
            hotels = game_state.hotels[group][0]
            
            # Skip if no development
            if houses == 0 and hotels == 0:
                continue
                
            # Skip if not owned by us
            house_owner = game_state.houses[group][1]
            hotel_owner = game_state.hotels[group][1]
            if house_owner != self and hotel_owner != self:
                continue
                
            # Calculate approximate ROI of current development
            roi = self._calculate_development_roi(game_state, group)
            group_roi[group] = roi
            
        # If no groups to downgrade
        if not group_roi:
            return []
            
        # Sort groups by ROI (lowest first, as these are best to downgrade)
        sorted_groups = sorted(group_roi.keys(), key=lambda g: group_roi[g])
        
        # In emergency, downgrade more aggressively
        if emergency:
            for group in sorted_groups:
                hotels = game_state.hotels[group][0]
                houses = game_state.houses[group][0]
                
                # Validate downgrading
                if hotels > 0 and game_state.hotels[group][1] == self:
                    if not GameValidation.validate_sell_hotel(game_state, self, group):
                        suggestions.append(group)
                        # Stop once we have enough cash
                        if cash + group.hotel_cost() // 2 >= self.strategy_params["min_cash_reserve"]:
                            break
                elif houses > 0 and game_state.houses[group][1] == self:
                    if not GameValidation.validate_sell_house(game_state, self, group):
                        suggestions.append(group)
                        # Stop once we have enough cash
                        if cash + group.house_cost() // 2 >= self.strategy_params["min_cash_reserve"]:
                            break
        else:
            # Only downgrade groups with low ROI relative to average
            if group_roi:
                avg_roi = sum(group_roi.values()) / len(group_roi)
                threshold = avg_roi * self.strategy_params["mortgage_property_threshold"]
                
                for group in sorted_groups:
                    if group_roi[group] <= threshold:
                        hotels = game_state.hotels[group][0]
                        houses = game_state.houses[group][0]
                        
                        # Validate downgrading
                        if hotels > 0 and game_state.hotels[group][1] == self:
                            if not GameValidation.validate_sell_hotel(game_state, self, group):
                                suggestions.append(group)
                                # Stop once we have enough cash
                                if cash + group.hotel_cost() // 2 >= self.strategy_params["min_cash_reserve"]:
                                    break
                        elif houses > 0 and game_state.houses[group][1] == self:
                            if not GameValidation.validate_sell_house(game_state, self, group):
                                suggestions.append(group)
                                # Stop once we have enough cash
                                if cash + group.house_cost() // 2 >= self.strategy_params["min_cash_reserve"]:
                                    break
                                    
        return suggestions
    
    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        # Validate if player is in jail
        if not game_state.in_jail.get(self, False):
            return False
            
        # Assess current board danger
        danger_level = self._assess_board_danger(game_state)
        
        # Check if we can afford the fine
        jail_fine = game_state.board.get_jail_fine()
        can_afford = self._emergency_can_afford(game_state, jail_fine)
        
        if not can_afford:
            return False
            
        # Decision based on danger level
        if danger_level >= self.strategy_params["jail_stay_threshold"]:
            # Board is dangerous, stay in jail
            return False
        else:
            # Board is relatively safe, get out of jail
            cash = game_state.player_balances[self]
            
            # If cash is tight, stay in jail
            if cash < self.strategy_params["min_cash_reserve"] * 1.5:
                return False
                
            # Otherwise, pay to get out
            return True
        
    
    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        # Validate if player is in jail
        if not game_state.in_jail.get(self, False):
            return False
            
        # Check if we have a card
        if game_state.escape_jail_cards.get(self, 0) == 0:
            return False
            
        # Assess current board danger
        danger_level = self._assess_board_danger(game_state)
        
        # Decision based on danger level
        if danger_level >= self.strategy_params["use_jail_card_threshold"]:
            # Board is dangerous, stay in jail
            return False
        else:
            # Board is relatively safe, use card to get out
            return True
        

    def _calculate_trade_value(self, game_state: GameState, properties: List[Tile], money: int, jail_cards: int) -> float:
        """
        Calculate the total strategic value of a trade package.
        
        Args:
            game_state: Current game state
            properties: List of properties in the trade
            money: Money amount in the trade
            jail_cards: Number of jail cards in the trade
            
        Returns:
            Total strategic value
        """
        total_value = money  # Start with cash value
        
        # Add jail card value (strategic worth)
        total_value += jail_cards * 75  # Each card worth ~$75 strategically
        
        # Calculate property values using existing method
        property_values = self._calculate_property_values(game_state)
        
        for prop in properties:
            if prop in property_values:
                base_value = property_values[prop]
                
                # Add monopoly completion bonus
                if isinstance(prop, Property):
                    group_info = self._property_group_completion[prop.group]
                    
                    # If this property would complete our monopoly
                    if group_info["can_complete"] and group_info["remaining_needed"] == 1:
                        base_value *= 2.5  # Massive bonus for monopoly completion
                    
                    # If this property would break opponent's monopoly
                    # (We need to check who owns it currently)
                    elif group_info["self_owned"] == 0:  # We don't own any in this group
                        # Check if opponent has monopoly
                        for player in game_state.players:
                            if player != self:
                                opponent_group_props = game_state.board.get_properties_by_group(prop.group)
                                if all(p in game_state.properties[player] for p in opponent_group_props):
                                    base_value *= 1.8  # High value for breaking monopoly
                                    break
                
                total_value += base_value
        
        return total_value


    def _calculate_monopoly_impact(self, game_state: GameState, properties_gained: List[Tile], 
                                properties_lost: List[Tile]) -> Dict[str, float]:
        """
        Calculate the monopoly impact of a potential trade.
        
        Args:
            game_state: Current game state
            properties_gained: Properties we would gain
            properties_lost: Properties we would lose
            
        Returns:
            Dictionary with monopoly impact metrics
        """
        impact = {
            'monopolies_completed': 0,
            'monopolies_broken': 0,
            'monopoly_progress': 0.0,
            'strategic_value': 0.0
        }
        
        # Check monopolies we would complete
        for prop in properties_gained:
            if isinstance(prop, Property):
                group_properties = game_state.board.get_properties_by_group(prop.group)
                current_owned = sum(1 for p in group_properties if p in game_state.properties[self])
                
                # If gaining this property completes monopoly
                if current_owned == len(group_properties) - 1:
                    impact['monopolies_completed'] += 1
                    impact['strategic_value'] += 500  # High strategic value
                else:
                    # Progress toward monopoly
                    progress = (current_owned + 1) / len(group_properties)
                    impact['monopoly_progress'] += progress
                    impact['strategic_value'] += progress * 200
        
        # Check monopolies we would break by losing properties
        for prop in properties_lost:
            if isinstance(prop, Property):
                group_properties = game_state.board.get_properties_by_group(prop.group)
                current_owned = sum(1 for p in group_properties if p in game_state.properties[self])
                
                # If losing this property breaks our monopoly
                if current_owned == len(group_properties):
                    impact['monopolies_broken'] += 1
                    impact['strategic_value'] -= 600  # Severe penalty for breaking monopoly
        
        return impact


    def _evaluate_cash_impact(self, game_state: GameState, cash_change: int) -> Dict[str, float]:
        """
        Evaluate the impact of cash changes on our position.
        
        Args:
            game_state: Current game state
            cash_change: Net cash change (positive = gaining, negative = losing)
            
        Returns:
            Dictionary with cash impact metrics
        """
        current_cash = game_state.player_balances[self]
        new_cash = current_cash + cash_change
        
        impact = {
            'liquidity_ratio': new_cash / max(game_state.get_player_net_worth(self), 1),
            'safety_margin': new_cash - self.strategy_params["min_cash_reserve"],
            'cash_flexibility': 0.0,
            'risk_level': 0.0
        }
        
        # Calculate cash flexibility (ability to make future moves)
        if new_cash > 800:
            impact['cash_flexibility'] = 1.0  # High flexibility
        elif new_cash > 500:
            impact['cash_flexibility'] = 0.7  # Good flexibility
        elif new_cash > 300:
            impact['cash_flexibility'] = 0.4  # Limited flexibility
        else:
            impact['cash_flexibility'] = 0.1  # Very limited
        
        # Calculate risk level
        if new_cash < 100:
            impact['risk_level'] = 1.0  # Very high risk
        elif new_cash < 200:
            impact['risk_level'] = 0.8  # High risk
        elif new_cash < 400:
            impact['risk_level'] = 0.5  # Moderate risk
        else:
            impact['risk_level'] = 0.2  # Low risk
        
        return impact


    def should_accept_trade_offer(self, game_state: GameState, trade_offer: TradeOffer) -> bool:
        # Validate trade offer
        if error := GameValidation.validate_trade_offer(game_state, trade_offer):
            return False
        
        # Calculate what we're gaining and losing
        properties_gained = trade_offer.properties_offered or []
        properties_lost = trade_offer.properties_requested or []
        money_gained = trade_offer.money_offered or 0
        money_lost = trade_offer.money_requested or 0
        jail_cards_gained = trade_offer.jail_cards_offered or 0
        jail_cards_lost = trade_offer.jail_cards_requested or 0
        
        net_cash_change = money_gained - money_lost
        current_cash = game_state.player_balances[self]
        
        # CRITICAL FILTERS - Auto-reject trades that are obviously bad
        
        # 1. Don't accept trades that would leave us with dangerously low cash
        if current_cash + net_cash_change < self.strategy_params["min_cash_reserve"]:
            return False
        
        # 2. Don't accept trades where money offered exceeds reasonable property value
        total_property_value = sum(prop.price for prop in properties_gained)
        if money_gained > total_property_value * 1.5:  # More than 1.5x property value is suspicious
            return False
        
        # 3. Don't accept trades where we pay more than 2x property value
        if money_lost > sum(prop.price for prop in properties_lost) * 2.0:
            return False
        
        # 4. Don't accept trades that would consume more than 70% of our cash
        if money_lost > current_cash * 0.7:
            return False
        
        # 5. Don't break our own monopolies unless compensation is extraordinary
        for prop in properties_lost:
            if isinstance(prop, Property):
                group_properties = game_state.board.get_properties_by_group(prop.group)
                if all(p in game_state.properties[self] for p in group_properties):
                    # We're breaking our monopoly - need 3x property value in compensation
                    compensation_needed = prop.price * 3
                    total_compensation = self._calculate_trade_value(game_state, properties_gained, 
                                                                money_gained, jail_cards_gained)
                    if total_compensation < compensation_needed:
                        return False
        
        # COMPREHENSIVE STRATEGIC ANALYSIS
        
        # Calculate monopoly impacts
        monopoly_impact = self._calculate_monopoly_impact(game_state, properties_gained, properties_lost)
        
        # Calculate cash impact
        cash_impact = self._evaluate_cash_impact(game_state, net_cash_change)
        
        # Calculate trade values
        value_gained = self._calculate_trade_value(game_state, properties_gained, money_gained, jail_cards_gained)
        value_lost = self._calculate_trade_value(game_state, properties_lost, money_lost, jail_cards_lost)
        
        # DECISION MATRIX - Weight different factors
        
        decision_score = 0.0
        
        # 1. Raw value comparison (30% weight)
        value_ratio = value_gained / max(value_lost, 1)
        if value_ratio > 1.3:
            decision_score += 0.3  # Great value
        elif value_ratio > 1.1:
            decision_score += 0.15  # Good value
        elif value_ratio > 0.9:
            decision_score += 0.0  # Fair value
        else:
            decision_score -= 0.2  # Poor value
        
        # 2. Monopoly impact (40% weight)
        if monopoly_impact['monopolies_completed'] > 0:
            decision_score += 0.4 * monopoly_impact['monopolies_completed']  # Huge bonus
        
        if monopoly_impact['monopolies_broken'] > 0:
            decision_score -= 0.3 * monopoly_impact['monopolies_broken']  # Major penalty
        
        decision_score += monopoly_impact['monopoly_progress'] * 0.2  # Progress bonus
        
        # 3. Cash management (20% weight)
        if cash_impact['risk_level'] > 0.7:
            decision_score -= 0.15  # High cash risk penalty
        elif cash_impact['risk_level'] < 0.3:
            decision_score += 0.1  # Low risk bonus
        
        if cash_impact['cash_flexibility'] > 0.8:
            decision_score += 0.1  # High flexibility bonus
        elif cash_impact['cash_flexibility'] < 0.3:
            decision_score -= 0.1  # Low flexibility penalty
        
        # 4. Strategic position (10% weight)
        # Consider board danger and opponent analysis
        board_danger = self._assess_board_danger(game_state)
        if board_danger > 0.7 and net_cash_change < 0:
            decision_score -= 0.1  # Don't spend cash when board is dangerous
        
        # Consider trade eagerness parameter
        eagerness_adjustment = (self.strategy_params["trade_eagerness"] - 0.5) * 0.1
        decision_score += eagerness_adjustment
        
        # FINAL DECISION
        # Also consider random factor for variety (small influence)
        randomness = (random.random() - 0.5) * 0.05
        final_score = decision_score + randomness
        
        return final_score > 0.1  # Require positive score with buffer


    def get_trade_offers(self, game_state: GameState) -> List[TradeOffer]:
        trade_offers = []
        current_cash = game_state.player_balances[self]
        
        # Don't make trades if we're in a precarious financial situation
        if current_cash < self.strategy_params["min_cash_reserve"] * 1.5:
            return []
        
        property_values = self._calculate_property_values(game_state)
        
        # For each opponent, analyze potential trades
        for opponent in game_state.players:
            if opponent == self:
                continue
            
            opponent_cash = game_state.player_balances[opponent]
            if opponent_cash < 100:  # Skip broke opponents
                continue
            
            # STRATEGY 1: Monopoly Completion Trades
            monopoly_trades = self._generate_monopoly_completion_trades(
                game_state, opponent, property_values, opponent_cash
            )
            trade_offers.extend(monopoly_trades)
            
            # STRATEGY 2: Monopoly Breaking Trades
            breaking_trades = self._generate_monopoly_breaking_trades(
                game_state, opponent, property_values, opponent_cash
            )
            trade_offers.extend(breaking_trades)
            
            # STRATEGY 3: Value Optimization Trades
            value_trades = self._generate_value_optimization_trades(
                game_state, opponent, property_values, opponent_cash
            )
            trade_offers.extend(value_trades)
            
            # STRATEGY 4: Cash Generation Trades
            if current_cash < 600:  # We need cash
                cash_trades = self._generate_cash_generation_trades(
                    game_state, opponent, property_values, opponent_cash
                )
                trade_offers.extend(cash_trades)
        
        # Sort trades by strategic value and return top ones
        if trade_offers:
            scored_trades = []
            for offer in trade_offers:
                score = self._score_trade_offer(game_state, offer)
                scored_trades.append((offer, score))
            
            # Sort by score (highest first)
            scored_trades.sort(key=lambda x: x[1], reverse=True)
            
            # Return top 3 trades to avoid overwhelming opponents
            return [trade for trade, score in scored_trades[:3] if score > 0]
        
        return []


    def _generate_monopoly_completion_trades(self, game_state: GameState, opponent, 
                                        property_values: Dict, opponent_cash: int) -> List[TradeOffer]:
        """Generate trades focused on completing monopolies."""
        trades = []
        
        for group, info in self._property_group_completion.items():
            if info["can_complete"] and info["remaining_needed"] == 1:
                # Find the missing property
                group_properties = game_state.board.get_properties_by_group(group)
                missing_properties = [p for p in group_properties 
                                    if p not in game_state.properties[self]]
                
                for missing_prop in missing_properties:
                    if missing_prop in game_state.properties[opponent]:
                        # Try to acquire this property
                        trade = self._create_monopoly_completion_trade(
                            game_state, opponent, missing_prop, property_values, opponent_cash
                        )
                        if trade:
                            trades.append(trade)
        
        return trades


    def _generate_monopoly_breaking_trades(self, game_state: GameState, opponent,
                                        property_values: Dict, opponent_cash: int) -> List[TradeOffer]:
        """Generate trades focused on breaking opponent monopolies."""
        trades = []
        
        # Check opponent's monopolies
        for group in PropertyGroup:
            group_properties = game_state.board.get_properties_by_group(group)
            if all(p in game_state.properties[opponent] for p in group_properties):
                # Opponent has monopoly - try to break it by acquiring one property
                for prop in group_properties:
                    if prop.price <= self.strategy_params["min_cash_reserve"] * 2:
                        # Try to buy this property to break monopoly
                        trade = self._create_monopoly_breaking_trade(
                            game_state, opponent, prop, property_values, opponent_cash
                        )
                        if trade:
                            trades.append(trade)
                            break  # Only need to break one property per monopoly
        
        return trades


    def _generate_value_optimization_trades(self, game_state: GameState, opponent,
                                        property_values: Dict, opponent_cash: int) -> List[TradeOffer]:
        """Generate trades focused on optimizing property values."""
        trades = []
        
        # Find undervalued properties we can acquire
        for prop in game_state.properties[opponent]:
            if isinstance(prop, (Property, Railway, Utility)):
                # Skip if property is part of opponent's monopoly
                if isinstance(prop, Property):
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if all(p in game_state.properties[opponent] for p in group_properties):
                        continue  # Don't try to break monopolies here (handled separately)
                
                our_value = property_values.get(prop, prop.price)
                fair_price = prop.price * 1.1  # 10% premium for negotiation
                
                if our_value > fair_price:
                    # This property is valuable to us
                    trade = self._create_value_trade(
                        game_state, opponent, prop, property_values, opponent_cash
                    )
                    if trade:
                        trades.append(trade)
        
        return trades


    def _generate_cash_generation_trades(self, game_state: GameState, opponent,
                                    property_values: Dict, opponent_cash: int) -> List[TradeOffer]:
        """Generate trades focused on raising cash."""
        trades = []
        
        # Find properties we can sell for good value
        for prop in game_state.properties[self]:
            if isinstance(prop, (Property, Railway, Utility)):
                # Don't sell monopoly properties
                if isinstance(prop, Property):
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if all(p in game_state.properties[self] for p in group_properties):
                        continue
                
                # Only sell if we can get good value
                min_price = prop.price * 1.2  # At least 20% premium
                if opponent_cash >= min_price:
                    trade = TradeOffer(
                        source_player=self,
                        target_player=opponent,
                        properties_offered=[],
                        money_offered=0,
                        jail_cards_offered=0,
                        properties_requested=[prop],
                        money_requested=min(min_price, opponent_cash // 2),  # Don't take all their cash
                        jail_cards_requested=0
                    )
                    
                    if not GameValidation.validate_trade_offer(game_state, trade):
                        trades.append(trade)
        
        return trades


    def _create_monopoly_completion_trade(self, game_state: GameState, opponent,
                                        target_property: Property, property_values: Dict, 
                                        opponent_cash: int) -> Optional[TradeOffer]:
        """Create a trade offer to complete a monopoly."""
        # Calculate how much we're willing to pay
        monopoly_value = property_values.get(target_property, target_property.price) * 2.5
        max_offer = min(monopoly_value, opponent_cash // 2, game_state.player_balances[self] // 3)
        
        if max_offer < target_property.price:
            return None
        
        # Try different trade combinations
        
        # Option 1: Cash only
        cash_offer = min(target_property.price * 1.3, max_offer)
        if cash_offer <= opponent_cash // 3:  # Don't take too much of their cash
            trade = TradeOffer(
                source_player=self,
                target_player=opponent,
                properties_offered=[],
                money_offered=0,
                jail_cards_offered=0,
                properties_requested=[target_property],
                money_requested=int(cash_offer),
                jail_cards_requested=0
            )
            
            if not GameValidation.validate_trade_offer(game_state, trade):
                return trade
        
        # Option 2: Property + Cash
        suitable_properties = self._find_suitable_trade_properties(game_state, opponent, target_property)
        if suitable_properties:
            offered_property = suitable_properties[0]
            cash_difference = max(0, target_property.price - offered_property.price)
            
            if cash_difference <= max_offer:
                trade = TradeOffer(
                    source_player=self,
                    target_player=opponent,
                    properties_offered=[offered_property],
                    money_offered=int(cash_difference),
                    jail_cards_offered=0,
                    properties_requested=[target_property],
                    money_requested=0,
                    jail_cards_requested=0
                )
                
                if not GameValidation.validate_trade_offer(game_state, trade):
                    return trade
        
        return None


    def _create_monopoly_breaking_trade(self, game_state: GameState, opponent,
                                    target_property: Property, property_values: Dict,
                                    opponent_cash: int) -> Optional[TradeOffer]:
        """Create a trade offer to break opponent's monopoly."""
        # Calculate premium for breaking monopoly
        break_value = target_property.price * 2.0  # High premium
        max_offer = min(break_value, game_state.player_balances[self] // 4)
        
        if max_offer < target_property.price * 1.5:
            return None
        
        trade = TradeOffer(
            source_player=self,
            target_player=opponent,
            properties_offered=[],
            money_offered=0,
            jail_cards_offered=0,
            properties_requested=[target_property],
            money_requested=int(max_offer),
            jail_cards_requested=0
        )
        
        if not GameValidation.validate_trade_offer(game_state, trade):
            return trade
        
        return None


    def _create_value_trade(self, game_state: GameState, opponent, target_property,
                        property_values: Dict, opponent_cash: int) -> Optional[TradeOffer]:
        """Create a value-based trade offer."""
        our_value = property_values.get(target_property, target_property.price)
        fair_offer = min(our_value, target_property.price * 1.2)
        
        if fair_offer > game_state.player_balances[self] // 4:
            return None
        
        trade = TradeOffer(
            source_player=self,
            target_player=opponent,
            properties_offered=[],
            money_offered=0,
            jail_cards_offered=0,
            properties_requested=[target_property],
            money_requested=int(fair_offer),
            jail_cards_requested=0
        )
        
        if not GameValidation.validate_trade_offer(game_state, trade):
            return trade
        
        return None


    def _find_suitable_trade_properties(self, game_state: GameState, opponent, 
                                    target_property) -> List[Property]:
        """Find properties suitable for trading."""
        suitable = []
        
        for prop in game_state.properties[self]:
            if isinstance(prop, type(target_property)):
                # Don't trade monopoly properties
                if isinstance(prop, Property):
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if all(p in game_state.properties[self] for p in group_properties):
                        continue
                
                # Property should be of similar or lesser value
                if prop.price <= target_property.price * 1.2:
                    suitable.append(prop)
        
        # Sort by strategic value (lower first - we prefer to trade less valuable properties)
        suitable.sort(key=lambda p: p.price)
        return suitable


    def _score_trade_offer(self, game_state: GameState, trade_offer: TradeOffer) -> float:
        """Score a trade offer for prioritization."""
        # This is a simplified scoring - could be expanded
        properties_gained = trade_offer.properties_offered
        properties_lost = trade_offer.properties_requested
        net_cash = trade_offer.money_offered - trade_offer.money_requested
        
        monopoly_impact = self._calculate_monopoly_impact(game_state, properties_gained, properties_lost)
        
        score = 0.0
        score += monopoly_impact['monopolies_completed'] * 100
        score -= monopoly_impact['monopolies_broken'] * 80
        score += monopoly_impact['strategic_value'] / 10
        score += net_cash / 50
        
        return score
    

    def handle_bankruptcy(self, game_state: GameState, amount: int) -> BankruptcyRequest:
        cash = game_state.player_balances[self]
        needed = amount - cash
        
        # No bankruptcy if we have enough cash
        if needed <= 0:
            return BankruptcyRequest([], [], [])
        
        # Initialize request
        downgrading_suggestions = []
        mortgaging_suggestions = []
        
        # Order of liquidation depends on strategy params
        if self.strategy_params["bankruptcy_mortgage_first"]:
            # Try mortgaging first
            self._handle_bankruptcy_mortgaging(game_state, needed, mortgaging_suggestions)
            
            # If still not enough, try selling houses/hotels
            if self._calculate_bankruptcy_funds(game_state, BankruptcyRequest([], mortgaging_suggestions, [])) < needed:
                self._handle_bankruptcy_downgrading(game_state, needed, downgrading_suggestions)
                
            # If still not enough, try trades (not implemented for simplicity)
        else:
            # Try selling houses/hotels first
            self._handle_bankruptcy_downgrading(game_state, needed, downgrading_suggestions)
            
            # If still not enough, try mortgaging
            if self._calculate_bankruptcy_funds(game_state, BankruptcyRequest(downgrading_suggestions, [], [])) < needed:
                self._handle_bankruptcy_mortgaging(game_state, needed, mortgaging_suggestions)
                
            # If still not enough, try trades (not implemented for simplicity)
        
        # Check if we can avoid bankruptcy
        bankruptcy_request = BankruptcyRequest(downgrading_suggestions, mortgaging_suggestions, [])
        can_raise = self._calculate_bankruptcy_funds(game_state, bankruptcy_request)
        
        if can_raise < needed:
            # Cannot avoid bankruptcy, return empty request to signal bankruptcy
            return BankruptcyRequest([], [], [])
            
        return bankruptcy_request
    

    def _calculate_bankruptcy_funds(self, game_state: GameState, bankruptcy_request: BankruptcyRequest) -> int:
        """
        Calculate how much money would be raised from a bankruptcy request.
        
        Args:
            game_state: Current game state
            bankruptcy_request: The bankruptcy request to evaluate
            
        Returns:
            The amount of money that would be raised
        """
        funds = 0
        
        # Money from mortgaging
        for prop in bankruptcy_request.mortgaging_suggestions:
            funds += prop.mortgage
            
        # Money from selling houses/hotels
        for group in bankruptcy_request.downgrading_suggestions:
            if group in game_state.hotels and game_state.hotels[group][0] > 0 and game_state.hotels[group][1] == self:
                funds += group.hotel_cost() // 2
            elif group in game_state.houses and game_state.houses[group][0] > 0 and game_state.houses[group][1] == self:
                num_properties = len(game_state.board.get_properties_by_group(group))
                funds += (group.house_cost() // 2) * num_properties
                
        # Money from trades (not implemented for simplicity)
        
        return funds
    
    
    def _handle_bankruptcy_mortgaging(self, game_state: GameState, needed: int, mortgage_suggestions: List[Tile]) -> None:
        """
        Handle bankruptcy by suggesting properties to mortgage.
        
        Args:
            game_state: Current game state
            needed: The amount needed
            mortgage_suggestions: List to append mortgage suggestions to
        """
        property_values = self._calculate_property_values(game_state)
        funds_raised = 0
        
        # Get all unmortgaged properties
        properties = [p for p in game_state.properties[self] if p not in game_state.mortgaged_properties]
        
        # Filter out properties with houses/hotels
        properties = [p for p in properties if not (
            isinstance(p, Property) and 
            (p.group in game_state.houses and game_state.houses[p.group][0] > 0 or 
             p.group in game_state.hotels and game_state.hotels[p.group][0] > 0)
        )]
        
        # Sort properties by strategic value (lowest first)
        def property_priority(prop):
            value = property_values.get(prop, prop.price)
            
            # Adjust for group completion
            if isinstance(prop, Property):
                group_info = self._property_group_completion[prop.group]
                if group_info["is_monopoly"]:
                    # Avoid mortgaging monopolies
                    value *= self.strategy_params["bankruptcy_group_completion_weight"]
                    
            # Normalize by mortgage value
            return value / prop.mortgage if prop.mortgage > 0 else float('inf')
            
        sorted_properties = sorted(properties, key=property_priority)
        
        # Add properties to mortgage suggestions
        for prop in sorted_properties:
            # Validate mortgaging
            if not GameValidation.validate_mortgage_property(game_state, self, prop):
                mortgage_suggestions.append(prop)
                funds_raised += prop.mortgage
                
                # Stop if we've raised enough funds
                if funds_raised >= needed:
                    break
    

    def _handle_bankruptcy_downgrading(self, game_state: GameState, needed: int, downgrade_suggestions: List[PropertyGroup]) -> None:
        """
        Handle bankruptcy by suggesting properties to downgrade (sell houses/hotels).
        
        Args:
            game_state: Current game state
            needed: The amount needed
            downgrade_suggestions: List to append downgrade suggestions to
        """
        funds_raised = 0
        property_values = self._calculate_property_values(game_state)
        
        # Get all groups with development
        groups_with_development = []
        
        for group in PropertyGroup:
            if group not in game_state.houses or group not in game_state.hotels:
                continue
                
            houses = game_state.houses[group][0]
            hotels = game_state.hotels[group][0]
            
            if (houses > 0 or hotels > 0) and (game_state.houses[group][1] == self or game_state.hotels[group][1] == self):
                # Calculate value per development
                group_properties = game_state.board.get_properties_by_group(group)
                total_value = sum(property_values.get(prop, prop.price) for prop in group_properties)
                
                # Calculate money that would be raised by selling
                money_raised = 0
                if hotels > 0 and game_state.hotels[group][1] == self:
                    money_raised = group.hotel_cost() // 2
                elif houses > 0 and game_state.houses[group][1] == self:
                    money_raised = (group.house_cost() // 2) * len(group_properties)
                
                # Calculate ratio of value to money raised
                value_ratio = total_value / money_raised if money_raised > 0 else float('inf')
                
                groups_with_development.append((group, value_ratio))
        
        # Sort groups by value ratio (lowest first)
        groups_with_development.sort(key=lambda x: x[1])
        
        # Add groups to downgrade suggestions
        for group, _ in groups_with_development:
            # Validate downgrading
            if group in game_state.hotels and game_state.hotels[group][0] > 0 and game_state.hotels[group][1] == self:
                if not GameValidation.validate_sell_hotel(game_state, self, group):
                    downgrade_suggestions.append(group)
                    funds_raised += group.hotel_cost() // 2
            elif group in game_state.houses and game_state.houses[group][0] > 0 and game_state.houses[group][1] == self:
                if not GameValidation.validate_sell_house(game_state, self, group):
                    downgrade_suggestions.append(group)
                    num_properties = len(game_state.board.get_properties_by_group(group))
                    funds_raised += (group.house_cost() // 2) * num_properties
            
            # Stop if we've raised enough funds
            if funds_raised >= needed:
                break


class AggressiveInvestor(StrategicAgent):
    """
    Aggressive investor who prioritizes property acquisition and rapid development.
    Willing to take risks for high returns.
    
    Strategy:
    - Buys properties aggressively, especially early game
    - Builds houses quickly once monopolies are formed
    - Maintains lower cash reserves
    - More willing to get out of jail to continue acquiring properties
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property acquisition
            "min_cash_reserve": 100,  # Lower cash reserve
            "property_value_multiplier": 1.0,  # Less demanding on property value
            "first_property_eagerness": 1.0,  # Very eager to get first property in a group
            
            # Development
            "min_cash_for_houses": 250,  # Lower threshold for building
            "house_build_threshold": 0.25,  # More aggressive building
            
            # Risk tolerance
            "risk_tolerance": 0.9,  # High risk tolerance
            
            # Jail strategy
            "jail_stay_threshold": 0.3,  # Less likely to stay in jail
            "use_jail_card_threshold": 0.2,  # More likely to use jail card
        }
        super().__init__(name, strategy_params)


class CautiousAccumulator(StrategicAgent):
    """
    Cautious player who prioritizes cash reserves and only invests in high-value properties.
    More patient and defensive in strategy.
    
    Strategy:
    - Selective about property purchases
    - Maintains high cash reserves
    - Cautious about development
    - Prefers to stay in jail when board is risky
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property acquisition
            "min_cash_reserve": 300,  # Higher cash reserve
            "property_value_multiplier": 1.4,  # More demanding on property value
            "first_property_eagerness": 0.6,  # Less eager for first property
            
            # Development
            "min_cash_for_houses": 600,  # Higher threshold for building
            "house_build_threshold": 0.1,  # Less aggressive building
            
            # Risk tolerance
            "risk_tolerance": 0.3,  # Low risk tolerance
            
            # Jail strategy
            "jail_stay_threshold": 0.8,  # More likely to stay in jail
            "use_jail_card_threshold": 0.7,  # Less likely to use jail card
        }
        super().__init__(name, strategy_params)


class CompletionistBuilder(StrategicAgent):
    """
    Focuses heavily on completing monopolies and developing them quickly.
    Prioritizes sets over individual property value.
    
    Strategy:
    - Values completing sets highly
    - Aggressive about building once sets are complete
    - Will trade eagerly to complete sets
    - Willing to mortgage non-monopoly properties to fund development
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property acquisition
            "complete_set_bonus": 0.7,  # Much higher bonus for completing sets
            "first_property_eagerness": 0.9,  # Eager to get first in group
            
            # Development
            "min_cash_for_houses": 300,  # Moderate threshold
            "house_build_threshold": 0.2,  # Quite aggressive building
            "hotel_roi_threshold": 1.2,  # Lower threshold for hotels
            
            # Trading
            "trade_eagerness": 0.8,  # Very eager to trade
            "trade_monopoly_bonus": 500,  # Higher bonus for trades that complete monopolies
            
            # Cash management
            "mortgage_property_threshold": 0.5,  # More willing to mortgage non-set properties
        }
        super().__init__(name, strategy_params)


class UtilityKing(StrategicAgent):
    """
    Specializes in railroads and utilities. Values these more highly than 
    others and tries to collect full sets of them.
    
    Strategy:
    - Highly values railroads and utilities
    - Still builds on color properties when profitable
    - Trades aggressively to acquire railroads/utilities
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property acquisition
            "railway_value_multiplier": 1.7,  # Much higher value for railways
            "utility_value_multiplier": 1.5,  # Higher value for utilities
            
            # Trading
            "trade_eagerness": 0.7,  # Eager to trade
            
            # General strategy
            "orange_red_property_bonus": 1.1,  # Slightly reduced focus on orange/red
        }
        super().__init__(name, strategy_params)


class OrangeRedSpecialist(StrategicAgent):
    """
    Specializes in the statistically most landed-on properties (orange/red).
    Highly prioritizes these groups and develops them heavily.
    
    Strategy:
    - Extremely high valuation of orange and red properties
    - Moderate interest in other properties
    - Aggressive development of orange/red once acquired
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property valuation
            "orange_red_property_bonus": 1.6,  # Much higher valuation
            "jail_adjacent_bonus": 1.3,  # Higher bonus for properties after jail
            
            # Development
            "min_cash_for_houses": 350,  # Moderate threshold
            "hotel_roi_threshold": 1.3,  # Easier to build hotels
            
            # Trading
            "trade_eagerness": 0.7,  # Eager to trade for orange/red
        }
        super().__init__(name, strategy_params)


class LateGameDeveloper(StrategicAgent):
    """
    Focuses on accumulating properties early but delays development until late game.
    Then develops rapidly to maximize return.
    
    Strategy:
    - Buys properties aggressively early
    - Saves cash and delays building
    - Develops rapidly in late game
    - Conservative jail strategy early, more aggressive later
    """
    
    def __init__(self, name):
        strategy_params = {
            # Property acquisition
            "first_property_eagerness": 0.9,  # Eager for first properties
            "property_value_multiplier": 1.1,  # Moderately selective
            
            # Development - more conservative early, dynamic in actual play
            "min_cash_for_houses": 650,  # Higher threshold initially
            "house_build_threshold": 0.1,  # Conservative early
            
            # Cash management
            "min_cash_reserve": 250,  # Moderate cash reserve
            "unmortgage_threshold": 700,  # Higher unmortgage threshold
        }
        super().__init__(name, strategy_params)
        
        # This agent will dynamically adjust strategies based on game progression
        self._original_params = dict(strategy_params)
    
    def _update_turn_counter(self, game_state):
        """Override to also update strategy based on game progression"""
        super()._update_turn_counter(game_state)
        
        # Transition to more aggressive development in mid/late game
        if self._current_turn > 20:  # Late game
            self.strategy_params["min_cash_for_houses"] = 250  # Much lower threshold
            self.strategy_params["house_build_threshold"] = 0.2  # More aggressive building
            self.strategy_params["hotel_roi_threshold"] = 1.2  # More aggressive hotels
            self.strategy_params["jail_stay_threshold"] = 0.4  # Less likely to stay in jail
        elif self._current_turn > 10:  # Mid game
            self.strategy_params["min_cash_for_houses"] = 450  # Somewhat lower
            self.strategy_params["house_build_threshold"] = 0.15  # Somewhat more aggressive
            self.strategy_params["jail_stay_threshold"] = 0.6  # Moderate jail strategy


class Trademaster(StrategicAgent):
    """
    Focuses heavily on trading to complete monopolies. Willing to offer favorable
    trades to opponents to secure key properties.
    
    Strategy:
    - Extremely eager to trade
    - Values completing monopolies very highly
    - Will make trades that appear somewhat unfavorable to complete sets
    - Aggressive development once monopolies are secured
    """
    
    def __init__(self, name):
        strategy_params = {
            # Trading strategy
            "trade_eagerness": 1.0,  # Maximum eagerness
            "trade_profit_threshold": 0.9,  # Willing to make slightly unfavorable trades
            "trade_monopoly_bonus": 600,  # Very high bonus for monopoly completion
            
            # Property valuation
            "complete_set_bonus": 0.6,  # Higher bonus for completing sets
            
            # Development
            "min_cash_for_houses": 300,  # Moderate threshold
            "house_build_threshold": 0.18,  # Relatively aggressive
        }
        super().__init__(name, strategy_params)


class BalancedAgent(StrategicAgent):
    """
    A well-rounded strategy that balances all aspects of the game.
    Adapts to game conditions with moderate risk tolerance.
    
    Strategy:
    - Balanced approach to property acquisition
    - Moderate cash management
    - Strategic development based on ROI
    - Adapts jail strategy to board conditions
    """
    
    def __init__(self, name):
        # Uses mostly default parameters with slight optimization
        strategy_params = {
            # Property acquisition
            "min_cash_reserve": 180,
            "property_value_multiplier": 1.15,
            
            # Development
            "min_cash_for_houses": 400,
            "house_build_threshold": 0.15,
            
            # Risk assessment
            "risk_tolerance": 0.5,
            
            # Value premium on high-traffic properties
            "orange_red_property_bonus": 1.25,
        }
        super().__init__(name, strategy_params)


class DynamicAdapter(StrategicAgent):
    """
    Highly adaptive player that changes strategy based on game state.
    Analyzes opponents and board conditions to make optimal decisions.
    
    Strategy:
    - Adapts property valuation based on what others own
    - Adjusts risk tolerance based on position in the game
    - Changes development strategy based on opponents' developments
    - Most complex AI with situational strategy shifts
    """
    
    def __init__(self, name):
        strategy_params = {
            # Start with balanced parameters
            "min_cash_reserve": 200,
            "property_value_multiplier": 1.2,
            "risk_tolerance": 0.6,
        }
        super().__init__(name, strategy_params)
        
        # Internal state tracking
        self._last_opponent_states = {}
        self._board_analysis = {}
        self._strategy_mode = "balanced"  # Initial strategy
    
    def _update_turn_counter(self, game_state):
        """Override to analyze game state and adapt strategy"""
        super()._update_turn_counter(game_state)
        
        # Store opponent states for analysis
        self._analyze_opponents(game_state)
        
        # Determine appropriate strategy mode
        self._adapt_strategy(game_state)
    
    def _analyze_opponents(self, game_state):
        """Analyze opponents' positions and strategies"""
        for player in game_state.players:
            if player == self:
                continue
                
            # Track basic metrics
            self._last_opponent_states[player] = {
                "cash": game_state.player_balances[player],
                "properties": len(game_state.properties[player]),
                "development": self._calculate_opponent_development(game_state, player),
                "monopolies": self._count_opponent_monopolies(game_state, player)
            }
    
    def _calculate_opponent_development(self, game_state, player):
        """Calculate opponent's development level"""
        development_score = 0
        for group in PropertyGroup:
            if game_state.houses[group][1] == player:
                development_score += game_state.houses[group][0] * len(game_state.board.get_properties_by_group(group))
            if game_state.hotels[group][1] == player:
                development_score += 5 * len(game_state.board.get_properties_by_group(group))  # Hotel = 5 houses
        
        return development_score
    
    def _count_opponent_monopolies(self, game_state, player):
        """Count how many monopolies an opponent has"""
        monopoly_count = 0
        for group in PropertyGroup:
            properties = game_state.board.get_properties_by_group(group)
            if all(p in game_state.properties[player] for p in properties):
                monopoly_count += 1
        
        return monopoly_count
    
    def _adapt_strategy(self, game_state):
        """Adapt strategy based on game analysis"""
        # Early game strategy (focus on acquisition)
        if self._current_turn <= 10:
            self.strategy_params["property_value_multiplier"] = 1.1
            self.strategy_params["min_cash_reserve"] = 150
            self.strategy_params["trade_eagerness"] = 0.7
            self._strategy_mode = "acquisition"
            
        # Mid game strategy
        elif self._current_turn <= 25:
            # Check if leading in properties
            self_properties = len(game_state.properties[self])
            max_opponent_properties = max(len(game_state.properties[p]) for p in game_state.players if p != self)
            
            if self_properties > max_opponent_properties:
                # Leading - focus on development
                self.strategy_params["min_cash_for_houses"] = 350
                self.strategy_params["house_build_threshold"] = 0.18
                self._strategy_mode = "development"
            else:
                # Behind - focus on strategic acquisition and trading
                self.strategy_params["trade_eagerness"] = 0.9
                self.strategy_params["trade_profit_threshold"] = 1.0
                self._strategy_mode = "strategic_catch_up"
                
        # Late game strategy
        else:
            # Count developed properties
            self_development = self._calculate_opponent_development(game_state, self)
            max_opponent_development = max(data["development"] for player, data in self._last_opponent_states.items())
            
            if self_development > max_opponent_development:
                # Leading in development - focus on maximizing rent
                self.strategy_params["min_cash_reserve"] = 250
                self.strategy_params["hotel_roi_threshold"] = 1.2
                self._strategy_mode = "maximize_rent"
            else:
                # Behind in development - focus on high-traffic properties
                self.strategy_params["orange_red_property_bonus"] = 1.5
                self.strategy_params["jail_adjacent_bonus"] = 1.4
                self._strategy_mode = "high_traffic_focus"