# validation/game_validation.py
from typing import Optional, TYPE_CHECKING
from exceptions.exceptions import GameException
from exceptions.exceptions import *
from game.player import Player
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.trade_offer import TradeOffer
from models.tile import Tile

if TYPE_CHECKING:
    from game.game_state import GameState
else:
    GameState = "GameState"

class GameValidation:
    @staticmethod
    def validate_buy_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        if property in game_state.is_owned:
            return PropertyAlreadyOwnedException(str(property))
        
        if game_state.player_balances[player] < property.price:
            return NotEnoughBalanceException(property.price, game_state.player_balances[player])
        
        if property in game_state.properties[player]:
            return PropertyAlreadyOwnedException(str(property))

        return None
    
    
    @staticmethod
    def validate_unmortgage_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        if property not in game_state.is_owned:
            return PropertyNotOwnedException(str(property))
        
        if property not in game_state.mortgaged_properties:
            return PropertyNotMortgagedException(str(property))
        
        if property not in game_state.properties[player]:
            return NotPropertyOwnerException(str(property), str(player))
        
        if game_state.player_balances[player] < property.buyback_price:
            return NotEnoughBalanceException(property.buyback_price, game_state.player_balances[player])
        

    @staticmethod
    def validate_mortgage_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        if property not in game_state.is_owned:
            return PropertyNotOwnedException(str(property))
        
        if property in game_state.mortgaged_properties:
            return PropertyAlreadyMortgagedException(str(property))
        
        if property not in game_state.properties[player]:
            return NotPropertyOwnerException(str(property), str(player))
        
        if isinstance(property, Property):
            if (game_state.houses[property.group][0] > 0 or 
                game_state.hotels[property.group][0] > 0):
                return PropertyHasImprovementsException(str(property))
        
        return None

    @staticmethod
    def validate_place_house(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        if game_state.hotels[property_group][0] >= 1:
            return BuildingHousesOfTopOnHotelException(str(property_group))
        
        if game_state.houses[property_group][0] >= 4:
            return MaxHousesReachedException(str(property_group))
        
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHouseException(str(property))

        group_properties = game_state.board.get_properties_by_group(property_group)
        if not all(property in game_state.properties[player] for property in group_properties):
            return IncompletePropertyGroupException(str(property_group))
        
        cost = property_group.house_cost() * len(group_properties)
        if game_state.player_balances[player] < cost:
            return NotEnoughBalanceException(cost, game_state.player_balances[player])
        
        return None

    @staticmethod
    def validate_place_hotel(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        if game_state.hotels[property_group][0] >= 1:
            return MaxHotelsReachedException(str(property_group))
        
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHotelException(str(property))
        
        group_properties = game_state.board.get_properties_by_group(property_group)
        if not all(property in game_state.properties[player] for property in group_properties):
            return IncompletePropertyGroupException(str(property_group))
        
        if game_state.houses[property_group][0] < 4:
            return InsufficientHousesException(str(property_group), 
                                             game_state.houses[property_group][0], 4)
        
        cost = property_group.hotel_cost()
        if game_state.player_balances[player] < cost:
            return NotEnoughBalanceException(cost, game_state.player_balances[player])
        
        return None

    @staticmethod
    def validate_sell_house(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        if game_state.houses[property_group][0] == 0:
            return NoHousesToSellException(str(property_group))
        
        if game_state.houses[property_group][1] != player:
            return NotImprovementOwnerException("houses", str(property_group), str(player))
        
        return None

    @staticmethod
    def validate_sell_hotel(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        if game_state.hotels[property_group][0] == 0:
            return NoHotelToSellException(str(property_group))
        
        if game_state.hotels[property_group][1] != player:
            return NotImprovementOwnerException("hotel", str(property_group), str(player))
        
        return None
    
    @staticmethod
    def validate_get_out_of_jail(game_state: GameState, player: Player) -> Optional[GameException]:
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))
        
        return None 

    @staticmethod
    def validate_use_escape_jail_card(game_state: GameState, player: Player) -> Optional[GameException]:
        if game_state.escape_jail_cards[player] == 0:
            return NoJailCardException(str(player))
        
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))
        
        return None
    
    @staticmethod
    def validate_pay_get_out_of_jail_fine(game_state: GameState, player: Player) -> Optional[GameException]:
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))

        if game_state.player_balances[player] < game_state.board.get_jail_fine():
            return NotEnoughBalanceException(game_state.board.get_jail_fine(), game_state.player_balances[player])
        
        return None
    
    @staticmethod
    def validate_pay_tax(game_state: GameState, player: Player, tax: int) -> Optional[GameException]:
        if game_state.player_balances[player] < tax:
            return NotEnoughBalanceException(tax, game_state.player_balances[player])
        
        return None

    @staticmethod
    def validate_pay_rent(
        game_state: GameState,
        player: Player, 
        property: Tile, 
        dice_roll: tuple[int, int] = None,
        utility_factor_multiplier: int = None,
        railway_factor_multiplier: int = None
        ) -> Optional[GameException]:

        if property in game_state.mortgaged_properties:
            return MortgagePropertyRentException(str(property))

        owner = None
        for p in game_state.properties:
            if property in game_state.properties[p]:
                owner = p
                break
        
        if owner is None:
            return PropertyHasNoOwnerException(str(property))
        
        if owner == player:
            return PropertyOwnerPayingRentException(str(property), str(player))
        
        if isinstance(property, Property):
            rent = property.base_rent
            if all(prop in game_state.properties[owner] 
                   for prop in game_state.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
            elif game_state.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            elif game_state.houses[property.group][0] > 0:
                rent = property.house_rent[game_state.houses[property.group][0] - 1]
        
        elif isinstance(property, Railway):
            rent_index = -1
            for prop in game_state.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]
            if railway_factor_multiplier:
                rent *= railway_factor_multiplier

        elif isinstance(property, Utility):
            assert dice_roll is not None
            dice = sum(dice_roll)
            
            if utility_factor_multiplier:
                rent = utility_factor_multiplier * dice
            else:
                rent = 4 * dice
                for prop in game_state.properties[owner]:
                    if isinstance(prop, Utility):
                        rent = 10 * dice
            
        if game_state.player_balances[player] < rent:
            return NotEnoughBalanceException(rent, game_state.player_balances[player])
        
        return None
    

    @staticmethod
    def validate_trade_offer(
        game_state: GameState,
        trade_offer: TradeOffer
        ) -> Optional[GameException]:

        if trade_offer.source_player not in game_state.players:
            return PlayerDoesNotExistException(str(trade_offer.source_player))
        
        if not trade_offer.target_player:
            return NoTargetPlayerException()
                
        if trade_offer.properties_offered and len(trade_offer.properties_offered) > 0:
            for property in trade_offer.properties_offered:
                if property not in game_state.is_owned:
                    return PropertyNotOwnedException(str(property))
                
                if property not in game_state.properties[trade_offer.source_player]:
                    return NotPropertyOwnerException(str(property), str(trade_offer.source_player))
                
                if property in trade_offer.properties_requested:
                    return PropertyInBothOfferedException(str(property))
                
                if property in game_state.mortgaged_properties:
                    return MortgagePropertyTradeException(str(property))
                
                if isinstance(property, Property):
                    if game_state.houses[property.group][0] > 0 or game_state.hotels[property.group][0] > 0:
                        return PropertyHasImprovementsException(str(property))
                    
        if trade_offer.properties_requested and len(trade_offer.properties_requested) > 0:
            for property in trade_offer.properties_requested:
                if property not in game_state.is_owned:
                    return PropertyNotOwnedException(str(property))
                
                if property not in game_state.properties[trade_offer.target_player]:
                    return NotPropertyOwnerException(str(property), str(trade_offer.target_player))
                
                if property in game_state.mortgaged_properties:
                    return MortgagePropertyTradeException(str(property))
                
                if isinstance(property, Property):
                    if game_state.houses[property.group][0] > 0 or game_state.hotels[property.group][0] > 0:
                        return PropertyHasImprovementsException(str(property))
                    
        if trade_offer.jail_cards_offered:
            if trade_offer.jail_cards_offered < 0:
                return NegativeJailCardOfferedException(trade_offer.jail_cards_offered)
            elif trade_offer.jail_cards_offered > game_state.escape_jail_cards[trade_offer.source_player]:
                return NotEnoughJailCardsException(str(trade_offer.source_player), trade_offer.jail_cards_offered)
            
        if trade_offer.jail_cards_requested:
            if trade_offer.jail_cards_requested < 0:
                return NegativeJailCardRequestedException(trade_offer.jail_cards_requested)
            elif trade_offer.jail_cards_requested > game_state.escape_jail_cards[trade_offer.target_player]:
                return NotEnoughJailCardsException(str(trade_offer.target_player), trade_offer.jail_cards_requested)
            

        # verify if there is only money offered or requested
        if trade_offer.properties_offered == [] and trade_offer.properties_requested == [] and\
            trade_offer.jail_cards_offered == 0 and trade_offer.jail_cards_requested == 0:
            return NoAssetIsBeingTradedException()

        if trade_offer.money_offered:
            if trade_offer.money_offered < 0:
                return NegativeMoneyOfferedException(trade_offer.money_offered)
        
        if trade_offer.money_requested:
            if trade_offer.money_requested < 0:
                return NegativeMoneyRequestedException(trade_offer.money_requested)
        
                    
        return None