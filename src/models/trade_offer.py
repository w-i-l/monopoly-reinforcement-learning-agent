from models.tile import Tile
from game.player import Player
from typing import List


class TradeOffer:
    """
    Represents a trade proposal between two players in Monopoly.
    
    Trade offers allow players to exchange properties, money, and Get Out of Jail
    Free cards. Each offer has a unique ID and specifies what the source player
    is offering and what they want in return from the target player.
    
    All trade components are optional - a trade can involve only money, only
    properties, only jail cards, or any combination thereof. The game engine
    validates trade legality before execution.
    
    Attributes
    ----------
    id : int
        Unique identifier for this trade offer
    source_player : Player
        Player making the trade offer
    target_player : Player
        Player receiving the trade offer
    properties_offered : List[Tile]
        Properties the source player is offering
    money_offered : int
        Amount of money the source player is offering
    jail_cards_offered : int
        Number of Get Out of Jail Free cards being offered
    properties_requested : List[Tile]
        Properties the source player wants in return
    money_requested : int
        Amount of money the source player wants in return
    jail_cards_requested : int
        Number of Get Out of Jail Free cards wanted in return
    """

    ID = 0  # Class-level counter for unique trade IDs


    def __init__(
            self,
            source_player: Player,
            target_player: Player,
            properties_offered: List[Tile] = None,
            money_offered: int = 0,
            jail_cards_offered: int = 0,
            properties_requested: List[Tile] = None,
            money_requested: int = 0,
            jail_cards_requested: int = 0
    ):
        """
        Initialize a trade offer between two players.
        
        Parameters
        ----------
        source_player : Player
            Player making the trade offer
        target_player : Player
            Player who will receive and evaluate the offer
        properties_offered : List[Tile], optional
            Properties being offered by the source player
        money_offered : int, default 0
            Amount of money being offered
        jail_cards_offered : int, default 0
            Number of Get Out of Jail Free cards being offered
        properties_requested : List[Tile], optional
            Properties requested from the target player
        money_requested : int, default 0
            Amount of money requested from the target player
        jail_cards_requested : int, default 0
            Number of Get Out of Jail Free cards requested
        """
        self.id = TradeOffer.ID
        TradeOffer.ID += 1
        
        self.source_player = source_player
        self.target_player = target_player
        self.properties_offered = properties_offered
        self.money_offered = money_offered
        self.jail_cards_offered = jail_cards_offered
        self.properties_requested = properties_requested
        self.money_requested = money_requested
        self.jail_cards_requested = jail_cards_requested


    def __str__(self):
        return f"""{self.source_player} is offering:
Properties: {self.properties_offered}
Money: {self.money_offered}
Jail Cards: {self.jail_cards_offered}
to {self.target_player} for:
Properties: {self.properties_requested}
Money: {self.money_requested}
Jail Cards: {self.jail_cards_requested}
"""
    

    def __repr__(self):
        return str(self)