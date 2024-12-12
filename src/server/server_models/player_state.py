from pydantic import BaseModel
from typing import List, Dict
from server_models.property import Property

class PlayerState(BaseModel):
    name: str
    properties: List[Property]
    houses: Dict[int, int]
    hotels: Dict[int, int]
    escape_jail_cards: int
    in_jail: bool
    position: int
    balance: int