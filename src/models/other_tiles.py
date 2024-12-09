from models.tile import Tile
from utils.helper_functions import format_path
import json

class Taxes(Tile):
    def __init__(self, id: int, name: str, tax: int):
        super().__init__(id, name)
        self.tax = tax

    def __repr__(self):
        return f"{self.name} (Tax)"
    
class Chance(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Chance)"
    
class CommunityChest(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Community Chest)"
    
class GoToJail(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Go To Jail)"
    
class Jail(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Jail)"
    
class FreeParking(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Free Parking)"
    
class Go(Tile):
    def __init__(self, id: int, name: str):
        super().__init__(id, name)

    def __repr__(self):
        return f"{self.name} (Go)"