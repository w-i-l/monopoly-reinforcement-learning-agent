from models.tile import Tile
from game.player import Player
from typing import List

class TradeOffer:

    ID = 0

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
        return f"{self.source_player} is offering {self.properties_offered} and {self.money_offered} and {self.jail_cards_offered} to {self.target_player} for {self.properties_requested} and {self.money_requested} and {self.jail_cards_requested}"
    
    def __repr__(self):
        return str(self)