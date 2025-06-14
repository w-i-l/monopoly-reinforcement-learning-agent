from game.player import Player
from models.trade_offer import TradeOffer
from models.railway import Railway
from models.utility import Utility
from models.property import Property
from models.tile import Tile
from typing import List, Optional
from game.game_state import GameState
from game.game_validation import GameValidation
from managers.chance_manager import ChanceManager
from managers.community_chest_manager import CommunityChestManager
from events.events import EventType

CAN_PRINT = False
def custom_print(*args, **kwargs):
    if CAN_PRINT:
        print(*args, **kwargs)

class TradeManager:
    def __init__(self):
        self.active_trades = []
        self.event_manager = None
        

    def set_event_manager(self, event_manager):
        self.event_manager = event_manager


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
            
            # Register trade accepted event
            if self.event_manager:
                self.event_manager.register_event(
                    EventType.TRADE_ACCEPTED,
                    player=trade_offer.source_player,
                    target_player=trade_offer.target_player,
                    additional_data={"trade_offer": trade_offer},
                    description=f"{trade_offer.target_player} accepted trade from {trade_offer.source_player}"
                )
            
            # Execute the trade in game state
            game_state.execute_trade_offer(trade_offer)
            
            # Register detailed events for traded items
            if self.event_manager:
                # Register property events
                if trade_offer.properties_offered:
                    for prop in trade_offer.properties_offered:
                        self.event_manager.register_event(
                            EventType.PROPERTY_PURCHASED,
                            player=trade_offer.target_player,
                            target_player=trade_offer.source_player,
                            tile=prop,
                            amount=0,  # Part of a trade
                            description=f"{trade_offer.target_player} received {prop} from {trade_offer.source_player}"
                        )
                
                if trade_offer.properties_requested:
                    for prop in trade_offer.properties_requested:
                        self.event_manager.register_event(
                            EventType.PROPERTY_PURCHASED,
                            player=trade_offer.source_player,
                            target_player=trade_offer.target_player,
                            tile=prop,
                            amount=0,  # Part of a trade
                            description=f"{trade_offer.source_player} received {prop} from {trade_offer.target_player}"
                        )
                
                # Register money events
                if trade_offer.money_offered:
                    self.event_manager.register_event(
                        EventType.MONEY_PAID,
                        player=trade_offer.source_player,
                        target_player=trade_offer.target_player,
                        amount=trade_offer.money_offered,
                        description=f"{trade_offer.source_player} paid {trade_offer.money_offered}₩ to {trade_offer.target_player}"
                    )
                    
                if trade_offer.money_requested:
                    self.event_manager.register_event(
                        EventType.MONEY_PAID,
                        player=trade_offer.target_player,
                        target_player=trade_offer.source_player,
                        amount=trade_offer.money_requested,
                        description=f"{trade_offer.target_player} paid {trade_offer.money_requested}₩ to {trade_offer.source_player}"
                    )
                
                # Track completion of trade
                self.event_manager.register_event(
                    EventType.TRADE_EXECUTED,
                    player=trade_offer.source_player,
                    target_player=trade_offer.target_player,
                    additional_data={"trade_offer": trade_offer},
                    description=f"Trade completed between {trade_offer.source_player} and {trade_offer.target_player}"
                )

            # Handle jail card transfers
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
                        
                        # Register jail card transfer event
                        if self.event_manager:
                            self.event_manager.register_event(
                                EventType.GET_OUT_OF_JAIL_CARD_USED,
                                player=trade_offer.source_player,
                                target_player=trade_offer.target_player,
                                description=f"{trade_offer.source_player} gave a Chance Get Out of Jail card to {trade_offer.target_player}"
                            )
                            
                    elif community_chest_manager.get_out_of_jail_card_owner == trade_offer.source_player:
                        community_chest_manager.get_out_of_jail_card_owner = trade_offer.target_player
                        
                        # Register jail card transfer event
                        if self.event_manager:
                            self.event_manager.register_event(
                                EventType.GET_OUT_OF_JAIL_CARD_USED,
                                player=trade_offer.source_player,
                                target_player=trade_offer.target_player,
                                description=f"{trade_offer.source_player} gave a Community Chest Get Out of Jail card to {trade_offer.target_player}"
                            )

                elif trade_offer.jail_cards_offered == 2:
                    chance_manager.get_out_of_jail_card_owner = trade_offer.target_player
                    community_chest_manager.get_out_of_jail_card_owner = trade_offer.target_player
                    
                    # Register jail card transfer events
                    if self.event_manager:
                        self.event_manager.register_event(
                            EventType.GET_OUT_OF_JAIL_CARD_USED,
                            player=trade_offer.source_player,
                            target_player=trade_offer.target_player,
                            description=f"{trade_offer.source_player} gave 2 Get Out of Jail cards to {trade_offer.target_player}"
                        )

            elif trade_offer.jail_cards_requested != 0:
                if trade_offer.jail_cards_requested == 1:
                    if chance_manager.get_out_of_jail_card_owner == trade_offer.target_player:
                        chance_manager.get_out_of_jail_card_owner = trade_offer.source_player
                        
                        # Register jail card transfer event
                        if self.event_manager:
                            self.event_manager.register_event(
                                EventType.GET_OUT_OF_JAIL_CARD_USED,
                                player=trade_offer.target_player,
                                target_player=trade_offer.source_player,
                                description=f"{trade_offer.target_player} gave a Chance Get Out of Jail card to {trade_offer.source_player}"
                            )
                            
                    elif community_chest_manager.get_out_of_jail_card_owner == trade_offer.target_player:
                        community_chest_manager.get_out_of_jail_card_owner = trade_offer.source_player
                        
                        # Register jail card transfer event
                        if self.event_manager:
                            self.event_manager.register_event(
                                EventType.GET_OUT_OF_JAIL_CARD_USED,
                                player=trade_offer.target_player,
                                target_player=trade_offer.source_player,
                                description=f"{trade_offer.target_player} gave a Community Chest Get Out of Jail card to {trade_offer.source_player}"
                            )

                elif trade_offer.jail_cards_requested == 2:
                    chance_manager.get_out_of_jail_card_owner = trade_offer.source_player
                    community_chest_manager.get_out_of_jail_card_owner = trade_offer.source_player
                    
                    # Register jail card transfer events
                    if self.event_manager:
                        self.event_manager.register_event(
                            EventType.GET_OUT_OF_JAIL_CARD_USED,
                            player=trade_offer.target_player,
                            target_player=trade_offer.source_player,
                            description=f"{trade_offer.target_player} gave 2 Get Out of Jail cards to {trade_offer.source_player}"
                        )
        else:
            # Register trade rejection event
            if self.event_manager:
                self.event_manager.register_event(
                    EventType.TRADE_REJECTED,
                    player=trade_offer.source_player,
                    target_player=trade_offer.target_player,
                    additional_data={"trade_offer": trade_offer},
                    description=f"{trade_offer.target_player} rejected trade offer from {trade_offer.source_player}"
                )