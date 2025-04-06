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
        self.message = f"Cannot build/sell house on mortgaged property {property_name}"
        super().__init__(self.message)

class MortgagePropertyHotelException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot build/sell hotel on mortgaged property {property_name}"
        super().__init__(self.message)

class PlayerInJailException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} is in jail"
        super().__init__(self.message)

class BuildingHousesOfTopOnHotelException(GameException):
    def __init__(self, property_group: str):
        self.message = f"Cannot build houses if there is an hotel already place on {property_group} group"
        super.__init__(self.message)

class PropertyNotMortgagedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is not mortgaged"
        super().__init__(self.message)

class PlayerDoesNotExistException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} does not exist"
        super().__init__(self.message)

class PropertyInBothOfferedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is in both offered and requested properties"
        super().__init__(self.message)

class MortgagePropertyTradeException(GameException):
    def __init__(self, property_name: str):
        self.message = f"Cannot trade mortgaged property {property_name}"
        super().__init__(self.message)

class NegativeMoneyOfferedException(GameException):
    def __init__(self):
        self.message = "Money offered cannot be negative"
        super().__init__(self.message)

class NegativeJailCardOfferedException(GameException):
    def __init__(self):
        self.message = "Jail cards offered cannot be negative"
        super().__init__(self.message)

class NegativeMoneyRequestedException(GameException):
    def __init__(self):
        self.message = "Money requested cannot be negative"
        super().__init__(self.message)

class NegativeJailCardRequestedException(GameException):
    def __init__(self):
        self.message = "Jail cards requested cannot be negative"
        super().__init__(self.message)

class NotEnoughJailCardsException(GameException):
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player {player_name} has only {jail_cards} jail cards"
        super().__init__(self.message)

class NoSourcePlayerException(GameException):
    def __init__(self):
        self.message = "Trade must have a source player"
        super().__init__(self.message)

class NoTargetPlayerException(GameException):
    def __init__(self):
        self.message = "Trade must have a target player"
        super().__init__(self.message)

class SameSourceAndTargetPlayerException(GameException):
    def __init__(self):
        self.message = "Source and target player cannot be the same"
        super().__init__(self.message)

class NoAssetIsBeingTradedException(GameException):
    def __init__(self):
        self.message = "Trade must have some assets being traded"
        super().__init__(self.message)

class NoJailFreeCardCommunityChestException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` doesn't own a jail free card from community chest"
        super().__init__(self.message)

class NoJailFreeCardChanceException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` doesn't own a jail free card from chance"
        super().__init__(self.message)

class InvalidJailCardOfferedException(GameException):
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player `{player_name}` cannot offer `{jail_cards}` jail cards"
        super().__init__(self.message)

class InvalidJailCardRequestedException(GameException):
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player `{player_name}` cannot request `{jail_cards}` jail cards"
        super().__init__(self.message)

class ExcedingMoneyInTraddingOfferException(GameException):
    def __init__(self, player_name: str, money: int):
        self.message = f"Player `{player_name}` cannot offer `{money}` money"
        super().__init__(self.message)

class InvalidAmountOfJailCardsException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` cannot hold more than 2 jail cards"
        super().__init__(self.message)

class PlayerAlreadyInJailException(GameException):
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` is already in jail"
        super().__init__(self.message)

class NoPropertyNamedException(GameException):
    def __init__(self, property_name: str):
        self.message = f"No property named `{property_name}`"
        super().__init__(self.message)

class NotImplementedHandlerException(GameException):
    def __init__(self, handler_name: str, *args):
        if args:
            args = f"with args: {args}"
        else:
            args = ""
        self.message = f"Handler `{handler_name}` not implemented\n{args}"
        super().__init__(self.message)

class BankrupcyException(NotImplementedHandlerException):
    def __init__(self, player_name: str):
        handler_name = "BankrupcyException"
        self.message = f"Player `{player_name}` is bankrupt"
        super().__init__(handler_name, self.message)