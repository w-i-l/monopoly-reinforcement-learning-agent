from events.events import EventType, Event
from game.player import Player
from typing import List, Optional


class EventManager:
    """
    Manages game events in a FIFO queue and provides mechanisms for registering 
    and processing events.
    """
    def __init__(self, game_state):
        self.game_state = game_state
        self.events = []
        # Track the most recent events for easier access/debugging
        self.recent_events = []
        self.max_recent_events = 50
    
    def register_event(self, event_type: EventType, player: Player, **kwargs) -> Event:
        """
        Register a new event with the given type and parameters.
        
        Args:
            event_type: The type of event to register
            player: The primary player involved in the event
            **kwargs: Additional parameters for the event
            
        Returns:
            The created Event object
        """
        event = Event(type=event_type, player=player, **kwargs)
        self.events.append(event)
        
        # Add to recent events history
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Notify all players about the event
        # This ensures all players are aware of events, not just those directly involved
        for game_player in self.game_state.players:
            # You can decide whether to filter events based on relevance,
            # or just send all events to all players as I'm doing here
            game_player.on_event_received(event)

        
        # If there's a target player, notify them too
        if event.target_player and event.target_player != player:
            event.target_player.on_event_received(event)
            
        return event
    
    def get_event(self) -> Optional[Event]:
        """
        Get the oldest event in the queue (FIFO).
        
        Returns:
            The oldest Event or None if the queue is empty
        """
        if not self.events:
            return None
        return self.events.pop(0)
    
    def peek_event(self) -> Optional[Event]:
        """
        Look at the oldest event without removing it.
        
        Returns:
            The oldest Event or None if the queue is empty
        """
        if not self.events:
            return None
        return self.events[0]
    
    def get_all_events(self) -> List[Event]:
        """
        Get all events and clear the queue.
        
        Returns:
            List of all events
        """
        all_events = self.events.copy()
        self.events.clear()
        return all_events
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """
        Get all events of a specific type without removing them.
        
        Args:
            event_type: The type of events to retrieve
            
        Returns:
            List of events of the specified type
        """
        return [e for e in self.events if e.type == event_type]
    
    def get_events_for_player(self, player: Player) -> List[Event]:
        """
        Get all events involving a specific player without removing them.
        
        Args:
            player: The player whose events we want
            
        Returns:
            List of events involving the player
        """
        return [e for e in self.events if e.player == player or e.target_player == player]
    
    def has_events(self) -> bool:
        """Check if there are any events in the queue."""
        return len(self.events) > 0
    
    def clear(self):
        """Clear all events from the queue."""
        self.events.clear()


# Factory methods to create common event types
def create_move_event(event_manager, player, position, tile, passed_go=False):
    """Factory method to create a player movement event."""
    event = event_manager.register_event(
        EventType.PLAYER_MOVED,
        player=player,
        tile=tile,
        additional_data={"position": position}
    )
    
    if passed_go:
        event_manager.register_event(
            EventType.PLAYER_PASSED_GO,
            player=player,
            amount=200
        )
    
    return event

def create_property_purchase_event(event_manager, player, property, price):
    """Factory method to create a property purchase event."""
    return event_manager.register_event(
        EventType.PROPERTY_PURCHASED,
        player=player,
        tile=property,
        amount=price
    )

def create_rent_payment_event(event_manager, player, owner, property, amount):
    """Factory method to create a rent payment event."""
    return event_manager.register_event(
        EventType.RENT_PAID,
        player=player,
        target_player=owner,
        tile=property,
        amount=amount
    )

def create_dice_roll_event(event_manager, player, dice):
    """Factory method to create a dice roll event."""
    event = event_manager.register_event(
        EventType.DICE_ROLLED,
        player=player,
        dice=dice
    )
    
    if dice[0] == dice[1]:
        event_manager.register_event(
            EventType.DOUBLES_ROLLED,
            player=player,
            dice=dice
        )
    
    return event

def create_trade_event(event_manager, trade_offer, accepted=True):
    """Factory method to create a trade event."""
    if accepted:
        event = event_manager.register_event(
            EventType.TRADE_ACCEPTED,
            player=trade_offer.source_player,
            target_player=trade_offer.target_player,
            additional_data={"trade_offer": trade_offer}
        )
        
        event_manager.register_event(
            EventType.TRADE_EXECUTED,
            player=trade_offer.source_player,
            target_player=trade_offer.target_player,
            additional_data={"trade_offer": trade_offer}
        )
    else:
        event = event_manager.register_event(
            EventType.TRADE_REJECTED,
            player=trade_offer.source_player,
            target_player=trade_offer.target_player,
            additional_data={"trade_offer": trade_offer}
        )
    
    return event