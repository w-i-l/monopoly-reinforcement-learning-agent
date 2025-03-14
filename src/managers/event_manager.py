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
        Args:
            event_type: The type of event to register
            player: The primary player involved in the event
            **kwargs: Additional parameters for the event
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
            game_player.on_event_received(event)
            
        return event
    
    
    def get_event(self) -> Optional[Event]:
        if not self.events:
            return None
        return self.events.pop(0)
    
    
    def peek_event(self) -> Optional[Event]:
        if not self.events:
            return None
        return self.events[0]
    

    def get_all_events(self) -> List[Event]:
        all_events = self.events.copy()
        self.events.clear()
        return all_events
    
    
    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        return [e for e in self.events if e.type == event_type]
    

    def get_events_for_player(self, player: Player) -> List[Event]:
        return [e for e in self.events if e.player == player or e.target_player == player]
    

    def has_events(self) -> bool:
        return len(self.events) > 0
    

    def clear(self):
        self.events.clear()