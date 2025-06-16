from models.tile import Tile
from models.property_group import PropertyGroup


class Property(Tile):
    """
    Represents a purchasable property tile with rent and development capabilities.
    
    Properties can be owned by players and generate rent when opponents land on them.
    Rent amounts vary based on whether the owner has a monopoly (all properties in
    the color group) and the level of development (houses/hotels).
    
    Properties can be mortgaged for immediate cash and later unmortgaged to restore
    rent collection. Development with houses and hotels is only possible when the
    owner controls the complete color group.
    
    Attributes
    ----------
    group : PropertyGroup
        Color group this property belongs to
    price : int
        Purchase price of the property
    base_rent : int
        Rent when property is owned individually
    full_group_rent : int
        Rent when owner has monopoly but no houses
    house_rent : list[int]
        Rent amounts for 1-4 houses [1_house, 2_house, 3_house, 4_house]
    hotel_rent : int
        Rent amount when property has a hotel
    mortgage : int
        Amount received when mortgaging the property
    buyback_price : int
        Cost to unmortgage the property (typically mortgage * 1.1)
    """


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
        """
        Initialize a property with all rent and pricing information.
        
        Parameters
        ----------
        id : int
            Board position of this property
        name : str
            Display name of the property
        group : PropertyGroup
            Color group this property belongs to
        price : int
            Purchase price of the property
        base_rent : int
            Rent collected when owned individually
        full_group_rent : int
            Rent collected when owner has monopoly but no development
        house_rent : list[int]
            List of rent amounts for 1-4 houses respectively
        hotel_rent : int
            Rent amount when property has a hotel
        mortgage : int
            Cash received when mortgaging
        buyback_price : int
            Cost to unmortgage (typically 110% of mortgage value)
        """
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
        return f"{self.name}"