from pydantic import BaseModel
from server_models.property import Property
from server_models.player_state import PlayerState
from typing import List, Set

class GameStateResponse(BaseModel):
    players: List[PlayerState]
    currentPlayer: int
    ownedProperties: Set[int]
    mortgagedProperties: Set[int]