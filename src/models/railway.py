from models.tile import Tile
from utils.helper_functions import format_path
import json


class Railway(Tile):
    """
    Represents a railway/railroad tile with scaling rent based on ownership count.
    
    Railways generate rent based on how many railways the owner controls.
    Unlike properties, railways cannot be developed with houses or hotels,
    but their rent scales significantly with the number of railways owned.
    
    All railways share the same price, mortgage value, and rent structure,
    loaded from a shared configuration file for consistency.
    
    Attributes
    ----------
    price : int
        Purchase price (shared by all railways)
    mortgage : int
        Mortgage value (shared by all railways)
    buyback_price : int
        Unmortgage cost (shared by all railways)
    rent : list[int]
        Rent amounts for owning 1-4 railways [1_railway, 2_railway, 3_railway, 4_railway]
    """


    @classmethod
    def _load_attributes(cls):
        """
        Load shared railway attributes from configuration file.
        
        Uses class-level caching to avoid repeated file reads since all
        railways share the same pricing and rent structure.
        
        Returns
        -------
        tuple
            (price, mortgage, buyback_price, rent_list)
        """
        if not hasattr(cls, '_attr_cache'):
            with open(format_path("../data/railway_stations.json"), 'r') as f:
                data = json.load(f)
                cls._attr_cache = (
                    data['price'],
                    data['mortgage'],
                    data['buyback_price'],
                    data['rent']
                )
        return cls._attr_cache


    def __init__(self, id: int, name: str):
        """
        Initialize a railway with shared attributes from configuration.
        
        Parameters
        ----------
        id : int
            Board position of this railway
        name : str
            Display name of the railway
        """
        super().__init__(id, name)
        self.price, self.mortgage, self.buyback_price, self.rent = self._load_attributes()


    def __repr__(self):
        return f"{self.name}"