from typing import List, Dict, Set, Tuple

from game.player import Player
from game.game_state import GameState
from game.game_validation import GameValidation
from game.bankruptcy_request import BankruptcyRequest
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from models.trade_offer import TradeOffer


class AlgorithmicAgent(Player):
    """
    Algorithmic Monopoly agent that makes decisions using configurable rule-based strategies.
    
    This agent implements a comprehensive algorithmic approach to Monopoly gameplay,
    using quantitative analysis and configurable parameters to make strategic decisions.
    All decisions are subject to game rule validation, with invalid actions being
    automatically filtered out.
    
    The agent evaluates properties based on multiple strategic factors including
    rent-to-cost ratios, set completion potential, landing probabilities, and
    development opportunities. Financial management is handled through configurable
    thresholds for cash reserves, emergency situations, and ROI calculations.

    Attributes
    ----------
    min_safe_balance : int
        Minimum cash to maintain for safety and future opportunities
    emergency_threshold : int
        Cash level below which emergency measures (mortgaging, selling) are triggered
    property_value_threshold : float
        Multiplier for property purchase decisions (buy if value > price * threshold)
    hotel_roi_threshold : float
        Minimum ROI required to upgrade properties to hotels
    house_roi_threshold : float
        Minimum ROI required to upgrade properties with houses
    max_mortgage_at_once : int
        Maximum number of properties to mortgage in a single turn
    railway_value_multiplier : float
        Value multiplier for railways based on quantity owned
    utility_pair_multiplier : float
        Value multiplier when owning multiple utilities
    complete_set_multiplier : float
        Value multiplier for properties that complete color groups
    jail_escape_property_threshold : int
        Minimum number of valuable properties required to justify paying jail fine
    bankruptcy_liquidity_priority : bool
        If True, prioritize selling buildings over mortgaging in bankruptcy
    property_values : Dict[Tile, float]
        Cache for calculated property strategic values
    """


    def __init__(self, name: str, 
                 min_safe_balance: int = 200,
                 emergency_threshold: int = 100,
                 property_value_threshold: float = 1.1,
                 hotel_roi_threshold: float = 0.15,
                 house_roi_threshold: float = 0.12,
                 max_mortgage_at_once: int = 2,
                 railway_value_multiplier: float = 1.2,
                 utility_pair_multiplier: float = 1.5,
                 complete_set_multiplier: float = 1.5,
                 jail_escape_property_threshold: int = 2,
                 bankruptcy_liquidity_priority: bool = True):
        """
        Initialize the algorithmic agent with configurable strategy parameters.
        
        Parameters
        ----------
        name : str
            Display name for this agent
        min_safe_balance : int, default 200
            Minimum cash to maintain for safety and opportunities
        emergency_threshold : int, default 100
            Cash level that triggers emergency asset liquidation
        property_value_threshold : float, default 1.1
            Buy properties only if strategic value exceeds price * threshold
        hotel_roi_threshold : float, default 0.15
            Minimum ROI required for hotel upgrades
        house_roi_threshold : float, default 0.12
            Minimum ROI required for house upgrades
        max_mortgage_at_once : int, default 2
            Maximum properties to mortgage per decision cycle
        railway_value_multiplier : float, default 1.2
            Exponential multiplier for railway values based on quantity
        utility_pair_multiplier : float, default 1.5
            Value multiplier when second utility is acquired
        complete_set_multiplier : float, default 1.5
            Value multiplier for properties completing color groups
        jail_escape_property_threshold : int, default 2
            Minimum valuable properties to justify paying jail fine
        bankruptcy_liquidity_priority : bool, default True
            Prioritize building sales over property mortgaging in bankruptcy
        """
        super().__init__(name)
        # Configurable parameters
        self.min_safe_balance = min_safe_balance
        self.emergency_threshold = emergency_threshold
        self.property_value_threshold = property_value_threshold
        self.hotel_roi_threshold = hotel_roi_threshold
        self.house_roi_threshold = house_roi_threshold
        self.max_mortgage_at_once = max_mortgage_at_once
        self.railway_value_multiplier = railway_value_multiplier
        self.utility_pair_multiplier = utility_pair_multiplier
        self.complete_set_multiplier = complete_set_multiplier
        self.jail_escape_property_threshold = jail_escape_property_threshold
        self.bankruptcy_liquidity_priority = bankruptcy_liquidity_priority  # If True, prioritize liquid assets in bankruptcy
        
        self.property_values = {}  # Cache for property valuations


    def calculate_property_value(self, game_state: GameState, property: Tile) -> float:
        """
        Calculate the strategic value of a property using multiple valuation factors.
        
        Evaluates properties based on rent-to-cost ratios, set completion potential,
        landing probabilities, and synergies with existing portfolio. Results are
        cached for performance optimization.
        
        Parameters
        ----------
        game_state : GameState
            Current game state
        property : Tile
            Property to evaluate
            
        Returns
        -------
        float
            Calculated strategic value of the property
        """
        if property in self.property_values:
            return self.property_values[property]
        
        base_value = property.price
        value_multiplier = 1.0

        if isinstance(property, Property):
            # Value complete color sets higher
            group_properties = game_state.board.get_properties_by_group(property.group)
            owned_in_group = sum(1 for p in group_properties if p in game_state.properties.get(self, []))
            total_in_group = len(group_properties)
            
            # High value for completing a set
            if owned_in_group == total_in_group - 1:
                value_multiplier *= self.complete_set_multiplier
            
            # Value properties with high rent return
            rent_to_cost = property.hotel_rent / property.price if property.price > 0 else 0
            value_multiplier *= (1 + rent_to_cost)
            
            # Value properties that others land on frequently (based on statistical analysis)
            landing_probability = {
                6: 1.3,   
                16: 1.2,  
                26: 1.2,  
                9: 1.1,   
                4: 1.1,   
                10: 1.1
            }.get(property.id, 1.0)
            value_multiplier *= landing_probability

        elif isinstance(property, Railway):
            # Railways become exponentially more valuable with quantity
            owned_railways = sum(1 for p in game_state.properties.get(self, []) if isinstance(p, Railway))
            value_multiplier *= (self.railway_value_multiplier ** owned_railways)

        elif isinstance(property, Utility):
            # Utilities gain significant value when paired
            owned_utilities = sum(1 for p in game_state.properties.get(self, []) if isinstance(p, Utility))
            value_multiplier *= (self.utility_pair_multiplier if owned_utilities == 1 else 1.0)

        calculated_value = base_value * value_multiplier
        self.property_values[property] = calculated_value
        return calculated_value


    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        # First validate that we can buy this property
        if error := GameValidation.validate_buy_property(game_state, self, property):
            return False

        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        budget = game_state.player_balances.get(self, 0)
        price = property.price

        # Ensure purchase maintains minimum safe balance
        if budget < price + self.min_safe_balance:
            return False

        # Buy only if strategic value exceeds price threshold
        property_value = self.calculate_property_value(game_state, property)
        return property_value > price * self.property_value_threshold


    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = [p for p in game_state.properties.get(self, []) if isinstance(p, Property)]
        grouped_properties = {p.group: [] for p in properties}
        for prop in properties:
            grouped_properties[prop.group].append(prop)

        budget = game_state.player_balances.get(self, 0)
        suggestions = []

        for group, props in grouped_properties.items():
            # Skip if any property in the group is mortgaged
            if any(p in game_state.mortgaged_properties for p in props):
                continue
                
            # Must own complete color group to develop
            if len(props) != len(game_state.board.get_properties_by_group(group)):
                continue

            # Check if the group exists in houses/hotels dictionaries
            if group not in game_state.houses or group not in game_state.hotels:
                continue

            current_houses = game_state.houses[group][0]
            current_hotels = game_state.hotels[group][0]
            
            # Consider hotel upgrade (4 houses -> hotel)
            if current_hotels == 0 and current_houses == 4:
                cost = group.hotel_cost()
                if budget >= cost + self.min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=True)
                    if roi > self.hotel_roi_threshold:
                        # Validate hotel placement
                        if not GameValidation.validate_place_hotel(game_state, self, group):
                            suggestions.append(group)
                            budget -= cost
            
            # Consider house upgrade (0-3 houses -> +1 house)
            elif current_houses < 4 and current_hotels == 0:
                cost = group.house_cost() * len(props)
                if budget >= cost + self.min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                    if roi > self.house_roi_threshold:
                        # Validate house placement
                        if not GameValidation.validate_place_house(game_state, self, group):
                            suggestions.append(group)
                            budget -= cost

        return suggestions


    def _calculate_upgrade_roi(self, game_state: GameState, group: PropertyGroup, is_hotel: bool) -> float:
        """
        Calculate return on investment for a potential property upgrade.
        
        Compares rent increase from upgrade against the cost of development
        to determine if the investment meets ROI thresholds.
        
        Parameters
        ----------
        game_state : GameState
            Current game state
        group : PropertyGroup
            Property group to analyze for upgrade
        is_hotel : bool
            True for hotel upgrade, False for house upgrade
            
        Returns
        -------
        float
            ROI as rent increase per dollar invested
        """
        properties = game_state.board.get_properties_by_group(group)
        
        # Check if the group exists in houses dictionary
        if group not in game_state.houses:
            return 0.0
            
        current_houses = game_state.houses[group][0]
        
        # Calculate current total rent for the group
        current_rent = 0
        for p in properties:
            if current_houses > 0:
                if 0 <= current_houses - 1 < len(p.house_rent):
                    current_rent += p.house_rent[current_houses - 1]
                else:
                    current_rent += p.base_rent
            else:
                current_rent += p.base_rent
        
        # Calculate rent after upgrade
        if is_hotel:
            new_rent = sum(p.hotel_rent for p in properties)
            cost = group.hotel_cost()
        else:
            new_houses = current_houses + 1
            new_rent = 0
            for p in properties:
                if 0 <= new_houses - 1 < len(p.house_rent):
                    new_rent += p.house_rent[new_houses - 1]
                else:
                    new_rent += p.base_rent
            cost = group.house_cost() * len(properties)
            
        return (new_rent - current_rent) / cost if cost > 0 else 0


    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties.get(self, [])
        budget = game_state.player_balances.get(self, 0)
        
        # Only mortgage in emergency situations
        if budget > self.emergency_threshold:
            return []
            
        mortgage_candidates = []
        for prop in properties:
            if isinstance(prop, Property):
                # Don't mortgage properties with buildings
                if prop.group in game_state.houses and game_state.houses[prop.group][0] > 0:
                    continue
                if prop.group in game_state.hotels and game_state.hotels[prop.group][0] > 0:
                    continue
                    
            if prop not in game_state.mortgaged_properties:
                # Validate mortgaging
                if error := GameValidation.validate_mortgage_property(game_state, self, prop):
                    continue
                    
                strategic_value = self.calculate_property_value(game_state, prop)
                mortgage_value = prop.mortgage
                
                if mortgage_value > 0:  # Avoid division by zero
                    # Lower ratio = better candidate for mortgaging
                    mortgage_candidates.append((prop, strategic_value / mortgage_value))
                    
        # Sort by strategic value ratio (lowest first - best to mortgage)
        mortgage_candidates.sort(key=lambda x: x[1])
        return [prop for prop, _ in mortgage_candidates[:self.max_mortgage_at_once]]


    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties.get(self, [])
        budget = game_state.player_balances.get(self, 0)
        mortgaged_properties = [p for p in properties if p in game_state.mortgaged_properties]
        
        if not mortgaged_properties or budget < self.min_safe_balance:
            return []
        
        unmortgage_candidates = []
        for prop in mortgaged_properties:
            # Validate unmortgaging
            if error := GameValidation.validate_unmortgage_property(game_state, self, prop):
                continue
                
            strategic_value = self.calculate_property_value(game_state, prop)
            
            # Calculate priority score based on various factors
            if prop.buyback_price > 0:  # Avoid division by zero
                priority_score = strategic_value / prop.buyback_price
            else:
                priority_score = 0
            
            if isinstance(prop, Property):
                # Higher priority for properties that complete sets
                group_properties = game_state.board.get_properties_by_group(prop.group)
                owned_unmortgaged = sum(1 for p in group_properties 
                                      if p in game_state.properties.get(self, []) and 
                                      p not in game_state.mortgaged_properties)
                total_in_group = len(group_properties)
                
                # Boost priority if this completes a monopoly
                if owned_unmortgaged == total_in_group - 1:
                    priority_score *= 1.5
                    
            if budget >= prop.buyback_price + self.min_safe_balance:
                unmortgage_candidates.append((prop, priority_score))
        
        # Sort by highest priority first
        unmortgage_candidates.sort(key=lambda x: x[1], reverse=True)
        return [prop for prop, _ in unmortgage_candidates[:self.max_mortgage_at_once]]


    def get_downgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        # Only downgrade in emergency situations
        if game_state.player_balances.get(self, 0) > self.emergency_threshold:
            return []
            
        properties = [p for p in game_state.properties.get(self, []) if isinstance(p, Property)]
        grouped_properties = {p.group: [] for p in properties}
        for prop in properties:
            grouped_properties[prop.group].append(prop)
            
        suggestions = []
        for group, props in grouped_properties.items():
            # Must own complete color group to have developments
            if len(props) != len(game_state.board.get_properties_by_group(group)):
                continue
                
            # Check if the group exists in houses/hotels dictionaries
            if group not in game_state.houses or group not in game_state.hotels:
                continue
                
            # Consider selling hotels
            if game_state.hotels[group][0] > 0 and game_state.hotels[group][1] == self:
                # Validate hotel sale
                if error := GameValidation.validate_sell_hotel(game_state, self, group):
                    continue
                    
                roi = self._calculate_upgrade_roi(game_state, group, is_hotel=True)
                # Use lower threshold for selling (emergency situation)
                if roi < self.hotel_roi_threshold * 0.7:
                    suggestions.append(group)
            
            # Consider selling houses
            elif game_state.houses[group][0] > 0 and game_state.houses[group][1] == self:
                # Validate house sale
                if error := GameValidation.validate_sell_house(game_state, self, group):
                    continue
                    
                roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                # Use lower threshold for selling (emergency situation)
                if roi < self.house_roi_threshold * 0.7:
                    suggestions.append(group)
                    
        return suggestions


    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        # First check if player is in jail
        if not game_state.in_jail.get(self, False):
            return False
            
        budget = game_state.player_balances.get(self, 0)
        fine = game_state.board.get_jail_fine()
        
        # Don't pay if it would compromise financial safety
        if budget < fine * 2:
            return False
            
        # Pay fine only if we have valuable properties worth actively managing
        valuable_properties = sum(1 for p in game_state.properties.get(self, []) 
                                if isinstance(p, Property) and 
                                self.calculate_property_value(game_state, p) > p.price * self.property_value_threshold)
        return valuable_properties > self.jail_escape_property_threshold


    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        # First check if player is in jail
        if not game_state.in_jail.get(self, False):
            return False
            
        if game_state.escape_jail_cards.get(self, 0) == 0:
            return False
            
        # Use card if we have developed properties that need active management
        valuable_properties = 0
        for p in game_state.properties.get(self, []):
            if isinstance(p, Property):
                group = p.group
                # Count properties with houses or hotels
                if (group in game_state.houses and game_state.houses[group][0] > 0 and game_state.houses[group][1] == self) or \
                   (group in game_state.hotels and game_state.hotels[group][0] > 0 and game_state.hotels[group][1] == self):
                    valuable_properties += 1
                    
        return valuable_properties > 0
    

    def should_accept_trade_offer(self, game_state: GameState, trade_offer: TradeOffer) -> bool:
        # Validate trade offer with GameValidation
        if error := GameValidation.validate_trade_offer(game_state, trade_offer):
            return False
        
        # Initialize with empty lists/values if None
        properties_offered = trade_offer.properties_offered or []
        money_offered = trade_offer.money_offered or 0
        jail_cards_offered = trade_offer.jail_cards_offered or 0
        properties_requested = trade_offer.properties_requested or []
        money_requested = trade_offer.money_requested or 0
        jail_cards_requested = trade_offer.jail_cards_requested or 0

        # Calculate total value of what we're giving up
        value_giving = (
            money_requested +
            (jail_cards_requested * 50) +  # Base strategic value for jail cards
            sum(self.calculate_property_value(game_state, prop)
                for prop in properties_requested if prop is not None)
        )

        # Calculate total value of what we're receiving
        value_receiving = (
            money_offered +
            (jail_cards_offered * 50) +
            sum(self.calculate_property_value(game_state, prop)
                for prop in properties_offered if prop is not None)
        )

        # Additional value adjustments based on strategic factors
        for prop in properties_offered:
            if prop is not None and isinstance(prop, Property):
                # Check if this completes a color set for us
                group_properties = game_state.board.get_properties_by_group(prop.group)
                if group_properties:  # Verify group properties exist
                    owned_in_group = sum(1 for p in group_properties 
                                    if p in game_state.properties.get(self, []))
                    # Massive bonus for completing monopoly
                    if owned_in_group == len(group_properties) - 1:
                        value_receiving *= self.complete_set_multiplier

        for prop in properties_requested:
            if prop is not None and isinstance(prop, Property):
                # Reduce likelihood of breaking existing color sets
                group_properties = game_state.board.get_properties_by_group(prop.group)
                if group_properties:  # Verify group properties exist
                    owned_in_group = sum(1 for p in group_properties 
                                    if p in game_state.properties.get(self, []))
                    # Penalty for breaking monopoly
                    if owned_in_group == len(group_properties):
                        value_giving *= self.complete_set_multiplier

        # Consider current financial situation
        if game_state.player_balances.get(self, 0) - money_requested < self.emergency_threshold:
            value_giving *= 1.5  # Increase perceived cost if it puts us in financial danger

        # Strategic adjustment based on other player's position
        if trade_offer.source_player in game_state.properties:
            opponent_properties = len(game_state.properties[trade_offer.source_player])
            our_properties = len(game_state.properties.get(self, []))
            # If opponent is significantly ahead, be more willing to take risks
            if opponent_properties > our_properties * 1.5:
                value_receiving *= 1.2

        # Final decision with margin for positive trades
        return value_receiving > value_giving * 1.1  # 10% margin required for acceptance


    def get_trade_offers(self, game_state: GameState) -> List[TradeOffer]:
        trade_offers = []
        
        # Validate game state and players
        if not game_state or not game_state.players:
            return []
            
        other_players = [p for p in game_state.players if p != self]
        if not other_players:
            return []
        
        for target_player in other_players:
            # Validate target player exists in game state
            if target_player not in game_state.properties or \
            target_player not in game_state.player_balances:
                continue

            # Skip if target player is in poor financial condition
            if game_state.player_balances[target_player] < self.emergency_threshold:
                continue

            # Analyze which properties we want from them
            desired_properties = []
            for prop in game_state.properties[target_player]:
                if prop is not None and isinstance(prop, Property):
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if not group_properties:  # Skip if group properties don't exist
                        continue
                        
                    our_count = sum(1 for p in group_properties 
                                if p in game_state.properties.get(self, []))
                    # Target properties in groups where we already have a presence
                    if our_count > 0:
                        # Validate if property can be in trade offer
                        if not GameValidation.validate_property_in_trade_offer(game_state, prop, target_player):
                            desired_properties.append(prop)

            if not desired_properties:
                continue

            # Calculate what we're willing to offer
            properties_to_offer = []
            money_to_offer = 0
            
            # Look for properties we're willing to trade
            for prop in game_state.properties.get(self, []):
                if prop is not None and isinstance(prop, Property):
                    # Don't offer properties that would break our monopolies
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if not group_properties:  # Skip if group properties don't exist
                        continue
                        
                    our_count = sum(1 for p in group_properties 
                                if p in game_state.properties.get(self, []))
                    # Only offer properties from incomplete sets
                    if our_count != len(group_properties):
                        strategic_value = self.calculate_property_value(game_state, prop)
                        # Only offer properties below our value threshold
                        if strategic_value < prop.price * self.property_value_threshold:
                            # Validate if property can be in trade offer
                            if not GameValidation.validate_property_in_trade_offer(game_state, prop, self):
                                properties_to_offer.append(prop)

            # Calculate fair money offer based on property values
            desired_value = sum(self.calculate_property_value(game_state, p) 
                            for p in desired_properties if p is not None)
            offered_value = sum(self.calculate_property_value(game_state, p) 
                            for p in properties_to_offer if p is not None)
            
            value_difference = desired_value - offered_value
            
            # Only proceed if we can afford a fair trade
            if value_difference > 0:
                # Ensure we maintain minimum safe balance
                max_money_offer = game_state.player_balances.get(self, 0) - self.min_safe_balance
                money_to_offer = min(value_difference, max_money_offer)
                
                if money_to_offer > 0 or properties_to_offer:
                    trade_offer = TradeOffer(
                        source_player=self,
                        target_player=target_player,
                        properties_offered=properties_to_offer,
                        money_offered=money_to_offer,
                        jail_cards_offered=0,
                        properties_requested=desired_properties,
                        money_requested=0,
                        jail_cards_requested=0
                    )
                    
                    # Validate the trade offer
                    if not GameValidation.validate_trade_offer(game_state, trade_offer):
                        trade_offers.append(trade_offer)

        return trade_offers


    def handle_bankruptcy(self, game_state: GameState, amount: int) -> BankruptcyRequest:
        current_balance = game_state.player_balances.get(self, 0)
        if current_balance >= amount:
            return BankruptcyRequest([], [], [])
            
        needed_amount = amount - current_balance
        
        # Initialize lists for the bankruptcy request
        downgrading_suggestions = []
        mortgaging_suggestions = []
        
        # First, analyze all assets and their strategic value
        properties = game_state.properties.get(self, [])
        property_values = {prop: self.calculate_property_value(game_state, prop) for prop in properties}
        
        # Identify properties with developments
        developed_groups = {}
        for group in PropertyGroup:
            # Check if we own all properties in the group
            group_properties = game_state.board.get_properties_by_group(group)
            if not all(prop in properties for prop in group_properties):
                continue
                
            # Check if the group has houses or hotels
            if group in game_state.houses and game_state.houses[group][0] > 0 and game_state.houses[group][1] == self:
                developed_groups[group] = {
                    'type': 'houses',
                    'count': game_state.houses[group][0],
                    'value': group.house_cost() * len(group_properties) / 2,  # Half price when selling
                    'strategic_value': sum(property_values.get(prop, 0) for prop in group_properties) / game_state.houses[group][0]
                }
            elif group in game_state.hotels and game_state.hotels[group][0] > 0 and game_state.hotels[group][1] == self:
                developed_groups[group] = {
                    'type': 'hotels',
                    'count': game_state.hotels[group][0],
                    'value': group.hotel_cost() / 2,  # Half price when selling
                    'strategic_value': sum(property_values.get(prop, 0) for prop in group_properties)
                }
        
        # Identify mortgageable properties (not in developed groups)
        mortgageable_properties = []
        for prop in properties:
            if prop in game_state.mortgaged_properties:
                continue
                
            if isinstance(prop, Property):
                # Skip if property is in a developed group
                if prop.group in developed_groups:
                    continue
                
            # Validate mortgaging
            if not GameValidation.validate_mortgage_property(game_state, self, prop):
                mortgageable_properties.append({
                    'property': prop,
                    'value': prop.mortgage,
                    'strategic_value': property_values.get(prop, 0) / prop.mortgage if prop.mortgage > 0 else float('inf')
                })
        
        # Strategy: Decide order of liquidation based on bankruptcy_liquidity_priority parameter
        money_raised = 0
        
        if self.bankruptcy_liquidity_priority:
            # Prioritize liquidity - Sell houses/hotels first, then mortgage properties
            
            # Sort developed groups by strategic value (lowest first)
            sorted_groups = sorted(developed_groups.items(), key=lambda x: x[1]['strategic_value'])
            
            # Downgrade buildings until we have enough or run out
            for group, details in sorted_groups:
                if money_raised >= needed_amount:
                    break
                    
                if details['type'] == 'hotels':
                    # Validate hotel sale
                    if not GameValidation.validate_sell_hotel(game_state, self, group):
                        downgrading_suggestions.append(group)
                        money_raised += details['value']
                elif details['type'] == 'houses':
                    # Validate house sale
                    if not GameValidation.validate_sell_house(game_state, self, group):
                        downgrading_suggestions.append(group)
                        money_raised += details['value']
            
            # If we still need more money, mortgage properties
            if money_raised < needed_amount:
                # Sort properties by strategic value (lowest first)
                sorted_properties = sorted(mortgageable_properties, key=lambda x: x['strategic_value'])
                
                for prop_info in sorted_properties:
                    if money_raised >= needed_amount:
                        break
                        
                    mortgaging_suggestions.append(prop_info['property'])
                    money_raised += prop_info['value']
        else:
            # Prioritize property preservation - Mortgage properties first, then sell houses/hotels
            
            # Sort properties by strategic value (lowest first)
            sorted_properties = sorted(mortgageable_properties, key=lambda x: x['strategic_value'])
            
            # Mortgage properties until we have enough or run out
            for prop_info in sorted_properties:
                if money_raised >= needed_amount:
                    break
                    
                mortgaging_suggestions.append(prop_info['property'])
                money_raised += prop_info['value']
            
            # If we still need more money, sell houses/hotels
            if money_raised < needed_amount:
                # Sort developed groups by strategic value (lowest first)
                sorted_groups = sorted(developed_groups.items(), key=lambda x: x[1]['strategic_value'])
                
                for group, details in sorted_groups:
                    if money_raised >= needed_amount:
                        break
                        
                    if details['type'] == 'hotels':
                        # Validate hotel sale
                        if not GameValidation.validate_sell_hotel(game_state, self, group):
                            downgrading_suggestions.append(group)
                            money_raised += details['value']
                    elif details['type'] == 'houses':
                        # Validate house sale
                        if not GameValidation.validate_sell_house(game_state, self, group):
                            downgrading_suggestions.append(group)
                            money_raised += details['value']
        
        # Check if we can raise enough money
        if money_raised < needed_amount:
            # We can't avoid bankruptcy, return empty request
            return BankruptcyRequest([], [], [])
            
        return BankruptcyRequest(downgrading_suggestions, mortgaging_suggestions, [])