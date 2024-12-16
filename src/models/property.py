from models.tile import Tile
from models.property_group import PropertyGroup
    

class Property(Tile):
    def __init__(
            self,
            id: int,
            name: str,
            group: PropertyGroup,
            price: int,
            base_rent: int,
            full_group_rent: int,
            house_rent: list[int],
            hotel_rent: int,
            mortgage: int,
            buyback_price: int
    ):
        super().__init__(id, name)
        self.group = group
        self.price = price
        self.base_rent = base_rent
        self.full_group_rent = full_group_rent
        self.house_rent = house_rent
        self.hotel_rent = hotel_rent
        self.mortgage = mortgage
        self.buyback_price = buyback_price

    def __repr__(self):
        return f"{self.name} ({self.group.value})"