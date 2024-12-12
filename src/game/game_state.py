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
            self.player_positions[player] = self.board.get_jail_id()
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


    def mortage_property(self, player: Player, property: Tile):
        print(f"{player} mortaging {property}")
        if property not in self.is_owned:
            raise Exception("Property not owned")
        
        if property in self.mortgaged_properties:
            raise Exception("Property already mortgaged")
        
        if property not in self.properties[player]:
            raise Exception("Property not owned by current player")
        
        if isinstance(property, Property) and (self.houses[property.group][0] > 0 or self.hotels[property.group][0] > 0):
            raise Exception("Property has houses/hotels")
        
        self.is_owned.remove(property)
        self.mortgaged_properties.add(property)
        self.properties[player].remove(property)
        self.player_balances[player] += property.mortage


    def change_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.doubles_rolled = 0


    def place_house(self, player: Player, property_group: PropertyGroup):
        if self.houses[property_group][0] == 4:
            raise Exception("Max houses already placed")
        
        group_properties = self.board.get_properties_by_group(property_group)
        if not all(property in self.properties[player] for property in group_properties):
            raise Exception("Not all properties owned")
        
        cost = property_group.house_cost() * len(group_properties)
        if self.player_balances[player] < cost:
            raise NotEnoughBalanceException(cost, self.player_balances[player])
        
        print(f"{player} placed a house on {property_group}")
        self.houses[property_group] = (self.houses[property_group][0] + 1, player)
        self.player_balances[player] -= cost


    def place_hotel(self, player: Player, property_group: PropertyGroup):
        if self.hotels[property_group][0] == 1:
            raise Exception("Max hotels already placed")
        
        group_properties = self.board.get_properties_by_group(property_group)
        if not all(property in self.properties[player] for property in group_properties):
            raise Exception("Not all properties owned")
        
        if self.houses[property_group][0] < 4:
            raise Exception("Not all houses placed")
        
        cost = property_group.hotel_cost()
        if self.player_balances[player] < cost:
            raise NotEnoughBalanceException(cost, self.player_balances[player])
        
        self.hotels[property_group] = (1, player)
        self.houses[property_group] = (0, None)
        self.player_balances[player] -= cost


    def sell_house(self, player: Player, property_group: PropertyGroup):
        if self.houses[property_group][0] == 0:
            raise Exception("No houses to sell")
        
        if self.houses[property_group][1] != player:
            raise Exception("Not owner of houses")
        
        group_properties = self.board.get_properties_by_group(property_group)
        cost = property_group.house_cost() * len(group_properties) // 2
        self.houses[property_group] = (self.houses[property_group][0] - 1, player)
        self.player_balances[player] += cost


    def sell_hotel(self, player: Player, property_group: PropertyGroup):
        if self.hotels[property_group][0] == 0:
            raise Exception("No hotels to sell")
        
        if self.hotels[property_group][1] != player:
            raise Exception("Not owner of hotels")
        
        group_properties = self.board.get_properties_by_group(property_group)
        cost = property_group.hotel_cost() // 2
        self.hotels[property_group] = (0, None)
        self.houses[property_group] = (4, player)
        self.player_balances[player] += cost


    def use_escape_jail_card(self, player: Player):
        if self.escape_jail_cards[player] == 0:
            raise Exception("No escape jail card")
        
        self.escape_jail_cards[player] -= 1
        self.in_jail[player] = False
        self.player_positions[player] = 10


    def pay_rent(self, player: Player, property: Tile):
        owner = None
        for p in self.properties:
            if property in self.properties[p]:
                owner = p
                break
        
        rent = property.base_rent
        if isinstance(property, Property):
            if all(property in self.properties[owner] for property in self.board.get_properties_by_group(property.group)):
                rent = property.full_group_rent
            else:
                rent = property.house_rent[self.houses[property.group][0]] + property.hotel_rent * self.hotels[property.group][0]
        
        if self.player_balances[player] < rent:
            raise NotEnoughBalanceException(rent, self.player_balances[player])
        
        self.player_balances[player] -= rent
        self.player_balances[owner] += rent
        print(f"{player} paid ${rent} rent to {owner}")


    def get_houses_for_player(self, player: Player):
        groups_owned = set(property.group for property in self.properties[player])
        groups_with_houses = set(group for group in groups_owned if self.houses[group][0] > 0)
        return {
            property.id: self.houses[property.group][0] for property in self.properties[player] if property.group in groups_with_houses
        }
    
    
    def get_hotels_for_player(self, player: Player):
        groups_owned = set(property.group for property in self.properties[player])
        groups_with_hotels = set(group for group in groups_owned if self.hotels[group][0] > 0)
        return {
            property.id: self.hotels[property.group][0] for property in self.properties[player] if property.group in groups_with_hotels
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
        except NotEnoughBalanceException as e:
            print(e.message)
        except Exception as e:
            print(e)
        game_state.change_turn()
        input()