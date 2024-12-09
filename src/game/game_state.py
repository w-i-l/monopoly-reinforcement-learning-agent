from game.player import Player
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.tile import Tile
from exceptions.not_enough_balance import NotEnoughBalanceException
from models.other_tiles import Jail, Go, GoToJail, FreeParking, Taxes, Chance, CommunityChest
from models.board import Board

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


    def move_player(self, player: Player, dice: tuple[int, int]):
        self.doubles_rolled += 1 if dice[0] == dice[1] else 0
        if self.doubles_rolled == 3:
            self.in_jail[player] = True
            self.player_positions[player] = Jail().id
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
            self.in_jail[player] = True
            self.player_positions[player] = self.board.get_jail_id()
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
        player_balance = self.player_balances[player]
        property_price = property.price

        if property in self.is_owned:
            raise Exception("Property already owned")

        if player_balance < property_price:
            raise NotEnoughBalanceException(property_price, player_balance)
        
        if property in self.mortgaged_properties:
            self.mortgaged_properties.remove(property)
            self.player_balances[player] -= property.buyback_price
            self.is_owned.add(property)
        else:
            self.properties[player].append(property)
            self.is_owned.add(property)
            self.player_balances[player] -= property_price
        print(f"{player} bought {property} remaining balance: ${self.player_balances[player]}")


    def mortgage_property(self, player: Player, property: Tile):
        if property not in self.is_owned:
            raise Exception("Property not owned")
        
        self.is_owned.remove(property)
        self.mortgaged_properties.add(property)
        self.player_balances[player] += property.mortage


    def change_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.doubles_rolled = 0


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
        except NotEnoughBalanceException as e:
            print(e.message)
        except Exception as e:
            print(e)
        game_state.change_turn()
        input()