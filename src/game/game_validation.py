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
from game.bankruptcy_request import BankruptcyRequest

if TYPE_CHECKING:
    from game.game_state import GameState
else:
    GameState = "GameState"


class GameValidation:
    """
    Static validation class for all Monopoly game actions and state changes.
    
    Provides comprehensive validation methods that check game rules compliance
    before allowing any game state modifications. Each method returns None if
    the action is valid, or a specific GameException if validation fails.
    Used by GameState methods to ensure all game actions follow official rules.
    """


    @staticmethod
    def validate_buy_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PropertyAlreadyOwnedException, PropertyMortagedException, 
            NotEnoughBalanceException, or None if valid
        """
        # Check if property is already owned by any player
        if property in game_state.is_owned:
            return PropertyAlreadyOwnedException(str(property))
        
        # Check if property is currently mortgaged (shouldn't be possible for unowned, but safety check)
        if property in game_state.mortgaged_properties:
            return PropertyMortagedException(str(property))
        
        # Check if player has sufficient balance to purchase
        if game_state.player_balances[player] < property.price:
            return NotEnoughBalanceException(property.price, game_state.player_balances[player])
        
        # Check if player already owns this property (redundant with first check, but explicit)
        if property in game_state.properties[player]:
            return PropertyAlreadyOwnedException(str(property))

        return None


    @staticmethod
    def validate_unmortgage_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PropertyNotOwnedException, PropertyNotMortgagedException,
            NotPropertyOwnerException, NotEnoughBalanceException, or None if valid
        """
        # Check if property is owned by anyone
        if property not in game_state.is_owned:
            return PropertyNotOwnedException(str(property))
        
        # Check if property is actually mortgaged
        if property not in game_state.mortgaged_properties:
            return PropertyNotMortgagedException(str(property))
        
        # Check if player is the owner of this property
        if property not in game_state.properties[player]:
            return NotPropertyOwnerException(str(property), str(player))
        
        # Check if player has sufficient balance to pay unmortgage cost (110% of mortgage value)
        if game_state.player_balances[player] < property.buyback_price:
            return NotEnoughBalanceException(property.buyback_price, game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_mortgage_property(game_state: GameState, player: Player, property: Tile) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PropertyNotOwnedException, PropertyAlreadyMortgagedException,
            NotPropertyOwnerException, PropertyHasImprovementsException, or None if valid
        """
        # Check if property is owned by anyone
        if property not in game_state.is_owned:
            return PropertyNotOwnedException(str(property))
        
        # Check if property is already mortgaged
        if property in game_state.mortgaged_properties:
            return PropertyAlreadyMortgagedException(str(property))
        
        # Check if player is the owner of this property
        if property not in game_state.properties[player]:
            return NotPropertyOwnerException(str(property), str(player))
        
        # Check if property has houses or hotels (must be sold before mortgaging)
        if isinstance(property, Property):
            if (game_state.houses[property.group][0] > 0 or 
                game_state.hotels[property.group][0] > 0):
                return PropertyHasImprovementsException(str(property))
        
        return None


    @staticmethod
    def validate_place_house(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            BuildingHousesOfTopOnHotelException, MaxHousesReachedException,
            MortgagePropertyHouseException, IncompletePropertyGroupException,
            NotEnoughBalanceException, or None if valid
        """
        # Check if property group already has a hotel (can't add houses on top of hotel)
        if game_state.hotels[property_group][0] >= 1:
            return BuildingHousesOfTopOnHotelException(str(property_group))
        
        # Check if property group already has maximum houses (4 per property)
        if game_state.houses[property_group][0] >= 4:
            return MaxHousesReachedException(str(property_group))
        
        # Check if any property in the group is mortgaged (can't build on mortgaged properties)
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHouseException(str(property))

        # Check if player owns all properties in the group (monopoly required)
        if not all(property in game_state.properties[player] for property in grouped_properties):
            return IncompletePropertyGroupException(str(property_group))
        
        # Check if player has sufficient balance to buy houses for all properties in group
        cost = property_group.house_cost() * len(grouped_properties)
        if game_state.player_balances[player] < cost:
            return NotEnoughBalanceException(cost, game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_place_hotel(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            MaxHotelsReachedException, MortgagePropertyHotelException,
            IncompletePropertyGroupException, InsufficientHousesException,
            NotEnoughBalanceException, or None if valid
        """
        # Check if property group already has a hotel
        if game_state.hotels[property_group][0] >= 1:
            return MaxHotelsReachedException(str(property_group))
        
        # Check if any property in the group is mortgaged (can't build hotels on mortgaged properties)
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHotelException(str(property))
        
        # Check if player owns all properties in the group (monopoly required)
        if not all(property in game_state.properties[player] for property in grouped_properties):
            return IncompletePropertyGroupException(str(property_group))
        
        # Check if property group has exactly 4 houses (required before hotel placement)
        number_of_houses, _ = game_state.houses[property_group]
        if number_of_houses < 4:
            return InsufficientHousesException(str(property_group), number_of_houses, 4)
        
        # Check if player has sufficient balance to buy hotel
        cost = property_group.hotel_cost()
        if game_state.player_balances[player] < cost:
            return NotEnoughBalanceException(cost, game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_sell_house(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NoHousesToSellException, MortgagePropertyHouseException,
            NotImprovementOwnerException, or None if valid
        """
        # Check if property group has any houses to sell
        if game_state.houses[property_group][0] <= 0:
            return NoHousesToSellException(str(property_group))
        
        # Check if any property in the group is mortgaged (can't sell houses on mortgaged properties)
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHouseException(str(property))
        
        # Check if player is the owner of the houses on this property group
        if game_state.houses[property_group][1] != player:
            return NotImprovementOwnerException("houses", str(property_group), str(player))
        
        return None


    @staticmethod
    def validate_sell_hotel(game_state: GameState, player: Player, property_group: PropertyGroup) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NoHotelToSellException, MortgagePropertyHotelException,
            NotImprovementOwnerException, or None if valid
        """
        # Check if property group has a hotel to sell
        if game_state.hotels[property_group][0] <= 0:
            return NoHotelToSellException(str(property_group))
        
        # Check if any property in the group is mortgaged (can't sell hotels on mortgaged properties)
        grouped_properties = game_state.board.get_properties_by_group(property_group)
        for property in grouped_properties:
            if property in game_state.mortgaged_properties:
                return MortgagePropertyHotelException(str(property))
        
        # Check if player is the owner of the hotel on this property group
        if game_state.hotels[property_group][1] != player:
            return NotImprovementOwnerException("hotel", str(property_group), str(player))
        
        return None


    @staticmethod
    def validate_send_player_to_jail(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PlayerAlreadyInJailException, or None if valid
        """
        # Check if player is already in jail
        if game_state.in_jail[player]:
            return PlayerAlreadyInJailException(str(player))
        
        return None


    @staticmethod
    def validate_count_turn_in_jail(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotInJailException, or None if valid
        """
        # Check if player is actually in jail before counting turns
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))
        
        return None


    @staticmethod
    def validate_receive_get_out_of_jail_card(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            InvalidAmountOfJailCardsException, or None if valid
        """
        # Check if player would exceed maximum jail cards (2 maximum)
        if game_state.escape_jail_cards[player] >= 2:
            return InvalidAmountOfJailCardsException(str(player))
        
        return


    @staticmethod
    def validate_get_out_of_jail(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotInJailException, or None if valid
        """
        # Check if player is actually in jail before releasing
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))
        
        return None


    @staticmethod
    def validate_use_escape_jail_card(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NoJailCardException, NotInJailException, or None if valid
        """
        # Check if player has any jail cards to use
        if game_state.escape_jail_cards[player] == 0:
            return NoJailCardException(str(player))
        
        # Check if player is actually in jail
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))
        
        return None


    @staticmethod
    def validate_pay_get_out_of_jail_fine(game_state: GameState, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotInJailException, NotEnoughBalanceException, or None if valid
        """
        # Check if player is actually in jail
        if not game_state.in_jail[player]:
            return NotInJailException(str(player))

        # Check if player has sufficient balance to pay jail fine (50₩)
        if game_state.player_balances[player] < game_state.board.get_jail_fine():
            return NotEnoughBalanceException(game_state.board.get_jail_fine(), game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_pay_tax(game_state: GameState, player: Player, tax: int) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotEnoughBalanceException, or None if valid
        """
        # Check if player has sufficient balance to pay tax
        if game_state.player_balances[player] < tax:
            return NotEnoughBalanceException(tax, game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_receive_from_players(game_state: GameState, receiver_player: Player, amount: int) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotEnoughBalanceException, or None if valid
        """
        # Check if all other players have sufficient balance to pay the receiver
        for player in game_state.players:
            if player == receiver_player:
                continue
            
            if game_state.player_balances[player] < amount:
                return NotEnoughBalanceException(amount, game_state.player_balances[player])
            
        return None


    @staticmethod
    def validate_pay_players(game_state: GameState, player: Player, amount: int) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            NotEnoughBalanceException, or None if valid
        """
        # Check if player has sufficient balance to pay all other players
        receivers_count = len(game_state.players) - 1
        if game_state.player_balances[player] < amount * receivers_count:
            return NotEnoughBalanceException(amount * receivers_count, game_state.player_balances[player])
        
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
        """
        Returns
        -------
        Optional[GameException]
            MortgagePropertyRentException, PropertyHasNoOwnerException,
            PropertyOwnerPayingRentException, NotEnoughBalanceException, or None if valid
        """
        # Check if property is mortgaged (no rent collected on mortgaged properties)
        if property in game_state.mortgaged_properties:
            return MortgagePropertyRentException(str(property))

        # Find the owner of the property
        owner = None
        for p in game_state.properties:
            if property in game_state.properties[p]:
                owner = p
                break
        
        # Check if property has an owner
        if owner is None:
            return PropertyHasNoOwnerException(str(property))
        
        # Check if player is trying to pay rent to themselves
        if owner == player:
            return PropertyOwnerPayingRentException(str(property), str(player))
        
        # Calculate rent based on property type and ownership
        if isinstance(property, Property):
            rent = property.base_rent
            # Check if owner has monopoly (all properties in group)
            if all(prop in game_state.properties[owner] 
                   for prop in game_state.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
            # Check for hotel rent
            elif game_state.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            # Check for house rent
            elif game_state.houses[property.group][0] > 0:
                rent = property.house_rent[game_state.houses[property.group][0] - 1]
        
        elif isinstance(property, Railway):
            # Count number of railways owned by the same owner
            rent_index = -1
            for prop in game_state.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]
            # Apply multiplier if specified (from Chance cards)
            if railway_factor_multiplier:
                rent *= railway_factor_multiplier

        elif isinstance(property, Utility):
            # Utility rent is based on dice roll
            assert dice_roll is not None
            dice = sum(dice_roll)
            
            # Apply specific multiplier if specified (from Chance cards)
            if utility_factor_multiplier:
                rent = utility_factor_multiplier * dice
            else:
                rent = 4 * dice
                # Check if owner owns both utilities (doubles the multiplier)
                for prop in game_state.properties[owner]:
                    if isinstance(prop, Utility):
                        rent = 10 * dice
        
        # Check if player has sufficient balance to pay calculated rent
        if game_state.player_balances[player] < rent:
            return NotEnoughBalanceException(rent, game_state.player_balances[player])
        
        return None


    @staticmethod
    def validate_trade_offer(
        game_state: GameState,
        trade_offer: TradeOffer
        ) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PlayerDoesNotExistException, NoTargetPlayerException, NoSourcePlayerException,
            SameSourceAndTargetPlayerException, PropertyNotOwnedException, NotPropertyOwnerException,
            PropertyInBothOfferedException, MortgagePropertyTradeException, PropertyHasImprovementsException,
            NegativeJailCardOfferedException, NotEnoughJailCardsException, InvalidJailCardOfferedException,
            NegativeJailCardRequestedException, InvalidJailCardRequestedException, NoAssetIsBeingTradedException,
            NegativeMoneyOfferedException, ExcedingMoneyInTraddingOfferException, NegativeMoneyRequestedException,
            or None if valid
        """
        # Check if source player exists in the game
        if trade_offer.source_player not in game_state.players:
            return PlayerDoesNotExistException(str(trade_offer.source_player))
        
        # Check if target player exists in the game
        if trade_offer.target_player not in game_state.players:
            return PlayerDoesNotExistException(str(trade_offer.target_player))
        
        # Check if target player is specified
        if not trade_offer.target_player:
            return NoTargetPlayerException()
        
        # Check if source player is specified
        if not trade_offer.source_player:
            return NoSourcePlayerException()
        
        # Check if source and target are different players
        if trade_offer.source_player == trade_offer.target_player:
            return SameSourceAndTargetPlayerException()
                
        # Validate properties offered by source player
        if trade_offer.properties_offered and len(trade_offer.properties_offered) > 0:
            for property in trade_offer.properties_offered:
                # Check if property is owned by anyone
                if property not in game_state.is_owned:
                    return PropertyNotOwnedException(str(property))
                
                # Check if source player owns the property they're offering
                if property not in game_state.properties[trade_offer.source_player]:
                    return NotPropertyOwnerException(str(property), str(trade_offer.source_player))
                
                # Check if property appears in both offered and requested lists
                if property in trade_offer.properties_requested:
                    return PropertyInBothOfferedException(str(property))
                
                # Check if property is mortgaged (mortgaged properties can't be traded)
                if property in game_state.mortgaged_properties:
                    return MortgagePropertyTradeException(str(property))
                
                # Check if property has improvements (must be sold before trading)
                if isinstance(property, Property):
                    if game_state.houses[property.group][0] > 0 or game_state.hotels[property.group][0] > 0:
                        return PropertyHasImprovementsException(str(property))
                    
        # Validate properties requested from target player
        if trade_offer.properties_requested and len(trade_offer.properties_requested) > 0:
            for property in trade_offer.properties_requested:
                # Check if property is owned by anyone
                if property not in game_state.is_owned:
                    return PropertyNotOwnedException(str(property))
                
                # Check if target player owns the property being requested
                if property not in game_state.properties[trade_offer.target_player]:
                    return NotPropertyOwnerException(str(property), str(trade_offer.target_player))
                
                # Check if property is mortgaged (mortgaged properties can't be traded)
                if property in game_state.mortgaged_properties:
                    return MortgagePropertyTradeException(str(property))
                
                # Check if property has improvements (must be sold before trading)
                if isinstance(property, Property):
                    if game_state.houses[property.group][0] > 0 or game_state.hotels[property.group][0] > 0:
                        return PropertyHasImprovementsException(str(property))
                    
        # Validate jail cards offered by source player
        if trade_offer.jail_cards_offered:
            # Check if jail cards offered is not negative
            if trade_offer.jail_cards_offered < 0:
                return NegativeJailCardOfferedException(trade_offer.jail_cards_offered)
            # Check if source player has enough jail cards to offer
            elif trade_offer.jail_cards_offered > game_state.escape_jail_cards[trade_offer.source_player]:
                return NotEnoughJailCardsException(str(trade_offer.source_player), trade_offer.jail_cards_offered)
            # Check if jail cards offered doesn't exceed maximum (2)
            elif trade_offer.jail_cards_offered > 2:
                return InvalidJailCardOfferedException(trade_offer.jail_cards_offered, trade_offer.jail_cards_offered)
            
        # Validate jail cards requested from target player
        if trade_offer.jail_cards_requested:
            # Check if jail cards requested is not negative
            if trade_offer.jail_cards_requested < 0:
                return NegativeJailCardRequestedException(trade_offer.jail_cards_requested)
            # Check if target player has enough jail cards to give
            elif trade_offer.jail_cards_requested > game_state.escape_jail_cards[trade_offer.target_player]:
                return NotEnoughJailCardsException(str(trade_offer.target_player), trade_offer.jail_cards_requested)
            # Check if jail cards requested doesn't exceed maximum (2)
            elif trade_offer.jail_cards_requested > 2:
                return InvalidJailCardRequestedException(trade_offer.jail_cards_requested, trade_offer.jail_cards_requested)

        # Check if trade contains at least one asset (not just money)
        if trade_offer.properties_offered == [] and trade_offer.properties_requested == [] and\
            trade_offer.jail_cards_offered == 0 and trade_offer.jail_cards_requested == 0:
            return NoAssetIsBeingTradedException()

        # Validate money offered by source player
        if trade_offer.money_offered:
            # Check if money offered is not negative
            if trade_offer.money_offered < 0:
                return NegativeMoneyOfferedException(trade_offer.money_offered)
            
            # Check if source player has enough money to offer
            if trade_offer.money_offered > game_state.player_balances[trade_offer.source_player]:
                return ExcedingMoneyInTraddingOfferException(str(trade_offer.source_player), trade_offer.money_offered)
        
        # Validate money requested from target player
        if trade_offer.money_requested:
            # Check if money requested is not negative
            if trade_offer.money_requested < 0:
                return NegativeMoneyRequestedException(trade_offer.money_requested)
            
            # Check if target player has enough money to give
            if trade_offer.money_requested > game_state.player_balances[trade_offer.target_player]:
                return ExcedingMoneyInTraddingOfferException(str(trade_offer.target_player), trade_offer.money_requested)
        
        return None


    @staticmethod
    def validate_property_in_trade_offer(game_state: GameState, property: Tile, player: Player) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PropertyNotOwnedException, NotPropertyOwnerException,
            MortgagePropertyTradeException, PropertyHasImprovementsException, or None if valid
        """
        # Check if property is owned by anyone
        if property not in game_state.is_owned:
            return PropertyNotOwnedException(str(property))
        
        # Check if specified player owns the property
        if property not in game_state.properties[player]:
            return NotPropertyOwnerException(str(property), str(player))
        
        # Check if property is mortgaged (mortgaged properties can't be traded)
        if property in game_state.mortgaged_properties:
            return MortgagePropertyTradeException(str(property))
        
        # Check if property has improvements (must be sold before trading)
        if isinstance(property, Property):
            if game_state.houses[property.group][0] > 0 or game_state.hotels[property.group][0] > 0:
                return PropertyHasImprovementsException(str(property))
            
        return None


    @staticmethod
    def validate_bankruptcy_request(game_state: GameState, player: Player, bankruptcy_model: BankruptcyRequest) -> Optional[GameException]:
        """
        Returns
        -------
        Optional[GameException]
            PlayerDoesNotExistException, or validation errors from constituent actions, or None if valid
        """
        # Check if player exists in the game
        if player not in game_state.players:
            return PlayerDoesNotExistException(str(player))
        
        # Separate downgrading suggestions by type (houses vs hotels)
        group_properties_for_houses = []
        group_properties_for_hotels = []

        for group_property in bankruptcy_model.downgrading_suggestions:
            # Check if group has houses to downgrade
            if game_state.houses[group_property][0] > 0:
                group_properties_for_houses.append(group_property)
            # Check if group has hotels to downgrade
            elif game_state.hotels[group_property][0] > 0:
                group_properties_for_hotels.append(group_property)

        # Validate each house selling suggestion
        for group_property in group_properties_for_houses:
            if error := GameValidation.validate_sell_house(game_state, player, group_property):
                return error
        
        # Validate each hotel selling suggestion
        for group_property in group_properties_for_hotels:
            if error := GameValidation.validate_sell_hotel(game_state, player, group_property):
                return error
            
        # Validate each mortgaging suggestion
        for property in bankruptcy_model.mortgaging_suggestions:
            if error := GameValidation.validate_mortgage_property(game_state, player, property):
                return error
            
        # Validate each trade offer suggestion
        for trade_offer in bankruptcy_model.trade_offers:
            if error := GameValidation.validate_trade_offer(game_state, trade_offer):
                return error
            
        return None