from game.player import Player
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.tile import Tile
from exceptions.exceptions import *
from models.other_tiles import Jail, Go, GoToJail, FreeParking, Taxes, Chance, CommunityChest
from models.board import Board
from game.game_validation import GameValidation

# TODO: implement verification for all paths

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

    
    def move_player_to_property(self, player: Player, property: Tile):
        property_position = property.id
        player_position = self.player_positions[player]

        # verify if the player has passed go
        if property_position < player_position:
            self.player_balances[player] += 200
            print(f"{player} passed Go and received $200")

        self.player_positions[player] = property_position


    def receive_get_out_of_jail_card(self, player: Player):
        self.escape_jail_cards[player] += 1
        print(f"{player} received a Get Out of Jail card")


    def pay_players(self, player: Player, amount: int):
        for other_player in self.players:
            if other_player != player:
                self.player_balances[player] -= amount
                self.player_balances[other_player] += amount
                print(f"{player} paid {other_player} ${amount}")


    def sent_player_to_jail(self, player: Player):
        self.in_jail[player] = True
        self.player_positions[player] = self.board.get_jail_id()
        print(f"{player} is sent to jail")


    def move_player_backwards(self, player: Player, steps: int):
        self.player_positions[player] -= steps
        print(f"{player} moved backwards {steps} steps")

        # Check if player landed on Community Chest
        community_chest_tile = self.board.has_land_on_community_chest(self.player_positions[player])
        if community_chest_tile:
            print(f"{player} landed on Community Chest")
            pass

        # Check if player landed on Taxes
        tax_tile = self.board.has_landed_on_tax(self.player_positions[player])
        if tax_tile:
            if tax_tile.tax > self.player_balances[player]:
                raise NotEnoughBalanceException(tax_tile.tax, self.player_balances[player])
            self.player_balances[player] -= tax_tile.tax
            print(f"{player} landed on {tax_tile.name} and paid ${tax_tile.tax}")


    def move_player(self, player: Player, dice: tuple[int, int]):
        self.doubles_rolled += 1 if dice[0] == dice[1] else 0
        if self.doubles_rolled == 3:
            self.sent_player_to_jail(player)
            print(f"{player} rolled doubles 3 times and is sent to jail")
            return
        
        rolled = dice[0] + dice[1]
        self.player_positions[player] += rolled
        
        # Check if player passed Go
        if self.player_positions[player] >= 40:
            print(f"{player} passed Go and received $200")
            self.player_balances[player] += 200

        # Normalize position
        self.player_positions[player] %= 40
        print(f"{player} landed on {self.board.tiles[self.player_positions[player]]}")
        
        # Check if player landed on Go To Jail
        if self.board.has_landed_on_go_to_jail(self.player_positions[player]):
            self.sent_player_to_jail(player)
            print(f"{player} landed on Go To Jail and is sent to jail")
            return
        
        # Check if player landed on Chance
        chance_tile = self.board.has_land_on_chance(self.player_positions[player])
        if chance_tile:
            print(f"{player} landed on Chance")
            pass

        # Check if player landed on Community Chest
        community_chest_tile = self.board.has_land_on_community_chest(self.player_positions[player])
        if community_chest_tile:
            print(f"{player} landed on Community Chest")
            pass

        # Check if player landed on Taxes
        tax_tile = self.board.has_landed_on_tax(self.player_positions[player])
        if tax_tile:
            if tax_tile.tax > self.player_balances[player]:
                raise NotEnoughBalanceException(tax_tile.tax, self.player_balances[player])
            self.player_balances[player] -= tax_tile.tax
            print(f"{player} landed on {tax_tile.name} and paid ${tax_tile.tax}")

    def buy_property(self, player: Player, property: Tile):
        if error := GameValidation.validate_buy_property(self, player, property):
            raise error
        
        if property in self.mortgaged_properties:
            owner = None
            for p in self.properties:
                if property in self.properties[p]:
                    owner = p
                    break
            
            if owner == player:
                self.mortgaged_properties.remove(property)
                self.player_balances[player] -= property.buyback_price
                print(f"{player} remove mortgage from {property}")

            else:
                self.player_balances[player] -= property.buyback_price
                self.player_balances[player] -= property.price
                self.player_balances[owner] += property.price
                self.properties[owner].remove(property)
                self.properties[player].append(property)
                self.is_owned.add(property)
                self.mortgaged_properties.remove(property)
                print(f"{player} bought mortgaged {property} from {owner} for ${property.price}")
        else:
            self.properties[player].append(property)
            self.is_owned.add(property)
            self.player_balances[player] -= property.price

        print(f"{player} bought {property} remaining balance: ${self.player_balances[player]}")
        print(self.properties)

    def mortgage_property(self, player: Player, property: Tile):
        print(property)
        print(self.is_owned)    
        if error := GameValidation.validate_mortgage_property(self, player, property):
            raise error
        
        print(f"{player} mortaging {property}")
        self.mortgaged_properties.add(property)
        self.player_balances[player] += property.mortgage

    def change_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.doubles_rolled = 0

    def place_house(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_place_house(self, player, property_group):
            raise error
        
        cost = property_group.house_cost() * len(self.board.get_properties_by_group(property_group))
        print(f"{player} placed a house on {property_group}")
        self.houses[property_group] = (self.houses[property_group][0] + 1, player)
        self.player_balances[player] -= cost

    def place_hotel(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_place_hotel(self, player, property_group):
            raise error
        
        cost = property_group.hotel_cost()
        self.hotels[property_group] = (1, player)
        self.houses[property_group] = (0, None)
        self.player_balances[player] -= cost


    def update_property_group(self, player: Player, property_group: PropertyGroup):
        if self.houses[property_group][0] == 4:
            self.place_hotel(player, property_group)
        else:
            self.place_house(player, property_group)

    
    def downgrade_property_group(self, player: Player, property_group: PropertyGroup):
        if self.hotels[property_group][0] == 1:
            self.sell_hotel(player, property_group)
        else:
            self.sell_house(player, property_group)


    def sell_house(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_sell_house(self, player, property_group):
            raise error
        
        group_properties = self.board.get_properties_by_group(property_group)
        cost = property_group.house_cost() * len(group_properties) // 2
        self.houses[property_group] = (self.houses[property_group][0] - 1, player)
        self.player_balances[player] += cost

    def sell_hotel(self, player: Player, property_group: PropertyGroup):
        if error := GameValidation.validate_sell_hotel(self, player, property_group):
            raise error
        
        cost = property_group.hotel_cost() // 2
        self.hotels[property_group] = (0, None)
        self.houses[property_group] = (4, player)
        self.player_balances[player] += cost

    def get_out_of_jail(self, player: Player):
        '''
        Used **ONLY** when player rolls a double
        '''

        if error := GameValidation.validate_get_out_of_jail(self, player):
            raise error
        
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0

    def use_escape_jail_card(self, player: Player):
        if error := GameValidation.validate_use_escape_jail_card(self, player):
            raise error
        
        self.escape_jail_cards[player] -= 1
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0

    def pay_get_out_of_jail_fine(self, player: Player):
        if error := GameValidation.validate_pay_get_out_of_jail_fine(self, player):
            raise error
        
        self.player_balances[player] -= self.board.get_jail_fine()
        self.in_jail[player] = False
        self.player_positions[player] = 10
        self.turns_in_jail[player] = 0

    def count_turn_in_jail(self, player: Player):
        self.turns_in_jail[player] += 1

    def pay_tax(self, player: Player, tax: int):
        if error := GameValidation.validate_pay_tax(self, player, tax):
            raise error
        
        self.player_balances[player] -= tax
        print(f"{player} paid ${tax} tax")


    def receive_income(self, player: Player, amount: int):
        self.player_balances[player] += amount
        print(f"{player} received ${amount}")

    
    def receive_from_players(self, player: Player, amount: int):
        for other_player in self.players:
            if other_player != player:
                self.player_balances[other_player] -= amount
                self.player_balances[player] += amount
                print(f"{player} received ${amount} from {other_player}")

    def pay_rent(
            self, 
            player: Player, 
            property: Tile,
            utility_factor_multiplier: int = None,
            railway_factor_multiplier: int = None
        ):
        # TODO: Add dice roll to validate rent for utilities
        dice = 4

        if error := GameValidation.validate_pay_rent(
            self,
            player, 
            property, 
            dice,
            utility_factor_multiplier,
            railway_factor_multiplier
            ):
            raise error
        
        owner = next(p for p in self.properties if property in self.properties[p])
        
        if isinstance(property, Property):
            rent = property.base_rent
            if all(property in self.properties[owner] for property in self.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
            elif self.hotels[property.group][0] > 0:
                rent = property.hotel_rent
            elif self.houses[property.group][0] > 0:
                rent = property.house_rent[self.houses[property.group][0] - 1]
                
        elif isinstance(property, Railway):
            rent_index = -1
            for prop in self.properties[owner]:
                if isinstance(prop, Railway):
                    rent_index += 1
            rent = property.rent[rent_index]

            if railway_factor_multiplier:
                rent *= railway_factor_multiplier

        elif isinstance(property, Utility):
            if utility_factor_multiplier:
                rent = utility_factor_multiplier * dice
            else:
                rent = 4 * dice
                for prop in self.properties[owner]:
                    if isinstance(prop, Utility) and prop != property:
                        rent = 10 * dice
            
        self.player_balances[player] -= rent
        self.player_balances[owner] += rent
        print(f"{player} paid ${rent} rent to {owner}")

    def get_houses_for_player(self, player: Player):
        properties = filter(lambda p: isinstance(p, Property), self.properties[player])
        groups_owned = set(property.group for property in properties)
        groups_with_houses = set(group for group in groups_owned if self.houses[group][0] > 0)
        return {
            property.id: self.houses[property.group][0] 
            for property in properties 
            if property.group in groups_with_houses
        }
    
    def get_hotels_for_player(self, player: Player):
        properties = filter(lambda p: isinstance(p, Property), self.properties[player])
        groups_owned = set(property.group for property in properties)
        groups_with_hotels = set(group for group in groups_owned if self.hotels[group][0] > 0)
        return {
            property.id: self.hotels[property.group][0] 
            for property in properties
            if property.group in groups_with_hotels
        }

if __name__ == "__main__":
    players = [Player("Player 1"), Player("Player 2")]
    game_state = GameState(players)
    import random
    while True:
        player = game_state.players[game_state.current_player_index]
        dice = (random.randint(1, 6), random.randint(1, 6))
        print(f"{player} rolled {dice}")
        game_state.move_player(player, dice)
        try:
            property = game_state.board.tiles[game_state.player_positions[player]]
            if isinstance(property, Property) or isinstance(property, Railway) or isinstance(property, Utility):
                game_state.buy_property(player, game_state.board.tiles[game_state.player_positions[player]])
        except GameException as e:
            print(e.message)
        game_state.change_turn()
        input()