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

# TODO: implement verification for all paths

CAN_PRINT = False
def custom_print(*args, **kwargs):
    if CAN_PRINT:
        print(*args, **kwargs)

class GameState:
    def __init__(self, players: list[Player]):
        self.players = players
        self.current_player_index = 0
        self.properties = { player: [] for player in players }
        self.houses = {
            group: (0, None) for group in PropertyGroup
        }
        self.hotels = {
            group: (0, None) for group in PropertyGroup
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
        if self.in_jail[player]:
            custom_print(f"{player} is in jail")
            self.print_debug_info()
            raise PlayerInJailException(player)

        self.doubles_rolled += 1 if dice[0] == dice[1] else 0
        if self.doubles_rolled == 3:
            self.send_player_to_jail(player)
            custom_print(f"{player} rolled doubles 3 times and is sent to jail")
            return
        
        rolled = dice[0] + dice[1]
        self.player_positions[player] += rolled
        
        # Check if player passed Go
        if self.player_positions[player] >= 40:
            custom_print(f"{player} passed Go and received $200")
            self.player_balances[player] += 200

        # Normalize position
        self.player_positions[player] %= 40
        custom_print(f"{player} landed on {self.board.tiles[self.player_positions[player]]}")
        
        # Check if player landed on Go To Jail
        if self.board.has_landed_on_go_to_jail(self.player_positions[player]):
            self.send_player_to_jail(player)
            custom_print(f"{player} landed on Go To Jail and is sent to jail")
            return
        

    def move_player_backwards(self, player: Player, steps: int):
        # We don t need to worry about negative positions
        # because of the placement of the activation tiles on the board
        self.player_positions[player] -= steps
        custom_print(f"{player} moved backwards {steps} steps")

        # player can land on 3 tiles: Orange Property, Community Chest, Taxes

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
            custom_print(f"{player} landed on {tax_tile.name} and paid ${tax_tile.tax}")
            return
        
        # Landing on Orange Property
        # paying rent/ buying property handled in chance manager
        return
        

    def move_player_to_property(self, player: Player, property: Tile):
        property_position = property.id
        player_position = self.player_positions[player]

        # verify if the player has passed go
        if property_position < player_position:
            self.player_balances[player] += 200
            custom_print(f"{player} passed Go and received $200")

        self.player_positions[player] = property_position

    
    def move_player_to_start(self, player: Player):
        self.player_positions[player] = 0
        self.player_balances[player] += 200
        custom_print(f"{player} moved to Start")


    ############## PROPERTY ACTIONS ##############

    def buy_property(self, player: Player, property: Tile):
        if error := GameValidation.validate_buy_property(self, player, property):
            self.print_debug_info()
            raise error
    
        self.properties[player].append(property)
        self.is_owned.add(property)
        self.player_balances[player] -= property.price

        custom_print(f"{player} bought {property} remaining balance: ${self.player_balances[player]}")
        custom_print(self.properties)


    def mortgage_property(self, player: Player, property: Tile):
        if error := GameValidation.validate_mortgage_property(self, player, property):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} mortaging {property}")
        self.mortgaged_properties.add(property)
        self.player_balances[player] += property.mortgage


    def unmortgage_property(self, player: Player, property: Tile):
        if error := GameValidation.validate_unmortgage_property(self, player, property):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} unmortaging {property}")
        self.mortgaged_properties.remove(property)
        self.player_balances[player] -= property.buyback_price


    ############## HOUSES AND HOTELS ##############

    def update_property_group(self, player: Player, property_group: PropertyGroup):
        if self.houses[property_group][0] == 4:
            self.place_hotel(player, property_group)
        else:
            self.place_house(player, property_group)


    def place_house(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_place_house(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} placed a house on {property_group}")
        cost = property_group.house_cost() * len(self.board.get_properties_by_group(property_group))
        self.houses[property_group] = (self.houses[property_group][0] + 1, player)
        self.player_balances[player] -= cost


    def place_hotel(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_place_hotel(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} placed a hotel on {property_group}")
        cost = property_group.hotel_cost()
        self.hotels[property_group] = (1, player)
        self.houses[property_group] = (0, player)
        self.player_balances[player] -= cost


    def downgrade_property_group(self, player: Player, property_group: PropertyGroup):
        if self.hotels[property_group][0] == 1:
            self.sell_hotel(player, property_group)
        else:
            self.sell_house(player, property_group)


    def sell_house(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_sell_house(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} sold a house on {property_group}")
        group_properties = self.board.get_properties_by_group(property_group)
        cost = property_group.house_cost() * len(group_properties) // 2
        self.houses[property_group] = (self.houses[property_group][0] - 1, player)
        self.player_balances[player] += cost

        if self.houses[property_group][0] == 0:
            self.houses[property_group] = (0, None)
            self.hotels[property_group] = (0, None)


    def sell_hotel(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_sell_hotel(self, player, property_group):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} sold a hotel on {property_group}")
        cost = property_group.hotel_cost() // 2
        self.hotels[property_group] = (0, player)
        self.houses[property_group] = (4, player)
        self.player_balances[player] += cost


    ############## JAIL ##############

    def send_player_to_jail(self, player: Player):
        if error := GameValidation.validate_send_player_to_jail(self, player):
            self.print_debug_info()
            raise error
        
        self.in_jail[player] = True
        self.doubles_rolled = 0
        self.turns_in_jail[player] = 0
        self.player_positions[player] = self.board.get_jail_id()
        custom_print(f"{player} is sent to jail")


    def get_out_of_jail(self, player: Player):
        '''
        Used **ONLY** when player rolls a double
        '''

        if error := GameValidation.validate_get_out_of_jail(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} got out of jail by rolling doubles")
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0


    def receive_get_out_of_jail_card(self, player: Player):
        if error := GameValidation.validate_receive_get_out_of_jail_card(self, player):
            self.print_debug_info()
            raise error
        
        self.escape_jail_cards[player] += 1
        custom_print(f"{player} received a Get Out of Jail card")


    def use_escape_jail_card(self, player: Player):
        if error := GameValidation.validate_use_escape_jail_card(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} used a Get Out of Jail card")
        self.escape_jail_cards[player] -= 1
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0


    def pay_get_out_of_jail_fine(self, player: Player):
        if error := GameValidation.validate_pay_get_out_of_jail_fine(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} paid ${self.board.get_jail_fine()} to get out of jail")
        self.player_balances[player] -= self.board.get_jail_fine()
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0


    def count_turn_in_jail(self, player: Player):
        if error := GameValidation.validate_count_turn_in_jail(self, player):
            self.print_debug_info()
            raise error
        
        custom_print(f"{player} is in jail for {self.turns_in_jail[player]} turns")
        self.turns_in_jail[player] += 1


    ############## PAYING ACTIONS ##############

    def pay_tax(self, player: Player, tax: int):
        if error := GameValidation.validate_pay_tax(self, player, tax):
            self.print_debug_info()
            raise error
        
        self.player_balances[player] -= tax
        custom_print(f"{player} paid ${tax} tax")


    def pay_players(self, player: Player, amount: int):
        if error := GameValidation.validate_pay_players(self, player, amount):
            self.print_debug_info()
            raise error
        
        for other_player in self.players:
            if other_player != player:
                self.player_balances[player] -= amount
                self.player_balances[other_player] += amount
                custom_print(f"{player} paid {other_player} ${amount}")


    def pay_rent(
            self, 
            player: Player, 
            property: Tile,
            dice_roll: tuple[int, int] = None,
            utility_factor_multiplier: int = None,
            railway_factor_multiplier: int = None
        ):
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
        
        owner = next(p for p in self.properties if property in self.properties[p])
        
        if isinstance(property, Property):
            rent = property.base_rent
            if self.houses[property.group][0] > 0:
                rent = property.house_rent[self.houses[property.group][0] - 1]
            elif self.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            elif all(property in self.properties[owner] for property in self.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
                
        elif isinstance(property, Railway):
            rent_index = -1
            for prop in self.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]

            if railway_factor_multiplier:
                rent *= railway_factor_multiplier

        elif isinstance(property, Utility):
            dice = sum(dice_roll)
            if utility_factor_multiplier:
                rent = utility_factor_multiplier * dice
            else:
                rent = 4 * dice
                for prop in self.properties[owner]:
                    if isinstance(prop, Utility) and prop != property:
                        rent = 10 * dice
            
        self.player_balances[player] -= rent
        self.player_balances[owner] += rent
        custom_print(f"{player} paid ${rent} rent to {owner}")


    ############## RECEIVING ACTIONS ##############

    def receive_income(self, player: Player, amount: int):
        self.player_balances[player] += amount
        custom_print(f"{player} received ${amount}")

    
    def receive_from_players(self, player: Player, amount: int):
        if error := GameValidation.validate_receive_from_players(self, player, amount):
            self.print_debug_info()
            raise error
        
        for other_player in self.players:
            if other_player != player:
                self.player_balances[other_player] -= amount
                self.player_balances[player] += amount
                custom_print(f"{player} received ${amount} from {other_player}")


    ############## TRADE ACTIONS ##############

    def execute_trade_offer(self, trade_offer: TradeOffer):
        if error := GameValidation.validate_trade_offer(self, trade_offer):
            self.print_debug_info()
            raise error
        
        source_player = trade_offer.source_player
        target_player = trade_offer.target_player
        
        if trade_offer.properties_offered:
            for property in trade_offer.properties_offered:
                self.properties[source_player].remove(property)
                self.properties[target_player].append(property)

        if trade_offer.properties_requested:
            for property in trade_offer.properties_requested:
                self.properties[target_player].remove(property)
                self.properties[source_player].append(property)

        if trade_offer.money_offered:
            self.player_balances[source_player] -= trade_offer.money_offered
            self.player_balances[target_player] += trade_offer.money_offered

        if trade_offer.money_requested:
            self.player_balances[target_player] -= trade_offer.money_requested
            self.player_balances[source_player] += trade_offer.money_requested

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
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.doubles_rolled = 0
        

    ############## UTILS METHODS ##############

    def get_houses_for_player(self, player: Player):
        properties = [p for p in self.properties[player] if isinstance(p, Property)]
        groups_owned = set(property.group for property in properties)
        groups_with_houses = set(group for group in groups_owned if self.houses[group][0] > 0)
        return {
            property.id: self.houses[property.group][0] 
            for property in properties 
            if property.group in groups_with_houses
        }


    def get_hotels_for_player(self, player: Player):
        properties = [p for p in self.properties[player] if isinstance(p, Property)]
        groups_owned = set(property.group for property in properties)
        groups_with_hotels = set(group for group in groups_owned if self.hotels[group][0] > 0)
        return {
            property.id: self.hotels[property.group][0] 
            for property in properties
            if property.group in groups_with_hotels
        }
    

    def get_player_net_worth(self, player: Player) -> int:
        net_worth = self.player_balances[player]

        # adding property values - mortgage values
        for property in self.properties[player]:
            if property in self.mortgaged_properties:
                net_worth += property.mortgage
            else:
                net_worth += property.price

        # adding houses and hotels values
        for group in PropertyGroup:
            number_of_properties = len(self.board.get_properties_by_group(group))
            net_worth += self.houses[group][0] * group.house_cost() * number_of_properties
            net_worth += self.hotels[group][0] * group.hotel_cost() * number_of_properties

        return net_worth
    

    def configure_debug_mode(self, can_print: bool):
        self.can_print_debug = can_print


    def print_debug_info(self):
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


if __name__ == "__main__":
    players = [Player("Player 1"), Player("Player 2")]
    game_state = GameState(players)
    import random
    while True:
        player = game_state.players[game_state.current_player_index]
        dice = (random.randint(1, 6), random.randint(1, 6))
        custom_print(f"{player} rolled {dice}")
        game_state.move_player(player, dice)
        try:
            property = game_state.board.tiles[game_state.player_positions[player]]
            if isinstance(property, Property) or isinstance(property, Railway) or isinstance(property, Utility):
                game_state.buy_property(player, game_state.board.tiles[game_state.player_positions[player]])
        except GameException as e:
            custom_print(e.message)
        game_state.change_turn()
        input()