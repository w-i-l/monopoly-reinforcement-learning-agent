from models.property import Tile
from models.property_group import PropertyGroup
from typing import List, Dict, Optional

# TODO: Allow player to upgrade/downgrade any number of times
# eg. buy 2 houses on one property and 1 house on another, instead of buying one house per call

class Player:
    def __init__(self, name):
        self.name = name

        self.event_queue = []
        self.event_history = []
        self.max_history = 100

    def __repr__(self):
        return f"{self.name}"
    
    def should_buy_property(self, game_state, property: Tile) -> bool:
        # TODO: Implement the logic to decide if the player should buy the property
        return True
    
    def get_upgrading_suggestions(self, game_state) -> List[PropertyGroup]:
        # TODO: Implement the logic to suggest which properties to upgrade
        return []
    
    def get_mortgaging_suggestions(self, game_state) -> List[Tile]:
        # TODO: Implement the logic to suggest which properties to mortgage
        return []
    
    def get_unmortgaging_suggestions(self, game_state) -> List[Tile]:
        # TODO: Implement the logic to suggest which properties to unmortgage
        return []
    
    def get_downgrading_suggestions(self, game_state) -> List[Tile]:
        # TODO: Implement the logic to suggest which properties to downgrade
        return []
    
    def should_pay_get_out_of_jail_fine(self, game_state) -> bool:
        # TODO: Implement the logic to decide if the player should pay the fine to get out of jail
        return True
    
    def should_use_escape_jail_card(self, game_state) -> bool:
        # TODO: Implement the logic to decide if the player should use the get out of jail free card
        return True
    
    def should_accept_trade_offer(self, game_state, trade_offer) -> bool:
        # TODO: Implement the logic to decide if the player should accept the trade offer
        return True
    
    def get_trade_offers(self, game_state) -> List:
        # TODO: Implement the logic to suggest trade offers
        return []
    
    def on_event_received(self, event):
        """
        Called when an event relevant to this player occurs.
        Each player type can override this to respond to events.
        
        Args:
            event: The Event object containing event information
        """
        # Store event in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
            
        # Add to player's event queue
        self.event_queue.append(event)
        
        # Basic implementation just logs the event
        # print(f"[{self.name}] Event: {event.description}")
    
    def get_event(self):
        """
        Get the oldest event from this player's queue.
        
        Returns:
            The oldest event or None if queue is empty
        """
        if not self.event_queue:
            return None
        return self.event_queue.pop(0)
    
    def has_events(self):
        """Check if player has unprocessed events."""
        return len(self.event_queue) > 0
    
    def clear_events(self):
        """Clear all events from the player's queue."""
        self.event_queue.clear()