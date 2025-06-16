from models.tile import Tile
from utils.helper_functions import format_path
import json


class Utility(Tile):
    """
    Represents a utility tile (Electric Company, Water Works) with dice-based rent.
    
    Utilities generate rent based on the dice roll that landed the player on the
    utility, multiplied by a factor determined by how many utilities the owner
    controls. Unlike properties, utilities cannot be developed but provide
    consistent income potential.
    
    All utilities share the same price and mortgage values, loaded from a shared
    configuration file for consistency.
    
    Rent calculation:
    - 1 utility owned: 4 × dice roll
    - 2 utilities owned: 10 × dice roll
    
    Attributes
    ----------
    price : int
        Purchase price (shared by all utilities)
    mortgage : int
        Mortgage value (shared by all utilities)
    buyback_price : int
        Unmortgage cost (shared by all utilities)
    """


    @classmethod
    def _load_attributes(cls):
        """
        Load shared utility attributes from configuration file.
        
        Uses class-level caching to avoid repeated file reads since all
        utilities share the same pricing structure.
        
        Returns
        -------
        tuple
            (price, mortgage, buyback_price)
        """
        if not hasattr(cls, '_attr_cache'):
            with open(format_path("../data/utilities.json"), 'r') as f:
                data = json.load(f)
                cls._attr_cache = (
                    data['price'],
                    data['mortgage'],
                    data['buyback_price']
                )
        return cls._attr_cache


    def __init__(self, id: int, name: str):
        """
        Initialize a utility with shared attributes from configuration.
        
        Parameters
        ----------
        id : int
            Board position of this utility
        name : str
            Display name of the utility
        """
        super().__init__(id, name)
        self.price, self.mortgage, self.buyback_price = self._load_attributes()


    def __repr__(self):
        return f"{self.name} (Utility)"