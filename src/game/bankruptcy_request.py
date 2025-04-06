from typing import List
from models.property import Tile
from models.property_group import PropertyGroup

class BankruptcyRequest:
    def __init__(
            self, 
            downgrading_suggestions: List[PropertyGroup] = [],
            mortgaging_suggestions: List[Tile] = [],
            trade_offers: List = [],
    ):
        self.downgrading_suggestions = downgrading_suggestions
        self.mortgaging_suggestions = mortgaging_suggestions
        self.trade_offers = trade_offers

    def __repr__(self):
        return f"BankruptcyRequest(downgrading_suggestions={self.downgrading_suggestions}, mortgaging_suggestions={self.mortgaging_suggestions}, trade_offers={self.trade_offers})"
    
    def __str__(self):
        return self.__repr__()
    
    def is_empty(self) -> bool:
        return len(self.downgrading_suggestions) == 0 and len(self.mortgaging_suggestions) == 0 and len(self.trade_offers) == 0
    