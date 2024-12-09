from models.tile import Tile
from utils.helper_functions import format_path
import json

class Railway(Tile):
    @classmethod
    def _load_attributes(cls):
        if not hasattr(cls, '_attr_cache'):
            with open(format_path("../data/railway_stations.json"), 'r') as f:
                data = json.load(f)
                cls._attr_cache = (
                    data['price'],
                    data['mortage'],
                    data['buyback_price'],
                    data['rent']
                )
        return cls._attr_cache

    def __init__(self, id: int, name: str):
        super().__init__(id, name)
        self.price, self.mortage, self.buyback_price, self.rent = self._load_attributes()

    def __repr__(self):
        return f"{self.name} (Railway)"