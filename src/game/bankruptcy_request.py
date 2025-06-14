from typing import List

from models.property import Tile
from models.property_group import PropertyGroup


class BankruptcyRequest:
    """
    Request object containing actions a player proposes to avoid bankruptcy.
    
    When a player cannot afford a required payment, they must submit a bankruptcy
    request specifying which assets to liquidate or trades to make. If the request
    is empty, the player declares bankruptcy and is eliminated from the game.
    
    Attributes
    ----------
    downgrading_suggestions : List[PropertyGroup]
        Property groups to downgrade by selling houses/hotels
    mortgaging_suggestions : List[Tile]
        Individual properties to mortgage for immediate cash
    trade_offers : List[TradeOffer]
        Trade proposals to generate cash or reduce debt
    """


    def __init__(
            self, 
            downgrading_suggestions: List[PropertyGroup] = [],
            mortgaging_suggestions: List[Tile] = [],
            trade_offers: List = [],
    ):
        """
        Initialize a bankruptcy request with proposed actions.
        
        Parameters
        ----------
        downgrading_suggestions : List[PropertyGroup], default []
            Property groups to sell buildings from
        mortgaging_suggestions : List[Tile], default []
            Properties to mortgage for cash
        trade_offers : List[TradeOffer], default []
            Trades to propose for emergency cash
        """
        self.downgrading_suggestions = downgrading_suggestions
        self.mortgaging_suggestions = mortgaging_suggestions
        self.trade_offers = trade_offers


    def __repr__(self):
        """String representation for debugging."""
        return f"BankruptcyRequest(downgrading_suggestions={self.downgrading_suggestions}, mortgaging_suggestions={self.mortgaging_suggestions}, trade_offers={self.trade_offers})"


    def __str__(self):
        """String representation for display."""
        return self.__repr__()


    def is_empty(self) -> bool:
        """
        Check if the bankruptcy request contains no actions.
        
        Returns
        -------
        bool
            True if no actions are proposed (player declares bankruptcy),
            False if player has actions to attempt debt resolution
        """
        return len(self.downgrading_suggestions) == 0 and len(self.mortgaging_suggestions) == 0 and len(self.trade_offers) == 0