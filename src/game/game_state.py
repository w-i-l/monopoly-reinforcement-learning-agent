from game.player import Player
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.trade_offer import TradeOffer
from models.tile import Tile
from exceptions.exceptions import *
from models.other_tiles import Jail, Go, GoToJail, FreeParking, Taxes, Chance, CommunityChest
from models.board import Board
from game.game_validation import GameValidation
from game.bankruptcy_request import BankruptcyRequest


CAN_PRINT = False
def custom_print(*args, **kwargs):
    if CAN_PRINT:
        print(*args, **kwargs)


class GameState:
    """
    Central state manager for Monopoly game containing all game data and state transitions.
    
    Maintains the complete state of a Monopoly game including player positions, balances,
    property ownership, building development, and jail status. All state modifications
    must go through this class's methods to ensure game rule compliance via validation.
    Acts as the single source of truth for the game's current state.
    
    Attributes
    ----------
    players : list[Player]
        List of all players in the game
    current_player_index : int
        Index of the current player whose turn it is
    properties : dict[Player, list[Tile]]
        Mapping of players to their owned properties
    houses : dict[PropertyGroup, tuple[int, Player]]
        House count and owner for each property group (count, owner)
    hotels : dict[PropertyGroup, tuple[int, Player]]
        Hotel count and owner for each property group (count, owner)
    escape_jail_cards : dict[Player, int]
        Number of Get Out of Jail Free cards each player has
    in_jail : dict[Player, bool]
        Whether each player is currently in jail
    player_positions : dict[Player, int]
        Current board position (0-39) for each player
    player_balances : dict[Player, int]
        Current cash balance for each player
    is_owned : set[Tile]
        Set of all properties that are owned by any player
    mortgaged_properties : set[Tile]
        Set of all properties that are currently mortgaged
    doubles_rolled : int
        Number of consecutive doubles rolled by current player
    board : Board
        The game board containing all tiles and their properties
    turns_in_jail : dict[Player, int]
        Number of turns each player has spent in jail
    """


    def __init__(self, players: list[Player]):
        """
        Initialize game state for the given players.
        
        Parameters
        ----------
        players : list[Player]
            List of Player objects participating in the game
        """
        self.players = players
        self.current_player_index = 0
        self.properties = { player: [] for player in players }
        self.houses = {
            group: (0, None) for group in PropertyGroup  # (count, owner)
        }
        self.hotels = {
            group: (0, None) for group in PropertyGroup  # (count, owner)
        }
        self.escape_jail_cards = { player: 0 for player in players }
        self.in_jail = { player: False for player in players }
        self.player_positions = { player: 0 for player in players }
        self.player_balances = { player: 1500 for player in players }
        self.is_owned = set()
        self.mortgaged_properties = set()
        self.doubles_rolled = 0
        self.board = Board()
        self.turns_in_jail = { player: 0 for player in players }


    ############## MOVING ACTIONS ##############


    def move_player(self, player: Player, dice: tuple[int, int]):
        """
        Move player forward on the board based on dice roll.
        
        Parameters
        ----------
        player : Player
            Player to move
        dice : tuple[int, int]
            Dice roll values
        
        Raises
        ------
        PlayerInJailException
            If player is in jail and cannot move normally
        """
        # Check if player is in jail (cannot move normally)
        if self.in_jail[player]:
            custom_print(f"{player} is in jail")
            self.print_debug_info()
            raise PlayerInJailException(player)

        # Track consecutive doubles for Go To Jail rule
        self.doubles_rolled += 1 if dice[0] == dice[1] else 0
        if self.doubles_rolled == 3:
            self.send_player_to_jail(player)
            custom_print(f"{player} rolled doubles 3 times and is sent to jail")
            return
        
        rolled = dice[0] + dice[1]
        self.player_positions[player] += rolled
        
        # Check if player passed Go and collect 200₩
        if self.player_positions[player] >= 40:
            custom_print(f"{player} passed Go and received 200₩")
            self.player_balances[player] += 200

        # Normalize position to board size (40 tiles)
        self.player_positions[player] %= 40
        custom_print(f"{player} landed on {self.board.tiles[self.player_positions[player]]}")
        
        # Check if player landed on Go To Jail tile
        if self.board.has_landed_on_go_to_jail(self.player_positions[player]):
            self.send_player_to_jail(player)
            custom_print(f"{player} landed on Go To Jail and is sent to jail")
            return


    def move_player_backwards(self, player: Player, steps: int):
        """
        Move player backwards on the board (used by Chance cards).
        
        Parameters
        ----------
        player : Player
            Player to move backwards
        steps : int
            Number of steps to move backwards
        """
        # We don't need to worry about negative positions
        # because of the placement of the activation tiles on the board
        self.player_positions[player] -= steps
        custom_print(f"{player} moved backwards {steps} steps")

        # Player can land on 3 tiles: Orange Property, Community Chest, Taxes

        # Check if player landed on Community Chest
        # implemented in game manager, by placing community chest tile checking
        # after the chance
        community_chest_tile = self.board.has_land_on_community_chest(self.player_positions[player])
        if community_chest_tile:
            custom_print(f"{player} landed on Community Chest")
            return

        # Check if player landed on Taxes
        # implemented in game manager, by placing tax tile checking
        # after the chance
        tax_tile = self.board.has_landed_on_tax(self.player_positions[player])
        if tax_tile:
            custom_print(f"{player} landed on {tax_tile.name} and paid {tax_tile.tax}₩")
            return
        
        # Landing on Orange Property
        # paying rent/ buying property handled in chance manager
        return


    def move_player_to_property(self, player: Player, property: Tile):
        """
        Move player directly to a specific property (used by Chance cards).
        
        Parameters
        ----------
        player : Player
            Player to move
        property : Tile
            Target property tile
        """
        property_position = property.id
        player_position = self.player_positions[player]

        # Check if the player has passed Go and collect 200₩
        if property_position < player_position:
            self.player_balances[player] += 200
            custom_print(f"{player} passed Go and received 200₩")

        self.player_positions[player] = property_position


    def move_player_to_start(self, player: Player):
        """
        Move player to the Start tile and collect 200₩.
        
        Parameters
        ----------
        player : Player
            Player to move to start
        """
        self.player_positions[player] = 0
        self.player_balances[player] += 200
        custom_print(f"{player} moved to Start")


    ############## PROPERTY ACTIONS ##############


    def buy_property(self, player: Player, property: Tile):
        """
        Purchase an unowned property for the player.
        
        Parameters
        ----------
        player : Player
            Player purchasing the property
        property : Tile
            Property to purchase
        
        Raises
        ------
        GameException
            If purchase is invalid (already owned, insufficient funds, etc.)
        """
        if error := GameValidation.validate_buy_property(self, player, property):
            self.print_debug_info()
            raise error
    
        self.properties[player].append(property)
        self.is_owned.add(property)
        self.player_balances[player] -= property.price

        custom_print(f"{player} bought {property} remaining balance: {self.player_balances[player]}₩")
        custom_print(self.properties)


    def mortgage_property(self, player: Player, property: Tile):
        """
        Mortgage a property to get immediate cash at half property value.
        
        Parameters
        ----------
        player : Player
            Player mortgaging the property
        property : Tile
            Property to mortgage
        
        Raises
        ------
        GameException
            If mortgage is invalid (not owned, has improvements, etc.)
        """
        if error := GameValidation.validate_mortgage_property(self, player, property):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} mortaging {property}")
        self.mortgaged_properties.add(property)
        self.player_balances[player] += property.mortgage


    def unmortgage_property(self, player: Player, property: Tile):
        """
        Unmortgage a property by paying 110% of mortgage value.
        
        Parameters
        ----------
        player : Player
            Player unmortgaging the property
        property : Tile
            Property to unmortgage
        
        Raises
        ------
        GameException
            If unmortgage is invalid (not mortgaged, insufficient funds, etc.)
        """
        if error := GameValidation.validate_unmortgage_property(self, player, property):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} unmortaging {property}")
        self.mortgaged_properties.remove(property)
        self.player_balances[player] -= property.buyback_price


    ############## HOUSES AND HOTELS ##############


    def update_property_group(self, player: Player, property_group: PropertyGroup):
        """
        Upgrade property group with next development level (house or hotel).
        
        Parameters
        ----------
        player : Player
            Player developing the property group
        property_group : PropertyGroup
            Property group to develop
        """
        # Upgrade to hotel if already has 4 houses, otherwise add house
        if self.houses[property_group][0] == 4:
            self.place_hotel(player, property_group)
        else:
            self.place_house(player, property_group)


    def place_house(self, player: Player, property_group: PropertyGroup):
        """
        Add one house to all properties in the group.
        
        Parameters
        ----------
        player : Player
            Player placing houses
        property_group : PropertyGroup
            Property group to develop
        
        Raises
        ------
        GameException
            If house placement is invalid (no monopoly, insufficient funds, etc.)
        """
        if error := GameValidation.validate_place_house(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} placed a house on {property_group}")
        cost = property_group.house_cost() * len(self.board.get_properties_by_group(property_group))
        self.houses[property_group] = (self.houses[property_group][0] + 1, player)
        self.player_balances[player] -= cost


    def place_hotel(self, player: Player, property_group: PropertyGroup):
        """
        Replace 4 houses with 1 hotel on all properties in the group.
        
        Parameters
        ----------
        player : Player
            Player placing hotel
        property_group : PropertyGroup
            Property group to develop
        
        Raises
        ------
        GameException
            If hotel placement is invalid (less than 4 houses, insufficient funds, etc.)
        """
        if error := GameValidation.validate_place_hotel(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} placed a hotel on {property_group}")
        cost = property_group.hotel_cost()
        self.hotels[property_group] = (1, player)
        self.houses[property_group] = (0, player)  # Houses are replaced by hotel
        self.player_balances[player] -= cost


    def downgrade_property_group(self, player: Player, property_group: PropertyGroup):
        """
        Downgrade property group by one development level (hotel to houses or sell house).
        
        Parameters
        ----------
        player : Player
            Player downgrading the property group
        property_group : PropertyGroup
            Property group to downgrade
        """
        # Downgrade hotel to 4 houses or sell one house level
        if self.hotels[property_group][0] == 1:
            self.sell_hotel(player, property_group)
        else:
            self.sell_house(player, property_group)


    def sell_house(self, player: Player, property_group: PropertyGroup):
        """
        Sell one house level from all properties in the group for half price.
        
        Parameters
        ----------
        player : Player
            Player selling houses
        property_group : PropertyGroup
            Property group to downgrade
        
        Raises
        ------
        GameException
            If house sale is invalid (no houses to sell, mortgaged properties, etc.)
        """
        if error := GameValidation.validate_sell_house(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} sold a house on {property_group}")
        group_properties = self.board.get_properties_by_group(property_group)
        cost = property_group.house_cost() * len(group_properties) // 2
        self.houses[property_group] = (self.houses[property_group][0] - 1, player)
        self.player_balances[player] += cost

        # Clear ownership if no more houses or hotels
        if self.houses[property_group][0] == 0:
            self.houses[property_group] = (0, None)
            self.hotels[property_group] = (0, None)


    def sell_hotel(self, player: Player, property_group: PropertyGroup):
        """
        Sell hotel and replace with 4 houses for half hotel price.
        
        Parameters
        ----------
        player : Player
            Player selling hotel
        property_group : PropertyGroup
            Property group to downgrade
        
        Raises
        ------
        GameException
            If hotel sale is invalid (no hotel to sell, mortgaged properties, etc.)
        """
        if error := GameValidation.validate_sell_hotel(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} sold a hotel on {property_group}")
        cost = property_group.hotel_cost() // 2
        self.hotels[property_group] = (0, player)
        self.houses[property_group] = (4, player)  # Hotel becomes 4 houses
        self.player_balances[player] += cost


    ############## JAIL ##############


    def send_player_to_jail(self, player: Player):
        """
        Send player to jail and reset doubles counter.
        
        Parameters
        ----------
        player : Player
            Player to send to jail
        
        Raises
        ------
        GameException
            If player is already in jail
        """
        if error := GameValidation.validate_send_player_to_jail(self, player):
            self.print_debug_info()
            raise error
        
        self.in_jail[player] = True
        self.doubles_rolled = 0
        self.turns_in_jail[player] = 0
        self.player_positions[player] = self.board.get_jail_id()
        custom_print(f"{player} is sent to jail")


    def get_out_of_jail(self, player: Player):
        """
        Release player from jail by rolling doubles.
        
        Used **ONLY** when player rolls a double.
        
        Parameters
        ----------
        player : Player
            Player getting out of jail
        
        Raises
        ------
        GameException
            If player is not in jail
        """
        if error := GameValidation.validate_get_out_of_jail(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} got out of jail by rolling doubles")
        self.in_jail[player] = False
        self.player_positions[player] = 10  # Just Visiting position
        self.turns_in_jail[player] = 0


    def receive_get_out_of_jail_card(self, player: Player):
        """
        Give player a Get Out of Jail Free card.
        
        Parameters
        ----------
        player : Player
            Player receiving the card
        
        Raises
        ------
        GameException
            If player already has maximum jail cards (2)
        """
        if error := GameValidation.validate_receive_get_out_of_jail_card(self, player):
            self.print_debug_info()
            raise error
        
        self.escape_jail_cards[player] += 1
        custom_print(f"{player} received a Get Out of Jail card")


    def use_escape_jail_card(self, player: Player):
        """
        Use a Get Out of Jail Free card to escape jail.
        
        Parameters
        ----------
        player : Player
            Player using the card
        
        Raises
        ------
        GameException
            If player has no jail cards or is not in jail
        """
        if error := GameValidation.validate_use_escape_jail_card(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} used a Get Out of Jail card")
        self.escape_jail_cards[player] -= 1
        self.in_jail[player] = False
        self.player_positions[player] = 10  # Just Visiting position
        self.turns_in_jail[player] = 0


    def pay_get_out_of_jail_fine(self, player: Player):
        """
        Pay 50₩ fine to get out of jail immediately.
        
        Parameters
        ----------
        player : Player
            Player paying the fine
        
        Raises
        ------
        GameException
            If player is not in jail or has insufficient funds
        """
        if error := GameValidation.validate_pay_get_out_of_jail_fine(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} paid {self.board.get_jail_fine()}₩ to get out of jail")
        self.player_balances[player] -= self.board.get_jail_fine()
        self.in_jail[player] = False
        self.player_positions[player] = 10  # Just Visiting position
        self.turns_in_jail[player] = 0


    def count_turn_in_jail(self, player: Player):
        """
        Increment the number of turns player has spent in jail.
        
        Parameters
        ----------
        player : Player
            Player in jail
        
        Raises
        ------
        GameException
            If player is not in jail
        """
        if error := GameValidation.validate_count_turn_in_jail(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} is in jail for {self.turns_in_jail[player]} turns")
        self.turns_in_jail[player] += 1


    ############## PAYING ACTIONS ##############


    def pay_tax(self, player: Player, tax: int):
        """
        Make player pay tax to the bank.
        
        Parameters
        ----------
        player : Player
            Player paying tax
        tax : int
            Amount of tax to pay
        
        Raises
        ------
        GameException
            If player has insufficient funds
        """
        if error := GameValidation.validate_pay_tax(self, player, tax):
            self.print_debug_info()
            raise error
        
        self.player_balances[player] -= tax
        custom_print(f"{player} paid {tax}₩ tax")


    def pay_players(self, player: Player, amount: int):
        """
        Make player pay specified amount to all other players.
        
        Parameters
        ----------
        player : Player
            Player making payments
        amount : int
            Amount to pay each other player
        
        Raises
        ------
        GameException
            If player has insufficient funds for all payments
        """
        if error := GameValidation.validate_pay_players(self, player, amount):
            self.print_debug_info()
            raise error
        
        for other_player in self.players:
            if other_player != player:
                self.player_balances[player] -= amount
                self.player_balances[other_player] += amount
                custom_print(f"{player} paid {other_player} {amount}₩")


    def pay_rent(
            self, 
            player: Player, 
            property: Tile,
            dice_roll: tuple[int, int] = None,
            utility_factor_multiplier: int = None,
            railway_factor_multiplier: int = None
        ):
        """
        Make player pay rent to property owner.
        
        Parameters
        ----------
        player : Player
            Player paying rent
        property : Tile
            Property being landed on
        dice_roll : tuple[int, int], optional
            Required for utility rent calculation
        utility_factor_multiplier : int, optional
            Multiplier for utility rent (from Chance cards)
        railway_factor_multiplier : int, optional
            Multiplier for railway rent (from Chance cards)
        
        Raises
        ------
        GameException
            If rent payment is invalid (mortgaged property, insufficient funds, etc.)
        """
        if error := GameValidation.validate_pay_rent(
            self,
            player, 
            property, 
            dice_roll,
            utility_factor_multiplier,
            railway_factor_multiplier
            ):
            self.print_debug_info()
            raise error
        
        # Find property owner
        owner = next(p for p in self.properties if property in self.properties[p])
        
        # Calculate rent based on property type and development
        if isinstance(property, Property):
            rent = property.base_rent
            # Check development level: hotels > houses > monopoly > base
            if self.houses[property.group][0] > 0:
                rent = property.house_rent[self.houses[property.group][0] - 1]
            elif self.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            elif all(property in self.properties[owner] for property in self.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
                
        elif isinstance(property, Railway):
            # Calculate based on number of railways owned
            rent_index = -1
            for prop in self.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]

            # Apply Chance card multiplier if present
            if railway_factor_multiplier:
                rent *= railway_factor_multiplier

        elif isinstance(property, Utility):
            dice = sum(dice_roll)
            # Apply specific multiplier or standard utility rules
            if utility_factor_multiplier:
                rent = utility_factor_multiplier * dice
            else:
                rent = 4 * dice
                # Double rent if owner has both utilities
                for prop in self.properties[owner]:
                    if isinstance(prop, Utility) and prop != property:
                        rent = 10 * dice
            
        self.player_balances[player] -= rent
        self.player_balances[owner] += rent
        custom_print(f"{player} paid {rent}₩ rent to {owner}")


    ############## RECEIVING ACTIONS ##############


    def receive_income(self, player: Player, amount: int):
        """
        Give player money from the bank.
        
        Parameters
        ----------
        player : Player
            Player receiving income
        amount : int
            Amount of income to receive
        """
        self.player_balances[player] += amount
        custom_print(f"{player} received {amount}₩")


    def receive_from_players(self, player: Player, amount: int):
        """
        Make all other players pay specified amount to this player.
        
        Parameters
        ----------
        player : Player
            Player receiving payments
        amount : int
            Amount each other player must pay
        
        Raises
        ------
        GameException
            If any other player has insufficient funds
        """
        if error := GameValidation.validate_receive_from_players(self, player, amount):
            self.print_debug_info()
            raise error
        
        for other_player in self.players:
            if other_player != player:
                self.player_balances[other_player] -= amount
                self.player_balances[player] += amount
                custom_print(f"{player} received {amount}₩ from {other_player}")


    ############## TRADE ACTIONS ##############


    def execute_trade_offer(self, trade_offer: TradeOffer):
        """
        Execute a validated trade between two players.
        
        Parameters
        ----------
        trade_offer : TradeOffer
            Complete trade offer with all terms
        
        Raises
        ------
        GameException
            If trade is invalid (insufficient assets, invalid properties, etc.)
        """
        if error := GameValidation.validate_trade_offer(self, trade_offer):
            self.print_debug_info()
            raise error
        
        source_player = trade_offer.source_player
        target_player = trade_offer.target_player
        
        # Transfer properties offered by source to target
        if trade_offer.properties_offered:
            for property in trade_offer.properties_offered:
                self.properties[source_player].remove(property)
                self.properties[target_player].append(property)

        # Transfer properties requested from target to source
        if trade_offer.properties_requested:
            for property in trade_offer.properties_requested:
                self.properties[target_player].remove(property)
                self.properties[source_player].append(property)

        # Transfer money offered by source to target
        if trade_offer.money_offered:
            self.player_balances[source_player] -= trade_offer.money_offered
            self.player_balances[target_player] += trade_offer.money_offered

        # Transfer money requested from target to source
        if trade_offer.money_requested:
            self.player_balances[target_player] -= trade_offer.money_requested
            self.player_balances[source_player] += trade_offer.money_requested

        # Handle jail card transfers
        if trade_offer.jail_cards_offered == trade_offer.jail_cards_requested:
            pass # No sense in trading jail cards

        if trade_offer.jail_cards_offered != 0 and trade_offer.jail_cards_requested == 0:
            self.escape_jail_cards[source_player] -= trade_offer.jail_cards_offered
            self.escape_jail_cards[target_player] += trade_offer.jail_cards_offered

        if trade_offer.jail_cards_requested != 0 and trade_offer.jail_cards_offered == 0:
            self.escape_jail_cards[target_player] -= trade_offer.jail_cards_requested
            self.escape_jail_cards[source_player] += trade_offer.jail_cards_requested

        custom_print(f"Trade executed: {trade_offer}")


    ############## TURN ACTIONS ##############


    def change_turn(self):
        """
        Advance to the next player's turn and reset doubles counter.
        """
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.doubles_rolled = 0


    ############## BANKRUPTCY ACTIONS ##############


    def complete_bankruptcy_request(self, player: Player, bankruptcy_request: BankruptcyRequest):
        """
        Execute a bankruptcy request to raise funds for debt payment.
        
        Parameters
        ----------
        player : Player
            Player executing bankruptcy actions
        bankruptcy_request : BankruptcyRequest
            Request containing actions to take (downgrade, mortgage, trade)
        
        Raises
        ------
        GameException
            If bankruptcy request is invalid
        """
        if error := GameValidation.validate_bankruptcy_request(self, player, bankruptcy_request):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} completed a bankruptcy request")
        
        # Execute all downgrading suggestions
        for group_property in bankruptcy_request.downgrading_suggestions:
            self.downgrade_property_group(player, group_property)

        # Execute all mortgaging suggestions
        for property in bankruptcy_request.mortgaging_suggestions:
            self.mortgage_property(player, property)

        # Trade offers should be fulfilled by trade manager and this list should be empty
        # for trade_offer in bankruptcy_request.trade_offers:
        #     self.execute_trade_offer(trade_offer)
        
        custom_print(f"{player} completed a bankruptcy request")


    ############## UTILS METHODS ##############


    def get_houses_for_player(self, player: Player):
        """
        Get dictionary of property IDs to house counts for a player.
        
        Parameters
        ----------
        player : Player
            Player to get house information for
        
        Returns
        -------
        dict
            Dictionary mapping property IDs to number of houses
        """
        properties = [p for p in self.properties[player] if isinstance(p, Property)]
        groups_owned = set(property.group for property in properties)
        groups_with_houses = set(group for group in groups_owned if self.houses[group][0] > 0)
        return {
            property.id: self.houses[property.group][0] 
            for property in properties 
            if property.group in groups_with_houses
        }


    def get_hotels_for_player(self, player: Player):
        """
        Get dictionary of property IDs to hotel counts for a player.
        
        Parameters
        ----------
        player : Player
            Player to get hotel information for
        
        Returns
        -------
        dict
            Dictionary mapping property IDs to number of hotels (0 or 1)
        """
        properties = [p for p in self.properties[player] if isinstance(p, Property)]
        groups_owned = set(property.group for property in properties)
        groups_with_hotels = set(group for group in groups_owned if self.hotels[group][0] > 0)
        return {
            property.id: self.hotels[property.group][0] 
            for property in properties
            if property.group in groups_with_hotels
        }


    def get_player_net_worth(self, player: Player) -> int:
        """
        Calculate total net worth of a player including cash, properties, and buildings.
        
        Parameters
        ----------
        player : Player
            Player to calculate net worth for
        
        Returns
        -------
        int
            Total net worth
        """
        net_worth = self.player_balances[player]

        # Add property values (mortgage value if mortgaged, full price if not)
        for property in self.properties[player]:
            if property in self.mortgaged_properties:
                net_worth += property.mortgage
            else:
                net_worth += property.price

        # Add houses and hotels values
        for group in PropertyGroup:
            number_of_properties = len(self.board.get_properties_by_group(group))
            net_worth += self.houses[group][0] * group.house_cost() * number_of_properties
            net_worth += self.hotels[group][0] * group.hotel_cost() * number_of_properties

        return net_worth


    def configure_debug_mode(self, can_print: bool):
        """
        Enable or disable debug output for this game state.
        
        Parameters
        ----------
        can_print : bool
            Whether to enable debug printing
        """
        self.can_print_debug = can_print


    def print_debug_info(self):
        """
        Print comprehensive debug information about current game state.
        
        Only prints if debug mode is enabled via configure_debug_mode().
        """
        if not hasattr(self, 'can_print_debug') or not self.can_print_debug:
            return

        print("\n\n############### DEBUG INFO ###############\n")
        print("Player positions: ", self.player_positions)
        print("Player balances: ", self.player_balances)
        print("Properties: ", self.properties)
        print("Houses: ", self.houses)
        print("Hotels: ", self.hotels)
        print("In jail: ", self.in_jail)
        print("Escape jail cards: ", self.escape_jail_cards)
        print("Mortgaged properties: ", self.mortgaged_properties)
        print("Is owned: ", self.is_owned)
        print("Doubles rolled: ", self.doubles_rolled)
        print("Current player: ", self.players[self.current_player_index])
        print("Current player index: ", self.current_player_index)
        print("Turn in jail: ", self.turns_in_jail)
        print("\n##########################################\n\n")


    def json_representation(self) -> dict:
        """
        Get a JSON-serializable representation of the game state.
        
        Returns
        -------
        dict
            Dictionary representation of the game state
        """
        return {
            "player_positions": {str(player): pos for player, pos in self.player_positions.items()},
            "player_balances": {str(player): balance for player, balance in self.player_balances.items()},
            "properties": {str(player): [str(prop) for prop in props] for player, props in self.properties.items()},
            "houses": {str(group): (count, str(owner)) for group, (count, owner) in self.houses.items()},
            "hotels": {str(group): (count, str(owner)) for group, (count, owner) in self.hotels.items()},
            "in_jail": {str(player): in_jail for player, in_jail in self.in_jail.items()},
            "escape_jail_cards": {str(player): cards for player, cards in self.escape_jail_cards.items()},
            "mortgaged_properties": [str(prop) for prop in self.mortgaged_properties],
            "is_owned": [str(prop) for prop in self.is_owned],
            "doubles_rolled": self.doubles_rolled,
            "current_player_index": self.current_player_index,
            "turns_in_jail": {str(player): turns for player, turns in self.turns_in_jail.items()}
        }
    

    @staticmethod
    def from_json(json_data: dict, players: list[Player]) -> 'GameState':
        """
        Create a GameState instance from a JSON-serializable dictionary.
        
        Parameters
        ----------
        json_data : dict
            JSON data to load from
        
        Returns
        -------
        GameState
            New GameState instance populated with data from json_data
        """

        if "game_state" in json_data:
            json_data = json_data['game_state']
        else:
            raise ValueError("Invalid JSON data: 'game_state' key not found")

        game_state = GameState(players=players)

        def get_player_by_name(name):
            if name == "None":
                return None
            
            return next(player for player in players if str(player) == name)

        player_positions = {
            player: json_data['player_positions'][str(player)]
            for player in players
        }
        game_state.player_positions = player_positions

        player_balances = {
            player: json_data['player_balances'][str(player)]
            for player in players
        }
        game_state.player_balances = player_balances

        properties = {
            player: [game_state.board.get_tile_by_name(prop) for prop in json_data['properties'][str(player)]]
            for player in players
        }
        game_state.properties = properties

        game_state.houses = {
            PropertyGroup.init_from(group): (count, get_player_by_name(owner))
            for group, (count, owner) in json_data['houses'].items()
        }

        game_state.hotels = {
            PropertyGroup.init_from(group): (count, get_player_by_name(owner))
            for group, (count, owner) in json_data['hotels'].items()
        }

        game_state.in_jail = {
            get_player_by_name(player): in_jail
            for player, in_jail in json_data['in_jail'].items()
        }


        game_state.escape_jail_cards = {
            get_player_by_name(player): cards
            for player, cards in json_data['escape_jail_cards'].items()
        }

        game_state.mortgaged_properties = {
            game_state.board.get_tile_by_name(prop)
            for prop in json_data['mortgaged_properties']
        }

        game_state.is_owned = {
            game_state.board.get_tile_by_name(prop)
            for prop in json_data['is_owned']
        }

        game_state.doubles_rolled = json_data['doubles_rolled']
        game_state.current_player_index = json_data['current_player_index']

        game_state.turns_in_jail = {
            get_player_by_name(player): turns
            for player, turns in json_data['turns_in_jail'].items()
        }

        return game_state