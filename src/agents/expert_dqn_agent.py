import numpy as np
import tensorflow as tf
import os
from collections import deque
import random
from typing import Dict, List, Tuple, Any, Optional

from agents.default_strategic_player import DefaultStrategicPlayer
from game.game_state import GameState
from models.tile import Tile
from game.game_validation import GameValidation
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.property_group import PropertyGroup

import traceback

class DQNAgent(DefaultStrategicPlayer):
    """
    DQN (Deep Q-Network) agent for Monopoly that inherits from DefaultStrategicPlayer.
    
    This agent uses deep Q-learning to make decisions for various methods,
    including property purchases, upgrading suggestions, downgrading suggestions, and jail fine decisions.
    """
    
    def __init__(
        self,
        name: str,
        state_dim: int = 100,
        hidden_dims: List[int] = [128, 64, 32],
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.1,
        epsilon_decay: float = 0.995,
        epsilon_update_freq = 100,
        target_update_freq: int = 10,
        memory_size: int = 10000,
        batch_size: int = 64,
        strategy_params: Optional[Dict] = None,
        training: bool = True,
        dqn_methods: Dict[str, Optional[str]] = None,
        active_training_method: Optional[str] = None,
        can_use_defaults_methods: dict[str, bool] = None
    ):
        # Initialize parent class
        super().__init__(name, strategy_params, can_be_referenced=True)
        
        # DQN specific parameters
        self.state_dim = state_dim
        self.hidden_dims = hidden_dims
        self.learning_rate = learning_rate
        self.gamma = gamma  # Discount factor
        self.epsilon = epsilon_start  # Exploration rate
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.epsilon_update_freq = epsilon_update_freq
        self.target_update_freq = target_update_freq
        self.batch_size = batch_size
        self.training = training  # Whether the agent is in training mode
        self.update_counter = 0
        self.epsilon_counter = {
            'buy_property': 0,
            'get_upgrading_suggestions': 0,
            'get_downgrading_suggestions': 0,
            'should_pay_get_out_of_jail_fine': 0
        }
        
        # Define which methods should use DQN and which ones inherit from parent
        # Keys are method names, values are either None (use parent) or path to model
        self.dqn_methods = dqn_methods or {
            'buy_property': None,
            'get_upgrading_suggestions': None,
            'get_downgrading_suggestions': None,
            'should_pay_get_out_of_jail_fine': None
        }
        
        # Which method is currently being trained (if any)
        self.active_training_method = active_training_method
        
        # Action spaces for different decisions
        self.action_dims = {
            'buy_property': 2,  # [don't buy, buy]
            'get_upgrading_suggestions': 8,  # [8 color groups]
            'get_downgrading_suggestions': 8,  # [8 color groups]
            'should_pay_get_out_of_jail_fine': 2  # [don't pay, pay]
        }

        self.can_use_defaults_methods = can_use_defaults_methods or {
            'buy_property': False,
            'get_upgrading_suggestions': False,
            'get_downgrading_suggestions': False,
            'should_pay_get_out_of_jail_fine': False
        }
        
        # Network dictionaries to hold separate networks for each decision
        self.q_networks = {}
        self.target_networks = {}
        self.optimizers = {}
        
        # Initialize networks for active methods
        self._init_networks()
        
        # Memory buffer for experience replay - separate for each decision type
        self.memory = {
            'buy_property': deque(maxlen=memory_size),
            'get_upgrading_suggestions': deque(maxlen=memory_size),
            'get_downgrading_suggestions': deque(maxlen=memory_size),
            'should_pay_get_out_of_jail_fine': deque(maxlen=memory_size)
        }
        
        # For tracking decisions during a game
        self.current_decisions = {
            'buy_property': None,
            'get_upgrading_suggestions': None,
            'get_downgrading_suggestions': None,
            'should_pay_get_out_of_jail_fine': None
        }
        
        # Game state reference
        self.game_state = None
    
    def _init_networks(self):
        """Initialize Q-network and target network for each active decision type."""
        try:
            # Initialize or load networks for each method using DQN
            for method, model_path in self.dqn_methods.items():
                # Check if this method should use DQN
                if model_path is not None or method == self.active_training_method:
                    print(f"Initializing networks for method: {method}")
                    # Build networks for this method
                    self.q_networks[method] = self._build_q_network(method)
                    self.target_networks[method] = self._build_q_network(method)
                    
                    # Copy weights from Q-network to target network
                    self.target_networks[method].set_weights(self.q_networks[method].get_weights())
                    
                    # Initialize optimizer
                    self.optimizers[method] = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
                    
                    # Load model if path provided and not in training mode for this method
                    if model_path is not None and method != self.active_training_method:
                        self.load_model_for_method(method, model_path)
            
            print(f"Successfully initialized networks for {self.name}")
            print(f"Active DQN methods: {list(self.q_networks.keys())}")
        except Exception as e:
            print(f"Error initializing networks: {e}")
            import traceback
            traceback.print_exc()

    def _build_q_network(self, decision_type):
        """Build a Q-network for a specific decision type."""
        inputs = tf.keras.layers.Input(shape=(self.state_dim,))
        x = inputs
        
        # Add hidden layers
        for dim in self.hidden_dims:
            x = tf.keras.layers.Dense(dim, activation='relu')(x)
        
        # Output layer - Q values for each action
        outputs = tf.keras.layers.Dense(
            self.action_dims[decision_type],
            activation=None
        )(x)
        
        model = tf.keras.Model(inputs=inputs, outputs=outputs)
        return model
    

    def _calculate_property_value(self, game_state: GameState, property_tile) -> float:
        """
        Robust implementation of property value calculation that doesn't rely on parent class state.
        
        Args:
            game_state: Current game state
            property_tile: The property to evaluate
            
        Returns:
            Calculated property value
        """
        try:
            # Determine which player to use for calculations
            # If self is in game_state.players, use self. Otherwise, use the first player.
            if self in game_state.players:
                current_player = self
            else:
                # In observer mode, use the first player
                current_player = game_state.players[0]
                
            # Get the opponent (if any)
            opponent = None
            for player in game_state.players:
                if player != current_player:
                    opponent = player
                    break
            
            # Base value starts with the property price
            base_value = property_tile.price
            
            # Calculate rent-based value
            if isinstance(property_tile, Property):
                # Value based on rent return
                rent_value = property_tile.full_group_rent * 10  # Approximate 10 rent payments
                
                # Add house/hotel potential
                development_value = 0
                if hasattr(property_tile, 'house_rent') and property_tile.house_rent:
                    development_value += sum(property_tile.house_rent) / len(property_tile.house_rent)
                if hasattr(property_tile, 'hotel_rent'):
                    development_value += property_tile.hotel_rent / 5
                
                # Group completion value - calculate directly
                group_properties = game_state.board.get_properties_by_group(property_tile.group)
                owned_in_group = sum(1 for p in group_properties if p in game_state.properties[current_player])
                total_in_group = len(group_properties)
                
                # Apply multiplier based on how close we are to completing the monopoly
                completion_multiplier = 1.0
                if owned_in_group == total_in_group:
                    # We own all properties in the group
                    completion_multiplier = 1.4
                elif owned_in_group > 0:
                    # We own some properties in the group
                    completion_multiplier = 1.0 + 0.4 * (owned_in_group / total_in_group)
                
                # Location value
                location_multiplier = 1.0
                
                # Orange and red properties (high chance of being landed on from jail)
                if property_tile.group in [PropertyGroup.ORANGE, PropertyGroup.RED]:
                    location_multiplier *= 1.2
                
                # Green and blue properties (high rents)
                elif property_tile.group in [PropertyGroup.GREEN, PropertyGroup.BLUE]:
                    location_multiplier *= 1.1
                
                # Calculate final value
                value = (base_value + rent_value + development_value) * completion_multiplier * location_multiplier
                
            elif isinstance(property_tile, Railway):
                # Count how many railways we already own
                owned_railways = sum(1 for r in game_state.board.get_railways() 
                                    if r in game_state.properties[current_player])
                
                # Calculate expected rent
                if owned_railways == 0:
                    rent_value = property_tile.rent[0] * 10
                elif owned_railways == 1:
                    rent_value = property_tile.rent[1] * 10
                elif owned_railways == 2:
                    rent_value = property_tile.rent[2] * 10
                else:  # 3 railways owned
                    rent_value = property_tile.rent[3] * 10
                
                # Calculate final value
                value = (base_value + rent_value) * 1.3  # Railway multiplier
                
            elif isinstance(property_tile, Utility):
                # Count how many utilities we already own
                owned_utilities = sum(1 for u in game_state.board.get_utilities() 
                                    if u in game_state.properties[current_player])
                
                # Calculate expected rent (approximately)
                # Average dice roll is 7
                if owned_utilities == 0:
                    rent_value = 4 * 7 * 8  # 4 × average roll × ~8 rent payments
                else:  # 1 utility owned
                    rent_value = 10 * 7 * 8  # 10 × average roll × ~8 rent payments
                
                # Calculate final value
                value = (base_value + rent_value) * 1.1  # Utility multiplier
                
            else:
                # Unknown property type
                value = base_value * 1.2  # Default multiplier
            
            return value
            
        except Exception as e:
            # If any error occurs, return a reasonable default
            print(f"Error in custom property value calculation: {e}")
            import traceback
            traceback.print_exc()
            return property_tile.price * 1.2  # Simple fallback value

    def encode_state(self, game_state: GameState, property_tile: Optional[Tile] = None) -> np.ndarray:
        """
        Enhanced state encoding with focus on strategic property development metrics.
        """
        # Determine the current player and opponent
        if self in game_state.players:
            current_player = self
            opponent = next((p for p in game_state.players if p != self), None)
        else:
            # For observer mode
            current_player = game_state.players[0]
            opponent = game_state.players[1] if len(game_state.players) > 1 else None
        
        features = []
        
        # 1. Basic player information (normalized)
        features.append(game_state.player_positions[current_player] / 40.0)
        features.append(game_state.player_positions[opponent] / 40.0 if opponent else 0.0)
        features.append(min(game_state.player_balances[current_player] / 5000.0, 1.0))
        features.append(min(game_state.player_balances[opponent] / 5000.0, 1.0) if opponent else 0.0)
        features.append(float(game_state.in_jail[current_player]))
        features.append(float(game_state.in_jail[opponent]) if opponent else 0.0)
        features.append(game_state.escape_jail_cards[current_player] / 2.0)
        features.append(game_state.escape_jail_cards[opponent] / 2.0 if opponent else 0.0)
        
        # 2. Liquidity ratio - critical for upgrading/downgrading decisions
        total_assets = game_state.get_player_net_worth(current_player)
        cash = game_state.player_balances[current_player]
        liquidity_ratio = cash / max(total_assets, 1.0)  # Avoid division by zero
        features.append(liquidity_ratio)
        
        # 3. Property ownership by group
        all_property_groups = list(PropertyGroup)
        for group in all_property_groups:
            group_properties = game_state.board.get_properties_by_group(group)
            total_in_group = len(group_properties)
            
            if total_in_group > 0:
                # Properties owned in this group
                current_player_owns = sum(1 for p in group_properties if p in game_state.properties[current_player])
                opponent_owns = sum(1 for p in group_properties if opponent and p in game_state.properties[opponent])
                
                # Normalized ownership
                features.append(current_player_owns / total_in_group)
                features.append(opponent_owns / total_in_group)
                
                # Monopoly status - binary feature
                has_monopoly = (current_player_owns == total_in_group)
                features.append(float(has_monopoly))
                
                # Development level 
                if has_monopoly:
                    # Current development level
                    houses = game_state.houses[group][0] if game_state.houses[group][1] == current_player else 0
                    hotels = game_state.hotels[group][0] if game_state.hotels[group][1] == current_player else 0
                    
                    # Normalized development level (0-5 scale where 5 is hotel)
                    development_level = houses
                    if hotels > 0:
                        development_level = 5  # Hotel is level 5
                    
                    features.append(development_level / 5.0)
                    
                    # Strategic value of upgrading
                    if houses < 4 or hotels == 0:
                        # Calculate expected upgrade ROI
                        upgrade_cost = 0
                        rent_increase = 0
                        
                        if houses < 4:  # Can add a house
                            upgrade_cost = group.house_cost() * total_in_group
                            
                            # Estimate rent increase from house
                            for prop in group_properties:
                                if isinstance(prop, Property):
                                    current_rent = prop.house_rent[houses] if houses > 0 else prop.base_rent
                                    next_rent = prop.house_rent[houses] if houses < len(prop.house_rent) else current_rent
                                    rent_increase += (next_rent - current_rent)
                        else:  # Can add a hotel
                            upgrade_cost = group.hotel_cost() * total_in_group
                            
                            # Estimate rent increase from hotel
                            for prop in group_properties:
                                if isinstance(prop, Property):
                                    current_rent = prop.house_rent[-1]
                                    next_rent = prop.hotel_rent
                                    rent_increase += (next_rent - current_rent)
                        
                        # Calculate ROI ratio and landing probability factor
                        roi = rent_increase / max(upgrade_cost, 1.0)
                        
                        # Landing probability factor based on position
                        # Orange and red (high probability from jail) get 1.2x boost
                        if group in [PropertyGroup.ORANGE, PropertyGroup.RED]:
                            roi *= 1.2
                        
                        # Green and blue (high rent) get 1.1x boost
                        elif group in [PropertyGroup.GREEN, PropertyGroup.BLUE]:
                            roi *= 1.1
                        
                        # Normalize ROI to typical range
                        features.append(min(roi / 0.5, 1.0))
                    else:
                        # Fully developed - ROI of adding more is 0
                        features.append(0.0)
                    
                    # Affordability ratio - can we afford to upgrade?
                    if houses < 4:  # House upgrade
                        upgrade_cost = group.house_cost() * total_in_group
                    else:  # Hotel upgrade
                        upgrade_cost = group.hotel_cost() * total_in_group
                    
                    affordability = cash / max(upgrade_cost, 1.0)
                    features.append(min(affordability, 3.0) / 3.0)  # Cap at 3x cash vs cost
                else:
                    # No monopoly - can't develop
                    features.append(0.0)  # development level
                    features.append(0.0)  # ROI
                    features.append(0.0)  # affordability
            else:
                # No properties in this group
                features.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        
        # 4. Railways and utilities
        railways = game_state.board.get_railways()
        utilities = game_state.board.get_utilities()
        
        # Railway ownership (normalized by 4)
        current_player_railways = sum(1 for r in railways if r in game_state.properties[current_player])
        opponent_railways = sum(1 for r in railways if opponent and r in game_state.properties[opponent])
        features.append(current_player_railways / 4.0)
        features.append(opponent_railways / 4.0 if opponent else 0.0)
        
        # Utility ownership (normalized by 2)
        current_player_utilities = sum(1 for u in utilities if u in game_state.properties[current_player])
        opponent_utilities = sum(1 for u in utilities if opponent and u in game_state.properties[opponent])
        features.append(current_player_utilities / 2.0)
        features.append(opponent_utilities / 2.0 if opponent else 0.0)
        
        # 5. Game stage indicator
        total_properties_owned = len(game_state.is_owned)
        features.append(min(total_properties_owned / 28.0, 1.0))  # 28 total properties
        
        # 6. Development summary
        total_houses = sum(1 for group in PropertyGroup if game_state.houses[group][1] == current_player)
        total_hotels = sum(1 for group in PropertyGroup if game_state.hotels[group][1] == current_player)
        features.append(min(total_houses / 32.0, 1.0))  # Max 32 houses
        features.append(min(total_hotels / 12.0, 1.0))  # Max 12 hotels
        
        # 7. Property-specific features (only for buying decisions)
        if property_tile:
            # Property ID
            features.append(property_tile.id / 40.0)
            
            # Property price
            property_price = getattr(property_tile, 'price', 0)
            features.append(min(property_price / 400.0, 1.0))
            
            # Property type encoding
            features.append(float(isinstance(property_tile, Property)))
            features.append(float(isinstance(property_tile, Railway)))
            features.append(float(isinstance(property_tile, Utility)))
            
            # Strategic value
            if property_price > 0:
                value = self._calculate_property_value(game_state, property_tile)
                value_to_cost_ratio = value / property_price
                features.append(min(value_to_cost_ratio / 2.0, 1.0))  # Normalize to 0-1
            else:
                features.append(0.0)
                
            # Affordability
            affordability = cash / max(property_price, 1.0)
            features.append(min(affordability, 5.0) / 5.0)  # Cap at 5x cash vs cost
        else:
            # Fill with zeros if no property
            features.extend([0.0] * 7)
        
        # 8. Jail-specific features (for jail fine decisions)
        jail_position = game_state.board.get_jail_id()
        jail_fine = game_state.board.get_jail_fine()
        
        # Distance-based danger assessment (spaces 6-9 from jail are high-traffic)
        danger_score = 0.0
        for steps in range(2, 13):  # Possible dice rolls
            landing_position = (jail_position + steps) % 40
            tile = game_state.board.tiles[landing_position]
            
            # Calculate danger for this tile
            tile_danger = 0.0
            if isinstance(tile, (Property, Railway, Utility)) and tile in game_state.is_owned:
                # Find the owner
                for player in game_state.players:
                    if player != current_player and tile in game_state.properties[player]:
                        # Estimate rent
                        if isinstance(tile, Property):
                            # Get rent based on development
                            if tile.group in game_state.hotels and game_state.hotels[tile.group][0] > 0:
                                rent = tile.hotel_rent
                            elif tile.group in game_state.houses and game_state.houses[tile.group][0] > 0:
                                houses = game_state.houses[tile.group][0]
                                rent = tile.house_rent[houses-1] if houses <= len(tile.house_rent) else tile.house_rent[-1]
                            else:
                                # Check if player has monopoly
                                group_props = game_state.board.get_properties_by_group(tile.group)
                                if all(p in game_state.properties[player] for p in group_props):
                                    rent = tile.full_group_rent
                                else:
                                    rent = tile.base_rent
                        elif isinstance(tile, Railway):
                            # Count railways owned by opponent
                            railways_owned = sum(1 for r in railways if r in game_state.properties[player])
                            rent = tile.rent[railways_owned-1] if railways_owned > 0 else 0
                        elif isinstance(tile, Utility):
                            # Estimate utility rent (average dice roll * multiplier)
                            utilities_owned = sum(1 for u in utilities if u in game_state.properties[player])
                            rent = 7 * (4 if utilities_owned == 1 else 10)
                        
                        # Normalize danger by cash available
                        tile_danger = min(rent / max(cash, 1), 1.0)
                        break
            
            # Weight by probability of rolling this number
            prob = (6 - abs(7 - steps)) / 36.0 if 2 <= steps <= 12 else 0
            danger_score += tile_danger * prob
        
        features.append(danger_score)
        
        # Jail fine affordability
        jail_fine_affordability = cash / max(jail_fine, 1.0)
        features.append(min(jail_fine_affordability, 5.0) / 5.0)
        
        # Turn in jail (if available in game state)
        turns_in_jail = getattr(game_state, 'turns_in_jail', {}).get(current_player, 0)
        features.append(min(turns_in_jail / 3.0, 1.0))  # Max 3 turns
        
        # Ensure we have exactly state_dim features
        assert len(features) <= self.state_dim, f"Feature count {len(features)} exceeds state_dim {self.state_dim}"
        
        # Pad if necessary
        if len(features) < self.state_dim:
            features.extend([0.0] * (self.state_dim - len(features)))
        
        return np.array(features, dtype=np.float32)
    
    def calculate_reward(self, 
                game_state: GameState,
                player,
                next_game_state: Optional[GameState] = None,
                done: bool = False,
                decision_type: str = 'buy_property') -> float:
        """
        Enhanced reward function that better captures strategic value.
        """
        # Calculate current net worth
        current_net_worth = game_state.get_player_net_worth(player)
        
        # If next state is available, calculate change in net worth
        if next_game_state:
            next_net_worth = next_game_state.get_player_net_worth(player)
            net_worth_change = next_net_worth - current_net_worth
            
            # Base reward on net worth change, normalized
            normalized_change = np.clip(net_worth_change / 200.0, -1.0, 1.0)
            
            # Additional reward components based on decision type
            if decision_type == 'buy_property':
                # For property buying, focus on immediate strategic value
                base_reward = normalized_change
                
                # Bonus for completing monopoly groups
                current_monopolies = sum(1 for group in PropertyGroup 
                                        if all(p in game_state.properties[player] 
                                            for p in game_state.board.get_properties_by_group(group)))
                
                next_monopolies = sum(1 for group in PropertyGroup 
                                    if all(p in next_game_state.properties[player] 
                                            for p in next_game_state.board.get_properties_by_group(group)))
                
                if next_monopolies > current_monopolies:
                    base_reward += 0.3  # Strong incentive for completing monopolies
                    
            elif decision_type == 'get_upgrading_suggestions':
                # For upgrading, focus on future value
                base_reward = normalized_change * 1.5  # Higher multiplier
                
                # Calculate development changes
                prev_houses = sum(count for group, (count, owner) in game_state.houses.items() 
                                if owner == player)
                current_houses = sum(count for group, (count, owner) in next_game_state.houses.items() 
                                    if owner == player)
                
                prev_hotels = sum(count for group, (count, owner) in game_state.hotels.items() 
                                if owner == player)
                current_hotels = sum(count for group, (count, owner) in next_game_state.hotels.items() 
                                    if owner == player)
                
                # Reward for strategic development
                if current_houses > prev_houses:
                    # Houses were added
                    house_increase = current_houses - prev_houses
                    base_reward += 0.15 * house_increase  # Moderate bonus per house
                
                if current_hotels > prev_hotels:
                    # Hotels were added
                    hotel_increase = current_hotels - prev_hotels
                    base_reward += 0.3 * hotel_increase  # Strong bonus per hotel
                
                # Liquidity penalty - too much spending can be risky
                current_liquidity = game_state.player_balances[player] / max(game_state.get_player_net_worth(player), 1)
                next_liquidity = next_game_state.player_balances[player] / max(next_game_state.get_player_net_worth(player), 1)
                
                if next_liquidity < 0.1 and next_liquidity < current_liquidity:
                    # Dangerously low liquidity
                    base_reward -= 0.2  # Penalty for risking bankruptcy
                    
            elif decision_type == 'get_downgrading_suggestions':
                # For downgrading, focus on cash management and financial stability
                base_reward = normalized_change * 0.8  # Lower multiplier since we're losing assets
                
                # Calculate development changes
                prev_houses = sum(count for group, (count, owner) in game_state.houses.items() 
                                if owner == player)
                current_houses = sum(count for group, (count, owner) in next_game_state.houses.items() 
                                    if owner == player)
                
                prev_hotels = sum(count for group, (count, owner) in game_state.hotels.items() 
                                if owner == player)
                current_hotels = sum(count for group, (count, owner) in next_game_state.hotels.items() 
                                    if owner == player)
                
                # Cash situation analysis
                prev_cash = game_state.player_balances[player]
                current_cash = next_game_state.player_balances[player]
                cash_increase = current_cash - prev_cash
                
                # If development was reduced (houses/hotels sold)
                if current_houses < prev_houses or current_hotels < prev_hotels:
                    # Good decision if we needed cash and got it
                    if prev_cash < 200:  # Was in financial trouble
                        base_reward += 0.3  # Reward for emergency cash management
                    elif prev_cash < 500:  # Moderate financial stress
                        base_reward += 0.15  # Moderate reward
                    else:
                        # Had plenty of cash - downgrading might be premature
                        base_reward -= 0.1  # Small penalty
                    
                    # Bonus for raising significant cash
                    if cash_increase > 100:
                        base_reward += min(cash_increase / 500.0, 0.2)  # Up to 0.2 bonus
                
                # Penalty for downgrading high-value monopolies unnecessarily
                for group in PropertyGroup:
                    if (game_state.houses.get(group, [0, None])[1] == player and 
                        next_game_state.houses.get(group, [0, None])[0] < game_state.houses.get(group, [0, None])[0]):
                        # This group was downgraded
                        if group in [PropertyGroup.ORANGE, PropertyGroup.RED]:
                            # High-traffic groups - more penalty for downgrading
                            base_reward -= 0.1
                        elif group in [PropertyGroup.GREEN, PropertyGroup.BLUE]:
                            # High-rent groups - penalty for downgrading
                            base_reward -= 0.08
                
                # Reward for improved liquidity ratio
                prev_liquidity = prev_cash / max(game_state.get_player_net_worth(player), 1)
                current_liquidity = current_cash / max(next_game_state.get_player_net_worth(player), 1)
                
                if current_liquidity > prev_liquidity and prev_liquidity < 0.15:
                    # Improved liquidity from dangerous level
                    base_reward += 0.2
                    
            elif decision_type == 'should_pay_get_out_of_jail_fine':
                # For jail fine decisions, focus on cash preservation vs mobility trade-off
                base_reward = normalized_change
                
                # Factor in cash management
                current_cash = game_state.player_balances[player]
                next_cash = next_game_state.player_balances[player]
                cash_change = next_cash - current_cash
                
                # If we paid (cash decreased significantly)
                if cash_change < -40:  # Assuming jail fine is around 50
                    # Reward based on whether we had enough cash to spare
                    if current_cash > 500:
                        base_reward += 0.1  # Could afford it, mobility might be worth it
                    else:
                        base_reward -= 0.1  # Maybe too expensive given cash situation
                        
                    # Bonus if getting out led to profitable moves
                    if net_worth_change > 0:
                        base_reward += 0.2  # Getting out was profitable
                else:
                    # We stayed in jail (cash preserved)
                    if current_cash < 300:
                        base_reward += 0.15  # Good to save cash when low
                    elif current_cash > 800:
                        base_reward -= 0.1  # Maybe missed opportunities with high cash
                
                # Consider board danger - staying in jail can be strategic when board is dangerous
                # This is a simplified danger assessment
                danger_score = self._assess_board_danger_simple(game_state, player)
                if danger_score > 0.6:  # High danger
                    if cash_change >= -10:  # Stayed in jail
                        base_reward += 0.1  # Good decision to stay in dangerous situation
                    else:  # Paid to get out
                        base_reward -= 0.1  # Risky decision in dangerous situation
            else:
                # Default case
                base_reward = normalized_change
            
            # Terminal state bonus/penalty
            if done:
                # Check if player won
                is_winner = True
                for other_player in next_game_state.players:
                    if other_player != player and next_game_state.player_balances[other_player] >= 0:
                        is_winner = False
                        break
                
                if is_winner:
                    return 1.0  # Win
                elif next_game_state.player_balances[player] < 0:
                    return -1.0  # Loss due to bankruptcy
            
            return base_reward
        
        # If no next state, return small positive reward for valid actions
        return 0.1

    def _assess_board_danger_simple(self, game_state: GameState, player) -> float:
        """
        Simplified board danger assessment for jail decisions.
        
        Args:
            game_state: Current game state
            player: Player to assess danger for
            
        Returns:
            Danger score between 0-1 (higher means more dangerous)
        """
        current_position = game_state.player_positions[player]
        
        danger_score = 0
        checks = 0
        
        # Check next 10 spaces for basic danger assessment
        for steps in range(1, 11):
            next_position = (current_position + steps) % 40
            tile = game_state.board.tiles[next_position]
            
            # Simple danger calculation
            if isinstance(tile, Property) and tile in game_state.is_owned and tile not in game_state.properties[player]:
                # Property owned by opponent - assume average rent of 100
                danger_score += min(100 / (game_state.player_balances[player] + 1), 1.0)
            elif isinstance(tile, Railway) and tile in game_state.is_owned and tile not in game_state.properties[player]:
                # Railway owned by opponent - assume average rent of 100
                danger_score += min(100 / (game_state.player_balances[player] + 1), 1.0)
            elif isinstance(tile, Utility) and tile in game_state.is_owned and tile not in game_state.properties[player]:
                # Utility owned by opponent - assume average rent of 70
                danger_score += min(70 / (game_state.player_balances[player] + 1), 1.0)
                
            checks += 1
        
        return danger_score / checks if checks > 0 else 0
    
    def should_buy_property(self, game_state: GameState, property_tile: Tile) -> bool:
        """
        Decide whether to buy a property using the DQN policy.
        
        Args:
            game_state: Current game state
            property_tile: The property tile being considered
            
        Returns:
            True if the agent decides to buy, False otherwise
        """
        # First validate we can buy this property
        if error := GameValidation.validate_buy_property(game_state, self, property_tile):
            return False
        
        # Check if it's a valid property type
        if not (isinstance(property_tile, Property) or 
                isinstance(property_tile, Railway) or 
                isinstance(property_tile, Utility)):
            return False
        
        # Check if we should use DQN for this method
        method = 'buy_property'
        if method not in self.q_networks:
            if not self.can_use_defaults_methods[method]:
                print(self.q_networks)
                print(self.can_use_defaults_methods)
                print(f"Using parent class implementation for {method}")
                exit(-1)
            # Use parent class implementation
            return super().should_buy_property(game_state, property_tile)

        # Update epsilon counter for this method
        self.epsilon_counter[method] += 1

        try:
            # Encode the state with property information
            state = self.encode_state(game_state, property_tile)
            state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
            
            # Get Q-values for the state
            q_values = self.q_networks[method](state_tensor)[0].numpy()
            
            # Determine action
            if self.training and (method == self.active_training_method):
                # Epsilon-greedy in training mode
                if np.random.random() < self.epsilon:
                    action = int(np.random.random() > 0.5)  # Random binary decision
                else:
                    action = int(q_values[1] > q_values[0])  # Buy if Q(buy) > Q(don't buy)
                
                # Store decision for future reward calculation
                self.current_decisions[method] = {
                    'state': state,
                    'action': action,
                    'property_id': property_tile.id,
                    'game_state': game_state
                }
                
                # Decay epsilon occasionally
                if self.epsilon_counter[method] % self.epsilon_update_freq == 0:
                    self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
            else:
                # Pure exploitation in evaluation mode
                action = int(q_values[1] > q_values[0])  # Buy if Q(buy) > Q(don't buy)
            
            return bool(action)  # 0 = don't buy, 1 = buy
        
        except Exception as e:
            print(f"Error in should_buy_property: {e}")
            traceback.print_exc()
            
            # Fall back to random decision with a penalty in training mode
            if self.training and (method == self.active_training_method):
                # Add a negative experience to penalize errors
                try:
                    state = self.encode_state(game_state, property_tile)
                    action = np.random.randint(0, 2)  # Random action
                    self.memory[method].append((
                        state,
                        action,
                        -0.5,  # Penalty for error
                        state,  # Same state as next_state since we don't have a real transition
                        True  # Treat as a terminal state
                    ))
                except:
                    pass
                
            # Fall back to parent implementation
            return super().should_buy_property(game_state, property_tile)

    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        """
        Decide which property groups to upgrade using the DQN policy.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of PropertyGroup to upgrade
        """
        # Check if we should use DQN for this method
        method = 'get_upgrading_suggestions'
        if method not in self.q_networks:
            if not self.can_use_defaults_methods[method]:
                print(f"Using parent class implementation for {method}")
                print(self.q_networks)
                print(self.can_use_defaults_methods)
                exit(-1)
            # Use parent class implementation
            return super().get_upgrading_suggestions(game_state)
        
        # Update epsilon counter for this method
        self.epsilon_counter[method] += 1

        try:
            # Encode the state
            state = self.encode_state(game_state)
            state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
            
            # Get Q-values for each property group
            q_values = self.q_networks[method](state_tensor)
            
            # Filter valid property groups (those we own completely and can build on)
            valid_groups = []
            group_indices = {}
            
            for i, group in enumerate(PropertyGroup):
                # Group is valid if EITHER houses OR hotels can be placed
                house_valid = not GameValidation.validate_place_house(game_state, self, group)
                hotel_valid = not GameValidation.validate_place_hotel(game_state, self, group)
                
                if house_valid or hotel_valid:
                    valid_groups.append(group)
                group_indices[group] = i
            

            # In training mode, use epsilon-greedy policy
            selected_group = None
            if self.training and (method == self.active_training_method):
                if np.random.random() < self.epsilon:
                    # Random valid group or none
                    if valid_groups:
                        selected_group = np.random.choice(valid_groups)
                        action = group_indices[selected_group]
                    else:
                        # Return empty list (no upgrades)
                        action = -1  # Special code for no upgrades
                else:
                    # Select the group with highest Q-value among valid groups
                    if valid_groups:
                        valid_q_values = [(group_indices[g], q_values[0][group_indices[g]]) for g in valid_groups]
                        best_idx, _ = max(valid_q_values, key=lambda x: x[1])
                        action = best_idx
                    else:
                        # No valid groups
                        action = -1
                
                # Store the current decision for future reward
                self.current_decisions[method] = {
                    'state': state,
                    'action': action,
                    'game_state': game_state
                }
                
                # Decay epsilon
                if self.epsilon_counter[method] % self.epsilon_update_freq == 0:
                    self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
            else:
                # In evaluation mode, select the group with highest Q-value among valid groups
                if valid_groups:
                    valid_q_values = [(group_indices[g], q_values[0][group_indices[g]]) for g in valid_groups]
                    best_idx, _ = max(valid_q_values, key=lambda x: x[1])
                    action = best_idx
                else:
                    # No valid groups
                    action = -1
            
            for group, idx in group_indices.items():
                if idx == action:
                    selected_group = group
                    break

            if selected_group and selected_group in valid_groups:
                can_be_added = False
                # If we can place a house OR a hotel, add the group
                if not GameValidation.validate_place_house(game_state=game_state, player=self, property_group=selected_group):
                    can_be_added = True
                elif not GameValidation.validate_place_hotel(game_state=game_state, player=self, property_group=selected_group):
                    can_be_added = True
                if can_be_added:
                    return [selected_group]
            
            # If no valid group selected, return empty list
            return []
        
        except Exception as e:
            print(f"Error in get_upgrading_suggestions: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to empty list with a penalty in training mode
            if self.training and (method == self.active_training_method):
                try:
                    state = self.encode_state(game_state)
                    action = -1  # No upgrade
                    self.memory[method].append((
                        state,
                        action,
                        -0.5,  # Penalty for error
                        state,  # Same state as next_state since we don't have a real transition
                        True  # Treat as a terminal state
                    ))
                except:
                    pass
            
            # Fall back to parent implementation
            return super().get_upgrading_suggestions(game_state)

    
    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        """
        Decide whether to pay the fine to get out of jail using the DQN policy.
        
        Args:
            game_state: Current game state
            
        Returns:
            True if the agent decides to pay the fine, False otherwise
        """
        # First validate we're actually in jail and can pay
        if error := GameValidation.validate_pay_get_out_of_jail_fine(game_state, self):
            # If validation fails, we can't pay - return False
            return False
        
        # Additional safety check - make sure we have enough money
        jail_fine = game_state.board.get_jail_fine()
        if game_state.player_balances[self] < jail_fine:
            return False
        
        # Check if we should use DQN for this method
        method = 'should_pay_get_out_of_jail_fine'
        if method not in self.q_networks:
            if not self.can_use_defaults_methods[method]:
                print(f"Using parent class implementation for {method}")
                print(self.q_networks)
                print(self.can_use_defaults_methods)
                exit(-1)
            # Use parent class implementation
            return super().should_pay_get_out_of_jail_fine(game_state)

        # Update epsilon counter for this method
        if method not in self.epsilon_counter:
            self.epsilon_counter[method] = 0
        self.epsilon_counter[method] += 1

        try:
            # Encode the state
            state = self.encode_state(game_state)
            state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
            
            # Get Q-values for the state
            q_values = self.q_networks[method](state_tensor)[0].numpy()
            
            # Determine action
            if self.training and (method == self.active_training_method):
                # Epsilon-greedy in training mode
                if np.random.random() < self.epsilon:
                    action = int(np.random.random() > 0.5)  # Random binary decision
                else:
                    action = int(q_values[1] > q_values[0])  # Pay if Q(pay) > Q(don't pay)
                
                # Store decision for future reward calculation
                self.current_decisions[method] = {
                    'state': state,
                    'action': action,
                    'game_state': game_state,
                    'jail_fine': jail_fine,
                    'cash_before': game_state.player_balances[self]
                }
                
                # Decay epsilon occasionally
                if self.epsilon_counter[method] % self.epsilon_update_freq == 0:
                    self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
            else:
                # Pure exploitation in evaluation mode
                action = int(q_values[1] > q_values[0])  # Pay if Q(pay) > Q(don't pay)
            
            return bool(action)  # 0 = don't pay, 1 = pay
        
        except Exception as e:
            print(f"Error in should_pay_get_out_of_jail_fine: {e}")
            import traceback
            traceback.print_exc()
            
            # Fall back to a simple heuristic
            # Pay if we have more than 3x the jail fine
            return random.choice([True, False])
        

    def get_downgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        """
        Decide which property groups to downgrade using the DQN policy.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of PropertyGroup to downgrade
        """
        # Check if we should use DQN for this method
        method = 'get_downgrading_suggestions'
        if method not in self.q_networks:
            if not self.can_use_defaults_methods[method]:
                print(f"Using parent class implementation for {method}")
                print(self.q_networks)
                print(self.can_use_defaults_methods)
                exit(-1)
            # Use parent class implementation
            return super().get_downgrading_suggestions(game_state)
        
        if super().get_downgrading_suggestions(game_state) == []:
            # If parent implementation returns empty, we can't downgrade
            return []

        # Update epsilon counter for this method
        if method not in self.epsilon_counter:
            self.epsilon_counter[method] = 0
        self.epsilon_counter[method] += 1
        print(f"Using DQN for {method}")

        try:
            # Encode the state
            state = self.encode_state(game_state)
            state_tensor = tf.convert_to_tensor([state], dtype=tf.float32)
            
            # Get Q-values for each property group
            q_values = self.q_networks[method](state_tensor)
            
            # Filter valid property groups (those we own completely and can downgrade)
            valid_groups = []
            group_indices = {}
            
            for i, group in enumerate(PropertyGroup):
                # Group is valid if EITHER houses OR hotels can be sold
                house_valid = not GameValidation.validate_sell_house(game_state, self, group)
                hotel_valid = not GameValidation.validate_sell_hotel(game_state, self, group)
                
                if house_valid or hotel_valid:
                    valid_groups.append(group)
                group_indices[group] = i
            
            # In training mode, use epsilon-greedy policy
            selected_group = None
            if self.training and (method == self.active_training_method):
                if np.random.random() < self.epsilon:
                    # Random valid group or none
                    if valid_groups:
                        selected_group = np.random.choice(valid_groups)
                        action = group_indices[selected_group]
                    else:
                        # Return empty list (no downgrades)
                        action = -1  # Special code for no downgrades
                else:
                    # Select the group with highest Q-value among valid groups
                    if valid_groups:
                        valid_q_values = [(group_indices[g], q_values[0][group_indices[g]]) for g in valid_groups]
                        best_idx, _ = max(valid_q_values, key=lambda x: x[1])
                        action = best_idx
                    else:
                        # No valid groups
                        action = -1
                
                # Store the current decision for future reward
                self.current_decisions[method] = {
                    'state': state,
                    'action': action,
                    'game_state': game_state
                }
                
                # Decay epsilon
                if self.epsilon_counter[method] % self.epsilon_update_freq == 0:
                    self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
            else:
                # In evaluation mode, select the group with highest Q-value among valid groups
                if valid_groups:
                    valid_q_values = [(group_indices[g], q_values[0][group_indices[g]]) for g in valid_groups]
                    best_idx, _ = max(valid_q_values, key=lambda x: x[1])
                    action = best_idx
                else:
                    # No valid groups
                    action = -1
            
            for group, idx in group_indices.items():
                if idx == action:
                    selected_group = group
                    break

            if selected_group and selected_group in valid_groups:
                can_be_added = False
                # If we can sell a house OR a hotel, add the group
                if not GameValidation.validate_sell_house(game_state=game_state, player=self, property_group=selected_group):
                    can_be_added = True
                elif not GameValidation.validate_sell_hotel(game_state=game_state, player=self, property_group=selected_group):
                    can_be_added = True
                if can_be_added:
                    return [selected_group]
            
            # If no valid group selected, return empty list
            return []
        
        except Exception as e:
            print(f"Error in get_downgrading_suggestions: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to empty list with a penalty in training mode
            if self.training and (method == self.active_training_method):
                try:
                    state = self.encode_state(game_state)
                    action = -1  # No downgrade
                    self.memory[method].append((
                        state,
                        action,
                        -0.5,  # Penalty for error
                        state,  # Same state as next_state since we don't have a real transition
                        True  # Treat as a terminal state
                    ))
                except:
                    pass
            
            # Fall back to parent implementation
            return super().get_downgrading_suggestions(game_state)

        
    def update_decision(self, method: str, next_game_state: GameState, done: bool = False):
        """
        Update a decision with its reward and add to memory.
        
        Args:
            method: The decision method to update
            next_game_state: The next game state
            done: Whether the game is done
        """
        if method in self.current_decisions and self.current_decisions[method]:
            try:
                # Calculate reward
                reward = self.calculate_reward(
                    self.current_decisions[method]['game_state'],
                    self,
                    next_game_state,
                    done,
                    method
                )
                
                # Encode the next state
                next_state = self.encode_state(next_game_state)
                
                # Add to memory
                self.memory[method].append((
                    self.current_decisions[method]['state'],
                    self.current_decisions[method]['action'],
                    reward,
                    next_state,
                    float(done)
                ))
                
                # Reset current decision
                self.current_decisions[method] = None
                
                # Train if we have enough samples
                if len(self.memory[method]) >= self.batch_size:
                    self.train_on_batch(method)
            
            except Exception as e:
                print(f"Error updating {method} decision: {e}")
                self.current_decisions[method] = None

    def train_on_batch(self, method: str):
        """
        Train the networks for a specific method using a random batch from memory.
        
        Args:
            method: The decision method to train
        """
        if method not in self.q_networks or method not in self.memory:
            return
            
        if len(self.memory[method]) < self.batch_size:
            return
        
        # Sample a batch of experiences
        indices = np.random.choice(
            len(self.memory[method]), 
            self.batch_size, 
            replace=False
        )
        
        states = []
        actions = []
        rewards = []
        next_states = []
        dones = []
        
        for idx in indices:
            experience = self.memory[method][idx]
            state, action, reward, next_state, done = experience
            
            # Handle special case for get_upgrading_suggestions where -1 means no upgrade
            if method == 'get_upgrading_suggestions' and action == -1:
                # Map to a valid action index (we'll use the last action)
                action = self.action_dims[method] - 1
            
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            next_states.append(next_state)
            dones.append(done)
        
        states = np.array(states)
        actions = np.array(actions, dtype=np.int32)
        rewards = np.array(rewards, dtype=np.float32)
        next_states = np.array(next_states)
        dones = np.array(dones, dtype=np.float32)
        
        # Convert to tensors
        states_tensor = tf.convert_to_tensor(states, dtype=tf.float32)
        actions_tensor = tf.convert_to_tensor(actions, dtype=tf.int32)
        rewards_tensor = tf.convert_to_tensor(rewards, dtype=tf.float32)
        next_states_tensor = tf.convert_to_tensor(next_states, dtype=tf.float32)
        dones_tensor = tf.convert_to_tensor(dones, dtype=tf.float32)
        
        # Training step
        with tf.GradientTape() as tape:
            # Current Q-values
            q_values = self.q_networks[method](states_tensor)
            
            # Get Q-values for the actions taken
            action_masks = tf.one_hot(actions_tensor, depth=self.action_dims[method])
            q_values_for_actions = tf.reduce_sum(q_values * action_masks, axis=1)
            
            # Target Q-values
            next_q_values = self.target_networks[method](next_states_tensor)
            next_q_values_max = tf.reduce_max(next_q_values, axis=1)
            
            # Compute targets
            targets = rewards_tensor + (1.0 - dones_tensor) * self.gamma * next_q_values_max
            
            # Compute loss (using Huber loss for stability)
            loss = tf.keras.losses.Huber()(targets, q_values_for_actions)
        
        # Get gradients and apply updates
        gradients = tape.gradient(loss, self.q_networks[method].trainable_variables)
        self.optimizers[method].apply_gradients(zip(gradients, self.q_networks[method].trainable_variables))
        
        # Update target network periodically
        self.update_counter += 1
        if self.update_counter % self.target_update_freq == 0:
            self.target_networks[method].set_weights(self.q_networks[method].get_weights())
        
        return loss.numpy()  # Return loss value for tracking

    def save_model_for_method(self, method: str, path: str):
        """
        Save network and parameters for a specific method to disk.
        
        Args:
            method: The decision method
            path: Base path to save the model
        """
        if method not in self.q_networks:
            print(f"No model to save for method {method}")
            return
            
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save Q-network
        self.q_networks[method].save_weights(f"{path}_{method}_q_network")
        
        # Save target network
        self.target_networks[method].save_weights(f"{path}_{method}_target_network")
        
        # Save parameters
        params = {
            'state_dim': self.state_dim,
            'hidden_dims': self.hidden_dims,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'epsilon_end': self.epsilon_end,
            'epsilon_decay': self.epsilon_decay,
            'target_update_freq': self.target_update_freq,
            'batch_size': self.batch_size,
            'action_dims': self.action_dims
        }
        
        import json
        with open(f"{path}_{method}_params.json", 'w') as f:
            json.dump(params, f)
        
        print(f"Model for method {method} saved to {path}")

    def load_model_for_method(self, method: str, path: str):
        """
        Load network and parameters for a specific method from disk.
        
        Args:
            method: The decision method
            path: Base path to load the model from
        """
        import json
        
        try:
            # Load parameters
            with open(f"{path}_{method}_params.json", 'r') as f:
                params = json.load(f)
            
            # Update agent parameters
            # Note: We only update method-specific parameters, not global ones
            if method not in self.q_networks:
                print(f"Initializing networks for method {method}...")
                # Initialize networks if they don't exist
                self.q_networks[method] = self._build_q_network(method)
                self.target_networks[method] = self._build_q_network(method)
                self.optimizers[method] = tf.keras.optimizers.Adam(learning_rate=self.learning_rate)
            
            # Load network weights
            self.q_networks[method].load_weights(f"{path}_{method}_q_network")
            self.target_networks[method].load_weights(f"{path}_{method}_target_network")
            
            # Update dqn_methods to mark this method as using DQN
            self.dqn_methods[method] = path
            
            print(f"Model for method {method} loaded from {path}")
            print(f"q_networks now contains: {list(self.q_networks.keys())}")
            print(f"q-network for {method}: {self.q_networks[method]}")
            
        except Exception as e:
            print(f"Error loading model for method {method}: {e}")
            import traceback
            traceback.print_exc()

    def save_model(self, path):
        """
        Save all networks and parameters to disk.
        
        Args:
            path: Base path to save the models
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save common parameters
        params = {
            'state_dim': self.state_dim,
            'hidden_dims': self.hidden_dims,
            'learning_rate': self.learning_rate,
            'gamma': self.gamma,
            'epsilon': self.epsilon,
            'epsilon_end': self.epsilon_end,
            'epsilon_decay': self.epsilon_decay,
            'target_update_freq': self.target_update_freq,
            'batch_size': self.batch_size,
            'action_dims': self.action_dims,
            'active_methods': list(self.q_networks.keys())
        }
        
        import json
        with open(f"{path}_global_params.json", 'w') as f:
            json.dump(params, f)
        
        # Save each method's networks
        for method in self.q_networks:
            self.save_model_for_method(method, path)
        
        print(f"All models saved to {path}")

    def load_model(self, path):
        """
        Load all networks and parameters from disk.
        
        Args:
            path: Base path to load the models from
        """
        import json
        
        try:
            # Load global parameters
            with open(f"{path}_global_params.json", 'r') as f:
                params = json.load(f)
            
            # Update agent parameters
            self.state_dim = params['state_dim']
            self.hidden_dims = params['hidden_dims']
            self.learning_rate = params['learning_rate']
            self.gamma = params['gamma']
            self.epsilon = params['epsilon']
            self.epsilon_end = params['epsilon_end']
            self.epsilon_decay = params['epsilon_decay']
            self.target_update_freq = params['target_update_freq']
            self.batch_size = params['batch_size']
            self.action_dims = params['action_dims']
            
            # Load each method's networks
            active_methods = params.get('active_methods', ['buy_property'])
            for method in active_methods:
                self.dqn_methods[method] = path  # Mark as using DQN
                self.load_model_for_method(method, path)
            
            print(f"All models loaded from {path}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            import traceback
            traceback.print_exc()