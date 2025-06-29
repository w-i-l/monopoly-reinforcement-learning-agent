from typing import List, Optional

from events.events import EventType, Event
from game.player import Player


class EventManager:
    """
    Centralized event management system for Monopoly game state changes and notifications.
    
    The manager maintains both a processing queue for game engine consumption and
    a recent events history for debugging and analysis purposes. All events are
    automatically broadcast to every player in the game, ensuring consistent
    information distribution.
    
    Attributes
    ----------
    game_state : GameState
        Reference to the current game state for player access
    events : List[Event]
        FIFO queue of pending events for processing
    recent_events : List[Event]
        Rolling history of recent events for debugging and analysis
    max_recent_events : int
        Maximum number of events to retain in recent history
    """


    def __init__(self, game_state):
        """
        Initialize the event manager with game state reference.
        
        Parameters
        ----------
        game_state : GameState
            Current game state containing player references for event distribution
        """
        self.game_state = game_state
        self.events = []
        # Track the most recent events for easier access/debugging
        self.recent_events = []
        self.max_recent_events = 50


    def register_event(self, event_type: EventType, player: Player, **kwargs) -> Event:
        """
        Create and register a new game event with automatic player notification.
        
        Creates an event object, adds it to the processing queue, maintains recent
        history, and automatically notifies all players in the game. This ensures
        consistent event distribution for logging, learning, and UI updates.
        
        Parameters
        ----------
        event_type : EventType
            The type of event being registered (property purchase, rent payment, etc.)
        player : Player
            Primary player involved in the event (the actor)
        **kwargs : dict
            Additional event parameters such as target_player, tile, amount, etc.
            
        Returns
        -------
        Event
            The created and registered event object
        """
        event = Event(type=event_type, player=player, **kwargs)
        self.events.append(event)
        
        # Add to recent events history with size management
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Notify all players about the event
        # This ensures all players are aware of events, not just those directly involved
        for game_player in self.game_state.players:
            game_player.on_event_received(event)
            
        return event


    def get_event(self) -> Optional[Event]:
        """
        Retrieve and remove the oldest event from the queue.
        
        Returns
        -------
        Optional[Event]
            The oldest event in the queue, or None if queue is empty.
            Event is removed from the queue when retrieved.
        """
        if not self.events:
            return None
        return self.events.pop(0)


    def peek_event(self) -> Optional[Event]:
        """
        View the oldest event without removing it from the queue.
        
        Returns
        -------
        Optional[Event]
            The oldest event in the queue, or None if queue is empty.
            Event remains in the queue after peeking.
        """
        if not self.events:
            return None
        return self.events[0]


    def get_all_events(self) -> List[Event]:
        """
        Retrieve all events and clear the queue.
        
        Returns
        -------
        List[Event]
            Copy of all events that were in the queue. Original queue is cleared.
        """
        all_events = self.events.copy()
        self.events.clear()
        return all_events


    def get_events_by_type(self, event_type: EventType) -> List[Event]:
        """
        Filter events by their type.
        
        Parameters
        ----------
        event_type : EventType
            The type of events to retrieve
            
        Returns
        -------
        List[Event]
            All events in the queue matching the specified type
        """
        return [e for e in self.events if e.type == event_type]


    def get_events_for_player(self, player: Player) -> List[Event]:
        """
        Filter events involving a specific player.
        
        Parameters
        ----------
        player : Player
            The player to filter events for
            
        Returns
        -------
        List[Event]
            All events where the player is either the actor or target
        """
        return [e for e in self.events if e.player == player or e.target_player == player]


    def has_events(self) -> bool:
        """
        Check if there are any pending events in the queue.
        
        Returns
        -------
        bool
            True if there are events waiting to be processed, False otherwise
        """
        return len(self.events) > 0


    def clear(self):
        """
        Remove all events from the processing queue.
        
        Recent events history is preserved for debugging purposes.
        Use this method when resetting game state or clearing pending events.
        """
        self.events.clear()