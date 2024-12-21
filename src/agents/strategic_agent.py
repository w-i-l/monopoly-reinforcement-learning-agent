from game.player import Player
from game.game_state import GameState
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.utility import Utility
from models.railway import Railway
from typing import List, Dict
from models.trade_offer import TradeOffer

class StrategicAgent(Player):
    def __init__(self, name, 
                 min_safe_balance: int = 200,
                 emergency_threshold: int = 100,
                 property_value_threshold: float = 1.1,
                 hotel_roi_threshold: float = 0.15,
                 house_roi_threshold: float = 0.12,
                 max_mortgage_at_once: int = 2,
                 railway_value_multiplier: float = 1.2,
                 utility_pair_multiplier: float = 1.5,
                 complete_set_multiplier: float = 1.5,
                 jail_escape_property_threshold: int = 2):
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
                value_multiplier *= self.complete_set_multiplier
            
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
            value_multiplier *= (self.railway_value_multiplier ** owned_railways)

        elif isinstance(property, Utility):
            owned_utilities = sum(1 for p in game_state.properties[self] if isinstance(p, Utility))
            value_multiplier *= (self.utility_pair_multiplier if owned_utilities == 1 else 1.0)

        self.property_values[property] = base_value * value_multiplier
        return self.property_values[property]

    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Utility) or isinstance(property, Railway)):
            return False

        budget = game_state.player_balances[self]
        price = property.price

        if budget < price + self.min_safe_balance:
            return False

        if property in game_state.properties[self] or property in game_state.mortgaged_properties:
            return False

        property_value = self.calculate_property_value(game_state, property)
        return property_value > price * self.property_value_threshold

    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        properties = [p for p in game_state.properties[self] if isinstance(p, Property)]
        grouped_properties = {p.group: [] for p in properties}
        for prop in properties:
            grouped_properties[prop.group].append(prop)

        budget = game_state.player_balances[self]
        suggestions = []

        for group, props in grouped_properties.items():
            # Skip if any property in the group is mortgaged
            if any(p in game_state.mortgaged_properties for p in props):
                continue
                
            if len(props) != len(game_state.board.get_properties_by_group(group)):
                continue

            current_houses = game_state.houses[group][0]
            current_hotels = game_state.hotels[group][0]
            
            if current_hotels == 0 and current_houses == 4:
                cost = group.hotel_cost()
                if budget >= cost + self.min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=True)
                    if roi > self.hotel_roi_threshold:
                        suggestions.append(group)
                        budget -= cost
            elif current_houses < 4 and current_hotels == 0:
                cost = group.house_cost() * len(props)
                if budget >= cost + self.min_safe_balance:
                    roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                    if roi > self.house_roi_threshold:
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
        
        if budget > self.emergency_threshold:
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
                
        mortgage_candidates.sort(key=lambda x: x[1])
        return [prop for prop, _ in mortgage_candidates[:self.max_mortgage_at_once]]

    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        properties = game_state.properties[self]
        budget = game_state.player_balances[self]
        mortgaged_properties = [p for p in properties if p in game_state.mortgaged_properties]
        
        if not mortgaged_properties or budget < self.min_safe_balance:
            return []
        
        unmortgage_candidates = []
        for prop in mortgaged_properties:
            strategic_value = self.calculate_property_value(game_state, prop)
            
            # Calculate priority score based on various factors
            priority_score = strategic_value / prop.buyback_price
            
            if isinstance(prop, Property):
                # Higher priority for properties that complete sets
                group_properties = game_state.board.get_properties_by_group(prop.group)
                owned_unmortgaged = sum(1 for p in group_properties 
                                      if p in game_state.properties[self] and 
                                      p not in game_state.mortgaged_properties)
                total_in_group = len(group_properties)
                
                if owned_unmortgaged == total_in_group - 1:
                    priority_score *= 1.5
                    
            if budget >= prop.buyback_price + self.min_safe_balance:
                unmortgage_candidates.append((prop, priority_score))
        
        unmortgage_candidates.sort(key=lambda x: x[1], reverse=True)  # Sort by highest priority
        return [prop for prop, _ in unmortgage_candidates[:self.max_mortgage_at_once]]

    def get_downgrading_suggestions(self, game_state: GameState) -> List[Tile]:
        if game_state.player_balances[self] > self.emergency_threshold:
            return []
            
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
                if roi < self.hotel_roi_threshold * 0.7:  # Lower threshold for selling
                    suggestions.append(group)
            elif game_state.houses[group][0] > 0:
                roi = self._calculate_upgrade_roi(game_state, group, is_hotel=False)
                if roi < self.house_roi_threshold * 0.7:
                    suggestions.append(group)
                    
        return suggestions

    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        budget = game_state.player_balances[self]
        fine = game_state.board.get_jail_fine()
        
        if budget < fine * 2:
            return False
            
        valuable_properties = sum(1 for p in game_state.properties[self] 
                                if isinstance(p, Property) and 
                                self.calculate_property_value(game_state, p) > p.price * self.property_value_threshold)
        return valuable_properties > self.jail_escape_property_threshold

    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        if game_state.escape_jail_cards[self] == 0:
            return False
            
        valuable_properties = sum(1 for p in game_state.properties[self] 
                                if isinstance(p, Property) and
                                (game_state.houses[p.group][0] > 0 or
                                 game_state.hotels[p.group][0] > 0))
        return valuable_properties > 0
    
    def should_accept_trade_offer(self, game_state, trade_offer: TradeOffer) -> bool:
        """Evaluate whether to accept an incoming trade offer based on strategic value."""
        # Validate trade offer and its components
        if not trade_offer:
            return False
            
        # Initialize with empty lists/values if None
        properties_offered = trade_offer.properties_offered or []
        money_offered = trade_offer.money_offered or 0
        jail_cards_offered = trade_offer.jail_cards_offered or 0
        properties_requested = trade_offer.properties_requested or []
        money_requested = trade_offer.money_requested or 0
        jail_cards_requested = trade_offer.jail_cards_requested or 0

        # Validate we have enough resources for the trade
        if (game_state.player_balances[self] < money_requested or
            game_state.escape_jail_cards[self] < jail_cards_requested):
            return False

        # Verify we actually own the requested properties
        if not all(prop in game_state.properties[self] for prop in properties_requested):
            return False

        # Verify they own the offered properties
        if not all(prop in game_state.properties[trade_offer.source_player] 
                for prop in properties_offered):
            return False

        # Calculate total value of what we're giving up
        value_giving = (
            money_requested +
            (jail_cards_requested * 50) +  # Base value for jail cards
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
                                    if p in game_state.properties[self])
                    if owned_in_group == len(group_properties) - 1:
                        value_receiving *= self.complete_set_multiplier

        for prop in properties_requested:
            if prop is not None and isinstance(prop, Property):
                # Reduce likelihood of breaking existing color sets
                group_properties = game_state.board.get_properties_by_group(prop.group)
                if group_properties:  # Verify group properties exist
                    owned_in_group = sum(1 for p in group_properties 
                                    if p in game_state.properties[self])
                    if owned_in_group == len(group_properties):
                        value_giving *= self.complete_set_multiplier

        # Consider current financial situation
        if game_state.player_balances[self] - money_requested < self.emergency_threshold:
            value_giving *= 1.5  # Increase perceived cost if it puts us in financial danger

        # Strategic adjustment based on other player's position
        if trade_offer.source_player in game_state.properties:
            opponent_properties = len(game_state.properties[trade_offer.source_player])
            our_properties = len(game_state.properties[self])
            if opponent_properties > our_properties * 1.5:  # If they're significantly ahead
                value_receiving *= 1.2  # We're more willing to take risks

        # Final decision with a small margin for positive trades
        return value_receiving > value_giving * 1.1  # 10% margin required for acceptance

    def get_trade_offers(self, game_state) -> List[TradeOffer]:
        """Generate strategic trade offers for other players."""
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
                                if p in game_state.properties[self])
                    if our_count > 0:  # We already have some properties in this group
                        desired_properties.append(prop)

            if not desired_properties:
                continue

            # Calculate what we're willing to offer
            properties_to_offer = []
            money_to_offer = 0
            
            # Look for properties we're willing to trade
            for prop in game_state.properties[self]:
                if prop is not None and isinstance(prop, Property):
                    # Don't offer properties that would break our monopolies
                    group_properties = game_state.board.get_properties_by_group(prop.group)
                    if not group_properties:  # Skip if group properties don't exist
                        continue
                        
                    our_count = sum(1 for p in group_properties 
                                if p in game_state.properties[self])
                    if our_count != len(group_properties):
                        strategic_value = self.calculate_property_value(game_state, prop)
                        if strategic_value < prop.price * self.property_value_threshold:
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
                max_money_offer = game_state.player_balances[self] - self.min_safe_balance
                money_to_offer = min(value_difference, max_money_offer)
                
                if money_to_offer > 0 or properties_to_offer:
                    trade_offers.append(TradeOffer(
                        source_player=self,
                        target_player=target_player,
                        properties_offered=properties_to_offer,
                        money_offered=money_to_offer,
                        properties_requested=desired_properties
                    ))

        return trade_offers