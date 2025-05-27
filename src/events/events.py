from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, List, Dict
from game.player import Player
from models.tile import Tile
from models.property_group import PropertyGroup

class EventType(Enum):
    # Movement Events
    PLAYER_MOVED = auto()
    PLAYER_PASSED_GO = auto()
    PLAYER_WENT_TO_JAIL = auto()
    PLAYER_GOT_OUT_OF_JAIL = auto()
    
    # Property Events
    PROPERTY_PURCHASED = auto()
    PROPERTY_MORTGAGED = auto()
    PROPERTY_UNMORTGAGED = auto()
    
    # Building Events
    HOUSE_BUILT = auto()
    HOTEL_BUILT = auto()
    HOUSE_SOLD = auto()
    HOTEL_SOLD = auto()
    
    # Financial Events
    RENT_PAID = auto()
    TAX_PAID = auto()
    MONEY_RECEIVED = auto()
    MONEY_PAID = auto()
    PLAYER_DID_NOT_HAVE_ENOUGH_MONEY = auto()
    PLAYER_BANKRUPT = auto()
    
    # Card Events
    CHANCE_CARD_DRAWN = auto()
    COMMUNITY_CHEST_CARD_DRAWN = auto()
    GET_OUT_OF_JAIL_CARD_RECEIVED = auto()
    GET_OUT_OF_JAIL_CARD_USED = auto()
    
    # Trading Events
    TRADE_OFFERED = auto()
    TRADE_ACCEPTED = auto()
    TRADE_REJECTED = auto()
    TRADE_EXECUTED = auto()
    
    # Dice Events
    DICE_ROLLED = auto()
    DOUBLES_ROLLED = auto()
    
    # Turn Events
    TURN_STARTED = auto()
    TURN_ENDED = auto()
    
    # Game Events
    GAME_STARTED = auto()
    GAME_ENDED = auto()
    AUCTION_STARTED = auto()
    AUCTION_ENDED = auto()


@dataclass
class Event:
    """
    Event class to represent game events.
    
    Attributes:
        type: The type of event that occurred.
        player: The player who triggered or is affected by the event.
        target_player: Optional second player involved in the event (e.g., for trades, rent payments).
        tile: Optional tile/property related to the event.
        amount: Optional monetary amount involved in the event.
        dice: Optional dice roll results.
        description: Human-readable description of what happened.
        additional_data: Dictionary for any other event-specific data.
    """
    type: EventType
    player: Player
    target_player: Optional[Player] = None
    property_group: Optional[PropertyGroup] = None
    tile: Optional[Tile] = None
    amount: Optional[int] = None
    dice: Optional[tuple[int, int]] = None
    description: str = ""
    additional_data: Dict[str, Any] = None
    reason: Optional[str] = None
    
    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}
        
        # Auto-generate a description if none was provided
        if not self.description:
            self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        """Generate a human-readable description of the event based on its type and data."""
        
        descriptions = {
            EventType.PLAYER_MOVED: f"{self.player} moved to {self.tile}" if self.tile else f"{self.player} moved",
            EventType.PLAYER_PASSED_GO: f"{self.player} passed GO and collected $200",
            EventType.PLAYER_WENT_TO_JAIL: f"{self.player} went to jail",
            EventType.PLAYER_GOT_OUT_OF_JAIL: f"{self.player} got out of jail",
            
            EventType.PROPERTY_PURCHASED: f"{self.player} purchased {self.tile} for ${self.amount}" if self.tile and self.amount else f"{self.player} purchased a property",
            EventType.PROPERTY_MORTGAGED: f"{self.player} mortgaged {self.tile} for ${self.amount}" if self.tile and self.amount else f"{self.player} mortgaged a property",
            EventType.PROPERTY_UNMORTGAGED: f"{self.player} unmortgaged {self.tile} for ${self.amount}" if self.tile and self.amount else f"{self.player} unmortgaged a property",
            
            EventType.HOUSE_BUILT: f"{self.player} built a house on {self.property_group}" if self.property_group else f"{self.player} built a house",
            EventType.HOTEL_BUILT: f"{self.player} built a hotel on {self.property_group}" if self.property_group else f"{self.player} built a hotel",
            EventType.HOUSE_SOLD: f"{self.player} sold a house from {self.property_group}" if self.property_group else f"{self.player} sold a house",
            EventType.HOTEL_SOLD: f"{self.player} sold a hotel from {self.property_group}" if self.property_group else f"{self.player} sold a hotel",
            
            EventType.RENT_PAID: f"{self.player} paid ${self.amount} rent to {self.target_player} for {self.tile}" if all([self.amount, self.target_player, self.tile]) else f"{self.player} paid rent",
            EventType.TAX_PAID: f"{self.player} paid ${self.amount} in taxes" if self.amount else f"{self.player} paid taxes",
            EventType.MONEY_RECEIVED: f"{self.player} received ${self.amount}" if self.amount else f"{self.player} received money",
            EventType.MONEY_PAID: f"{self.player} paid ${self.amount}" if self.amount else f"{self.player} paid money",
            EventType.PLAYER_BANKRUPT: f"{self.player} went bankrupt",
            EventType.PLAYER_DID_NOT_HAVE_ENOUGH_MONEY: f"{self.player} did not have enough money to pay ${self.amount} for {self.reason}",
            
            EventType.CHANCE_CARD_DRAWN: f"{self.player} drew a Chance card",
            EventType.COMMUNITY_CHEST_CARD_DRAWN: f"{self.player} drew a Community Chest card",
            EventType.GET_OUT_OF_JAIL_CARD_RECEIVED: f"{self.player} received a Get Out of Jail Free card",
            EventType.GET_OUT_OF_JAIL_CARD_USED: f"{self.player} used a Get Out of Jail Free card",
            
            EventType.TRADE_OFFERED: f"{self.player} offered a trade to {self.target_player}" if self.target_player else f"{self.player} offered a trade",
            EventType.TRADE_ACCEPTED: f"{self.target_player} accepted {self.player}'s trade offer" if self.target_player else f"Trade was accepted",
            EventType.TRADE_REJECTED: f"{self.target_player} rejected {self.player}'s trade offer" if self.target_player else f"Trade was rejected",
            EventType.TRADE_EXECUTED: f"Trade executed between {self.player} and {self.target_player}" if self.target_player else f"Trade executed",
            
            EventType.DICE_ROLLED: f"{self.player} rolled {self.dice[0]} and {self.dice[1]} ({self.dice[0] + self.dice[1]} total)" if self.dice else f"{self.player} rolled the dice",
            EventType.DOUBLES_ROLLED: f"{self.player} rolled doubles ({self.dice[0]}, {self.dice[1]})" if self.dice else f"{self.player} rolled doubles",
            
            EventType.TURN_STARTED: f"{self.player}'s turn started",
            EventType.TURN_ENDED: f"{self.player}'s turn ended",
            
            EventType.GAME_STARTED: "Game has started",
            EventType.GAME_ENDED: f"Game has ended. Winner: {self.player}" if self.player else "Game has ended",
            EventType.AUCTION_STARTED: f"Auction started for {self.tile}" if self.tile else "Auction started",
            EventType.AUCTION_ENDED: f"Auction ended. {self.tile} sold to {self.player} for ${self.amount}" if all([self.tile, self.player, self.amount]) else "Auction ended"
        }
        
        return descriptions.get(self.type, f"Event: {self.type}")
