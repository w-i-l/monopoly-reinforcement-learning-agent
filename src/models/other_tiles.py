from models.tile import Tile
from utils.helper_functions import format_path
import json


class Taxes(Tile):
    """
    Represents a tax tile on the Monopoly board.
    
    Tax tiles require players to pay a fixed amount when landed on.
    The tax amount is predefined and cannot be negotiated or avoided.
    
    Attributes
    ----------
    tax : int
        Amount of tax that must be paid when landing on this tile
    """


    def __init__(self, id: int, name: str, tax: int):
        """
        Initialize a tax tile with its tax amount.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the tax tile
        tax : int
            Tax amount to be paid when landed on
        """
        super().__init__(id, name)
        self.tax = tax


    def __repr__(self):
        return f"{self.name} (Tax)"


class Chance(Tile):
    """
    Represents a Chance tile that triggers drawing from the Chance deck.
    
    When players land on this tile, they must draw a card from the Chance deck
    and execute its instructions immediately.
    """

    def __init__(self, id: int, name: str):
        """
        Initialize a chance tile.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the chance tile
        """
        super().__init__(id, name)


    def __repr__(self):
        return f"{self.name} (Chance)"


class CommunityChest(Tile):
    """
    Represents a Community Chest tile that triggers drawing from the Community Chest deck.
    
    When players land on this tile, they must draw a card from the Community Chest
    deck and execute its instructions immediately.
    """


    def __init__(self, id: int, name: str):
        """
        Initialize a community chest tile.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the community chest tile
        """
        super().__init__(id, name)


    def __repr__(self):
        return f"{self.name} (Community Chest)"


class GoToJail(Tile):
    """
    Represents the "Go to Jail" tile that sends players directly to jail.
    
    When players land on this tile, they are immediately sent to jail without
    collecting $200 for passing Go, and must use normal jail escape methods.
    """


    def __init__(self, id: int, name: str):
        """
        Initialize a go to jail tile.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the go to jail tile
        """
        super().__init__(id, name)


    def __repr__(self):
        return f"{self.name} (Go To Jail)"


class Jail(Tile):
    """
    Represents the jail tile where players can be visiting or imprisoned.
    
    Players can be "just visiting" (landing normally) or "in jail" (sent by
    various game mechanics). Imprisoned players must pay a fine, roll doubles,
    or use a Get Out of Jail Free card to escape.
    
    Attributes
    ----------
    fine : int
        Amount that must be paid to immediately escape from jail
    """


    def __init__(self, id: int, name: str):
        """
        Initialize the jail tile with escape fine.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the jail tile
        """
        super().__init__(id, name)
        self.fine = 50  # Standard jail fine amount


    def __repr__(self):
        return f"{self.name} (Jail)"


class FreeParking(Tile):
    """
    Represents the Free Parking tile with no game effect.
    
    This is a neutral tile where players can land without any positive or
    negative consequences. In house rules, money from taxes and fines may
    be collected here, but the standard rules have no effect.
    """


    def __init__(self, id: int, name: str):
        """
        Initialize the free parking tile.
        
        Parameters
        ----------
        id : int
            Board position of this tile
        name : str
            Display name of the free parking tile
        """
        super().__init__(id, name)


    def __repr__(self):
        return f"{self.name} (Free Parking)"


class Go(Tile):
    """
    Represents the starting tile where players collect salary.
    
    Players collect $200 each time they pass or land on Go. This tile
    serves as the starting position and salary collection point for all players.
    """


    def __init__(self, id: int, name: str):
        """
        Initialize the go tile.
        
        Parameters
        ----------
        id : int
            Board position of this tile (typically 0)
        name : str
            Display name of the go tile
        """
        super().__init__(id, name)


    def __repr__(self):
        return f"{self.name} (Go)"
