class GameException(Exception):
    """Base class for all game exceptions."""
    pass


class TileCannotBePurchasedException(GameException):
    """Raised when attempting to purchase a tile that cannot be bought."""
    
    def __init__(self, tile_name: str):
        self.message = f"Tile {tile_name} cannot be purchased"
        super().__init__(self.message)


class PropertyAlreadyOwnedException(GameException):
    """Raised when attempting to purchase or assign a property that is already owned."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is already owned"
        super().__init__(self.message)


class PropertyNotOwnedException(GameException):
    """Raised when attempting an action on a property that has no owner."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is not owned"
        super().__init__(self.message)


class PropertyAlreadyMortgagedException(GameException):
    """Raised when attempting to mortgage a property that is already mortgaged."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is already mortgaged"
        super().__init__(self.message)


class NotPropertyOwnerException(GameException):
    """Raised when a player attempts an action on a property they don't own."""
    
    def __init__(self, property_name: str, player_name: str):
        self.message = f"Player {player_name} does not own property {property_name}"
        super().__init__(self.message)


class PropertyMortagedException(GameException):
    """Raised when attempting to purchase a mortgaged property."""
    
    def __init__(self, property_name: str):
        self.message = f"Mortgaged property {property_name} cannot be bought"
        super().__init__(self.message)


class PropertyOwnerPayingRentException(GameException):
    """Raised when a player attempts to pay rent on their own property."""
    
    def __init__(self, property_name: str, player_name: str):
        self.message = f"Cannot pay rent to self for property {property_name} owned by {player_name}"
        super().__init__(self.message)


class PropertyHasImprovementsException(GameException):
    """Raised when attempting to mortgage or trade a property with houses/hotels."""
    
    def __init__(self, property_name: str):
        self.message = f"Cannot mortgage property {property_name} with houses/hotels"
        super().__init__(self.message)


class MaxHousesReachedException(GameException):
    """Raised when attempting to build houses on a property group that already has 4 houses."""
    
    def __init__(self, group_name: str):
        self.message = f"Maximum houses already placed on {group_name}"
        super().__init__(self.message)


class IncompletePropertyGroupException(GameException):
    """Raised when attempting to build on a property group without owning all properties."""
    
    def __init__(self, group_name: str):
        self.message = f"Must own all properties in {group_name} group"
        super().__init__(self.message)


class MaxHotelsReachedException(GameException):
    """Raised when attempting to build a hotel on a property group that already has one."""
    
    def __init__(self, group_name: str):
        self.message = f"Hotel already exists on {group_name}"
        super().__init__(self.message)


class InsufficientHousesException(GameException):
    """Raised when attempting to build a hotel without the required 4 houses."""
    
    def __init__(self, group_name: str, current: int, required: int):
        self.message = f"Need {required} houses on {group_name} (currently has {current})"
        super().__init__(self.message)


class NoHousesToSellException(GameException):
    """Raised when attempting to sell houses from a property group that has none."""
    
    def __init__(self, group_name: str):
        self.message = f"No houses to sell on {group_name}"
        super().__init__(self.message)


class NoHotelToSellException(GameException):
    """Raised when attempting to sell a hotel from a property group that has none."""
    
    def __init__(self, group_name: str):
        self.message = f"No hotel to sell on {group_name}"
        super().__init__(self.message)


class NotImprovementOwnerException(GameException):
    """Raised when a player attempts to sell buildings they don't own."""
    
    def __init__(self, improvement_type: str, group_name: str, player_name: str):
        self.message = f"Player {player_name} does not own the {improvement_type} on {group_name}"
        super().__init__(self.message)


class NoJailCardException(GameException):
    """Raised when a player attempts to use a Get Out of Jail Free card they don't have."""
    
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} has no jail free card"
        super().__init__(self.message)


class NotInJailException(GameException):
    """Raised when attempting jail-related actions on a player who is not in jail."""
    
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} is not in jail"
        super().__init__(self.message)


class PropertyHasNoOwnerException(GameException):
    """Raised when attempting to collect rent from a property with no owner."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} has no owner"
        super().__init__(self.message)


class NotEnoughBalanceException(GameException):
    """Raised when a player attempts a transaction they cannot afford."""
    
    def __init__(self, price: int, balance: int):
        self.price = price
        self.balance = balance
        self.message = f"Not enough balance to complete the transaction. Price: {price}, Balance: {balance}"
        super().__init__(self.message)


class MortgagePropertyRentException(GameException):
    """Raised when attempting to collect rent from a mortgaged property."""
    
    def __init__(self, property_name: str):
        self.message = f"Cannot pay rent on mortgaged property {property_name}"
        super().__init__(self.message)


class MortgagePropertyHouseException(GameException):
    """Raised when attempting to build or sell houses on a mortgaged property."""
    
    def __init__(self, property_name: str):
        self.message = f"Cannot build/sell house on mortgaged property {property_name}"
        super().__init__(self.message)


class MortgagePropertyHotelException(GameException):
    """Raised when attempting to build or sell hotels on a mortgaged property."""
    
    def __init__(self, property_name: str):
        self.message = f"Cannot build/sell hotel on mortgaged property {property_name}"
        super().__init__(self.message)


class PlayerInJailException(GameException):
    """Raised when attempting to move a player who is currently in jail."""
    
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} is in jail"
        super().__init__(self.message)


class BuildingHousesOfTopOnHotelException(GameException):
    """Raised when attempting to build houses on a property group that already has a hotel."""
    
    def __init__(self, property_group: str):
        self.message = f"Cannot build houses if there is an hotel already place on {property_group} group"
        super().__init__(self.message)


class PropertyNotMortgagedException(GameException):
    """Raised when attempting to unmortgage a property that is not mortgaged."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is not mortgaged"
        super().__init__(self.message)


class PlayerDoesNotExistException(GameException):
    """Raised when referencing a player who is not in the current game."""
    
    def __init__(self, player_name: str):
        self.message = f"Player {player_name} does not exist"
        super().__init__(self.message)


class PropertyInBothOfferedException(GameException):
    """Raised when a trade offer includes the same property in both offered and requested lists."""
    
    def __init__(self, property_name: str):
        self.message = f"Property {property_name} is in both offered and requested properties"
        super().__init__(self.message)


class MortgagePropertyTradeException(GameException):
    """Raised when attempting to trade a mortgaged property."""
    
    def __init__(self, property_name: str):
        self.message = f"Cannot trade mortgaged property {property_name}"
        super().__init__(self.message)


class NegativeMoneyOfferedException(GameException):
    """Raised when a trade offer includes negative money amounts."""
    
    def __init__(self):
        self.message = "Money offered cannot be negative"
        super().__init__(self.message)


class NegativeJailCardOfferedException(GameException):
    """Raised when a trade offer includes negative jail card amounts."""
    
    def __init__(self):
        self.message = "Jail cards offered cannot be negative"
        super().__init__(self.message)


class NegativeMoneyRequestedException(GameException):
    """Raised when a trade request includes negative money amounts."""
    
    def __init__(self):
        self.message = "Money requested cannot be negative"
        super().__init__(self.message)


class NegativeJailCardRequestedException(GameException):
    """Raised when a trade request includes negative jail card amounts."""
    
    def __init__(self):
        self.message = "Jail cards requested cannot be negative"
        super().__init__(self.message)


class NotEnoughJailCardsException(GameException):
    """Raised when a player attempts to trade more jail cards than they possess."""
    
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player {player_name} has only {jail_cards} jail cards"
        super().__init__(self.message)


class NoSourcePlayerException(GameException):
    """Raised when a trade offer is missing a source player."""
    
    def __init__(self):
        self.message = "Trade must have a source player"
        super().__init__(self.message)


class NoTargetPlayerException(GameException):
    """Raised when a trade offer is missing a target player."""
    
    def __init__(self):
        self.message = "Trade must have a target player"
        super().__init__(self.message)


class SameSourceAndTargetPlayerException(GameException):
    """Raised when a trade offer has the same player as both source and target."""
    
    def __init__(self):
        self.message = "Source and target player cannot be the same"
        super().__init__(self.message)


class NoAssetIsBeingTradedException(GameException):
    """Raised when a trade offer contains no assets (only money exchange)."""
    
    def __init__(self):
        self.message = "Trade must have some assets being traded"
        super().__init__(self.message)


class NoJailFreeCardCommunityChestException(GameException):
    """Raised when a player attempts to use a Community Chest jail card they don't have."""
    
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` doesn't own a jail free card from community chest"
        super().__init__(self.message)


class NoJailFreeCardChanceException(GameException):
    """Raised when a player attempts to use a Chance jail card they don't have."""
    
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` doesn't own a jail free card from chance"
        super().__init__(self.message)


class InvalidJailCardOfferedException(GameException):
    """Raised when a trade offer includes an invalid number of jail cards."""
    
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player `{player_name}` cannot offer `{jail_cards}` jail cards"
        super().__init__(self.message)


class InvalidJailCardRequestedException(GameException):
    """Raised when a trade request includes an invalid number of jail cards."""
    
    def __init__(self, player_name: str, jail_cards: int):
        self.message = f"Player `{player_name}` cannot request `{jail_cards}` jail cards"
        super().__init__(self.message)


class ExcedingMoneyInTraddingOfferException(GameException):
    """Raised when a trade offer exceeds the player's available money."""
    
    def __init__(self, player_name: str, money: int):
        self.message = f"Player `{player_name}` cannot offer `{money}` money"
        super().__init__(self.message)


class InvalidAmountOfJailCardsException(GameException):
    """Raised when a player would exceed the maximum jail cards limit (2)."""
    
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` cannot hold more than 2 jail cards"
        super().__init__(self.message)


class PlayerAlreadyInJailException(GameException):
    """Raised when attempting to send a player to jail who is already there."""
    
    def __init__(self, player_name: str):
        self.message = f"Player `{player_name}` is already in jail"
        super().__init__(self.message)


class NoPropertyNamedException(GameException):
    """Raised when referencing a property that doesn't exist on the board."""
    
    def __init__(self, property_name: str):
        self.message = f"No property named `{property_name}`"
        super().__init__(self.message)


class NotImplementedHandlerException(GameException):
    """Raised when encountering a game situation that hasn't been implemented yet."""
    
    def __init__(self, handler_name: str, *args):
        if args:
            args = f"with args: {args}"
        else:
            args = ""
        self.message = f"Handler `{handler_name}` not implemented\n{args}"
        super().__init__(self.message)


class BankrupcyException(NotImplementedHandlerException):
    """Raised when a player is declared bankrupt and eliminated from the game."""
    
    def __init__(self, player_name: str):
        handler_name = "BankrupcyException"
        self.message = f"Player `{player_name}` is bankrupt"
        super().__init__(handler_name, self.message)