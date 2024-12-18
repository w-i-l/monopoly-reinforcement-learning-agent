class GameException(Exception):
    """Base class for all game exceptions"""
    pass

class PropertyAlreadyOwnedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is already owned"
        super().__init__(self.message)

class PropertyNotOwnedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is not owned"
        super().__init__(self.message)

class PropertyAlreadyMortgagedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is already mortgaged"
        super().__init__(self.message)

class NotPropertyOwnerException(GameException):
    def __init__(self, property_name: str, player_name: str):
        self.message = f"Player {player_name} does not own property {property_name}"
        super().__init__(self.message)

class PropertyOwnerPayingRentException(GameException):
    def __init__(self, property_name: str, player_name: str):
        self.message = f"Cannot pay rent to self for property {property_name} owned by {player_name}"
        super().__init__(self.message)

class PropertyHasImprovementsException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot mortgage property {property_name} with houses/hotels"
        super().__init__(self.message)

class MaxHousesReachedException(GameException):
    def __init__(self, group_name: str):
        self.message = f"Maximum houses already placed on {group_name}"
        super().__init__(self.message)

class IncompletePropertyGroupException(GameException):
    def __init__(self, group_name: str):
        self.message = f"Must own all properties in {group_name} group"
        super().__init__(self.message)

class MaxHotelsReachedException(GameException):
    def __init__(self, group_name: str):
        self.message = f"Hotel already exists on {group_name}"
        super().__init__(self.message)

class InsufficientHousesException(GameException):
    def __init__(self, group_name: str, current: int, required: int):
        self.message = f"Need {required} houses on {group_name} (currently has {current})"
        super().__init__(self.message)

class NoHousesToSellException(GameException):
    def __init__(self, group_name: str):
        self.message = f"No houses to sell on {group_name}"
        super().__init__(self.message)

class NoHotelToSellException(GameException):
    def __init__(self, group_name: str):
        self.message = f"No hotel to sell on {group_name}"
        super().__init__(self.message)

class NotImprovementOwnerException(GameException):
    def __init__(self, improvement_type: str, group_name: str, player_name: str):
        self.message = f"Player {player_name} does not own the {improvement_type} on {group_name}"
        super().__init__(self.message)

class NoJailCardException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} has no jail free card"
        super().__init__(self.message)

class NotInJailException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} is not in jail"
        super().__init__(self.message)

class PropertyHasNoOwnerException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} has no owner"
        super().__init__(self.message)

class NotEnoughBalanceException(GameException):
    def __init__(self, price: int, balance: int):
        self.message = f"Not enough balance to complete the transaction. Price: {price}, Balance: {balance}"
        super().__init__(self.message)

class MortgagePropertyRentException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot pay rent on mortgaged property {property_name}"
        super().__init__(self.message)

class MortgagePropertyHouseException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot build house on mortgaged property {property_name}"
        super().__init__(self.message)

class MortgagePropertyHotelException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot build hotel on mortgaged property {property_name}"
        super().__init__(self.message)

class PlayerInJailException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} is in jail"
        super().__init__(self.message)

class BuildingHousesOfTopOnHotelException(GameException):
    def __init__(self, property_group: str):
        self.message = f"Cannot build houses if there is an hotel already place on {property_group} group"
        super.__init__(self.message)