from game.player import Player
from models.trade_offer import TradeOffer
from models.railway import Railway
from models.utility import Utility
from models.property import Property
from models.tile import Tile
from typing import List
from game.game_state import GameState
from game.game_validation import GameValidation
from chance_manager import ChanceManager
from community_chest_manager import CommunityChestManager


CAN_PRINT = False
def custom_print(*args, **kwargs):
    if CAN_PRINT:
        print(*args, **kwargs)

class TradeManager:
    def __init__(self):
        self.active_trades = []


    def make_trade(self, trade_offer: TradeOffer):
        self.active_trades.append(trade_offer)


    def execute_all_active_trades(self, game_state: GameState):
        for trade in self.active_trades:
            self.execute_trade(trade, game_state)
        self.active_trades = []


    def execute_trade(
            self, 
            trade_offer: TradeOffer,
            game_state: GameState, 
            chance_manager: ChanceManager, 
            community_chest_manager: CommunityChestManager
    ):
        custom_print(f"Checking if trade is valid: {trade_offer}")

        # Check if the trade is valid
        if error := GameValidation.validate_trade_offer(game_state, trade_offer):
            raise error
        
        # Check if the players want to trade
        if trade_offer.target_player.should_accept_trade_offer(game_state, trade_offer):
            custom_print(f"Executing trade: {trade_offer}")
            game_state.execute_trade_offer(trade_offer)

            if trade_offer.jail_cards_offered == trade_offer.jail_cards_requested:
                return # Nothing to do
            
            """ 
            Table for cards offered/requested 
                Source player/Target player | 0 | 1 | 2 |
                ----------------------------------------
                0                           | x | ✓ | ✓ |
                ----------------------------------------
                1                           | ✓ | x | x |
                ----------------------------------------
                2                           | ✓ | x | x |

            x = Invalid trade
            ✓ = Valid trade
            """
            # Update the jail card owner
            if trade_offer.jail_cards_offered != 0:
                if trade_offer.jail_cards_offered == 1:
                    if chance_manager.get_out_of_jail_card_owner == trade_offer.source_player:
                        chance_manager.get_out_of_jail_card_owner = trade_offer.target_player
                    elif community_chest_manager.get_out_of_jail_card_owner == trade_offer.source_player:
                        community_chest_manager.get_out_of_jail_card_owner = trade_offer.target_player

                elif trade_offer.jail_cards_offered == 2:
                    chance_manager.get_out_of_jail_card_owner = trade_offer.target_player
                    community_chest_manager.get_out_of_jail_card_owner = trade_offer.target_player

            elif trade_offer.jail_cards_requested != 0:
                if trade_offer.jail_cards_requested == 1:
                    if chance_manager.get_out_of_jail_card_owner == trade_offer.target_player:
                        chance_manager.get_out_of_jail_card_owner = trade_offer.source_player
                    elif community_chest_manager.get_out_of_jail_card_owner == trade_offer.target_player:
                        community_chest_manager.get_out_of_jail_card_owner = trade_offer.source_player

                elif trade_offer.jail_cards_requested == 2:
                    chance_manager.get_out_of_jail_card_owner = trade_offer.source_player
                    community_chest_manager.get_out_of_jail_card_owner = trade_offer.source_player

       