from abc import ABC, abstractmethod
from typing import List

from models.property import Tile
from models.property_group import PropertyGroup
from game.bankruptcy_request import BankruptcyRequest


class Player(ABC):
    """
    Abstract base class for all Monopoly agents in the reinforcement learning environment.
    
    This interface defines the contract that all agent implementations must follow,
    providing callback methods that the game engine uses to query agent decisions
    during gameplay. Each method represents a specific decision point where the
    agent must choose an action based on the current game state.
    
    The Player class also handles event management, maintaining a queue of game
    events relevant to this player for potential use in decision-making or learning.

    Attributes
    ----------
    event_queue : List
        FIFO queue of unprocessed events relevant to this player
    event_history : List
        Historical record of events, automatically pruned to max_history size
    max_history : int
        Maximum number of events to retain in history (default: 100)
    """


    def __init__(self, name: str, can_be_referenced: bool = False):
        """
        Initialize a new Player agent.
        
        Parameters
        ----------
        name : str
            Display name of this agent used for identification, logging, and
            tournament results. Should be unique within a game session.
            
        can_be_referenced : bool, default False
            Controls how the game engine manages player instances:
            - True: Game maintains reference to this exact instance (recommended
              for stateful agents like RL agents that need to preserve internal
              state between games)
            - False: Game may create new instances as needed (suitable for
              stateless algorithmic agents)
        """
        self.name = name
        self.event_queue = []
        self.event_history = []
        self.max_history = 100
        self.can_be_referenced = can_be_referenced


    def __repr__(self) -> str:
        """String representation showing player name."""
        return f"{self.name}"
    

    @abstractmethod
    def should_buy_property(self, game_state, property: Tile) -> bool:
        """
        Decide whether to purchase an unowned property upon landing on it.
        
        Called when the player lands on an unowned purchasable property
        (Property, Railway, or Utility).
        
        Parameters
        ----------
        game_state : GameState
            
        property : Tile
            The property tile being offered for purchase.
        
        Returns
        -------
        bool
            True if the player wants to purchase the property, False otherwise.
            If False, the property wont't go through the auction process(in the current implementation, it ramains in bank).
        """
        pass
    

    def get_upgrading_suggestions(self, game_state) -> List[PropertyGroup]:
        """
        Suggest property groups to upgrade with houses/hotels.
        
        Called during the player's turn to determine which complete property
        groups should be developed. In this implementation, upgrades must be
        done for entire property groups at once (all properties in a group
        get the same number of houses/hotels).
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        List[PropertyGroup]
            List of PropertyGroup enums representing groups to upgrade.
            Each group in the list will have one house/hotel added to all
            properties in that group (subject to building availability).
        """
        pass
    

    def get_downgrading_suggestions(self, game_state) -> List[PropertyGroup]:
        """
        Suggest property groups to downgrade by selling houses/hotels.
        
        Downgrading converts buildings back to cash at half
        their purchase price.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        List[PropertyGroup]
            List of PropertyGroup enums to downgrade. Each group will have
            one level of development removed (hotel to 4 houses, or remove
            one house from all properties in the group).
        """
        pass
    

    def get_mortgaging_suggestions(self, game_state) -> List[Tile]:
        """
        Suggest individual properties to mortgage for immediate cash.
        
        Mortgaging provides cash equal to half the property's purchase price
        but prevents rent collection. Mortgaged properties can be unmortgaged
        later by paying 110% of the mortgage value.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        List[Tile]
            List of specific properties to mortgage.
        """
        pass
    

    def get_unmortgaging_suggestions(self, game_state) -> List[Tile]:
        """
        Suggest mortgaged properties to unmortgage (reactivate).
        
        Unmortgaging costs 110% of the original mortgage value but allows
        the property to collect rent again.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        List[Tile]
            List of mortgaged properties to reactivate.
        """
        pass
    

    def should_pay_get_out_of_jail_fine(self, game_state) -> bool:
        """
        Decide whether to pay 50₩ fine to get out of jail immediately.
        
        Called when the player is in jail and has the option to pay the fine
        instead of trying to roll doubles or using a Get Out of Jail Free card.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        bool
            True to pay the 50₩ fine and get out immediately, False to try
            rolling doubles or use a card if available.
        """
        pass
    

    def should_use_escape_jail_card(self, game_state) -> bool:
        """
        Decide whether to use a Get Out of Jail Free card.
        
        Called when the player is in jail and possesses a Get Out of Jail Free
        card from Chance or Community Chest.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        bool
            True to use the card immediately, False to save it and try other
            methods (rolling doubles or paying fine).
        """
        pass
    

    def should_accept_trade_offer(self, game_state, trade_offer) -> bool:
        """
        Decide whether to accept a trade offer from another player.
        
        Parameters
        ----------
        game_state : GameState
            
        trade_offer : TradeOffer
        
        Returns
        -------
        bool
            True to accept the trade, False to reject it.
        """
        pass
    

    def get_trade_offers(self, game_state) -> List:
        """
        Generate trade offers to propose to other players.
        
        Parameters
        ----------
        game_state : GameState
        
        Returns
        -------
        List[TradeOffer]
        """
        pass
    

    def handle_bankruptcy(self, game_state, amount: int) -> BankruptcyRequest:
        """
        Handle bankruptcy by proposing actions to raise the required cash.
        
        Called when the player cannot afford a required payment (rent, tax, etc.).
        The player must propose a combination of actions to raise the needed funds
        or he is declared bankrupt.
        
        Parameters
        ----------
        game_state : GameState

            
        amount : int
            The amount of money needed to avoid bankruptcy
        
        Returns
        -------
        BankruptcyRequest
        """
        return BankruptcyRequest()
    

    def on_event_received(self, event):
        """
        Process game events relevant to this player.
        
        Called by the event system when significant game events occur.
        Events provide information about game state changes and can be
        used for learning, strategy adjustment, or logging.
        
        Parameters
        ----------
        event : Event
        """
        # Store event in history (with size limit)
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)
            
        # Add to player's event queue for processing
        self.event_queue.append(event)
        
        # Default implementation: events are stored but not actively processed
        # Subclasses should override this method for custom event handling
    

    def get_event(self):
        """
        Retrieve the oldest unprocessed event from this player's queue.
        
        Returns
        -------
        Event or None
            The oldest event from the queue, or None if queue is empty.
            Event is removed from the queue when retrieved.
        """
        if not self.event_queue:
            return None
        return self.event_queue.pop(0)
    

    def has_events(self):
        """
        Check if there are unprocessed events in the queue.
        
        Returns
        -------
        bool
            True if there are events waiting to be processed, False otherwise.
        """
        return len(self.event_queue) > 0
    

    def clear_events(self):
        """
        Remove all events from the player's queue.
        """
        self.event_queue.clear()