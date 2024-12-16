from typing import List
from game.player import Player
from game.game_state import GameState
from game.dice_manager import DiceManager
from game.chance_manager import ChanceManager
from game.community_chest_manager import CommunityChestManager
from exceptions.exceptions import *
from models.other_tiles import Chance, CommunityChest

class GameManager:
    def __init__(self, players: List[Player]):
        self.players = players
        self.game_state = GameState(players)
        self.dice_manager = DiceManager()
        self.chance_manager = ChanceManager()
        self.community_chest_manager = CommunityChestManager()
                                    

    def play_turn(self):
        current_palayer_index = self.game_state.current_player_index
        current_player = self.players[current_palayer_index]

        # TODO: Verify if the player can play - check if the player has any money left
        if self.game_state.player_balances[current_player] <= 0:
            print(f"{current_player} is bankrupt")
            print("GAME OVER")
            return -1

        # TODO: Verify if the player can play - check if the player is in jail
        if self.game_state.in_jail[current_player]:
            if self.game_state.turns_in_jail[current_player] == 3:
                self.game_state.pay_get_out_of_jail_fine(current_player)

            else:
                # try to pay the fine
                if current_player.should_pay_get_out_of_jail_fine(self.game_state):
                    self.game_state.pay_get_out_of_jail_fine(current_player)

                # try to use the escape jail card
                elif current_player.should_use_escape_jail_card(self.game_state):
                    self.game_state.use_escape_jail_card(current_player)

                # try to roll a double
                else:
                    dice_roll = self.dice_manager.roll()
                    if dice_roll[0] == dice_roll[1]:
                        self.game_state.get_out_of_jail(current_player)
                    else:
                        self.game_state.count_turn_in_jail(current_player)
                        return


        # Roll the dice
        dice_roll = self.dice_manager.roll()

        # Move the player
        self.game_state.move_player(current_player, dice_roll)

        # check if the player went to jail
        if self.game_state.player_positions[current_player] == self.game_state.board.get_jail_id():
            return
        
        current_player_position = self.game_state.player_positions[current_player]
        current_player = self.players[current_palayer_index]
        tile = self.game_state.board.tiles[current_player_position]
        
        # TODO: check if the player landed on chance/ community chest
        if isinstance(tile, Chance):
            chance_card = self.chance_manager.draw_card(self.game_state, current_player)
            try:
                print("Performing chance card action", chance_card)
                chance_card.action(*chance_card.args)
            except Exception as e:
                print(e)
                print("Error in chance card action")
                return -1

        elif isinstance(tile, CommunityChest):
            community_chest_card = self.community_chest_manager.draw_card(self.game_state, current_player)
            try:
                print("Performing community chest card action", community_chest_card)
                community_chest_card.action(*community_chest_card.args)
            except Exception as e:
                print(e)
                print("Error in community chest card action")
                return -1
        
        # Check if the player landed on an owned property
        print(tile)
        print(self.game_state.is_owned)
        if tile in self.game_state.is_owned and\
           tile not in self.game_state.properties[current_player] and\
           tile not in self.game_state.mortgaged_properties:
            try:
                self.game_state.pay_rent(current_player, tile)
            except NotEnoughBalanceException as e:
                # TODO: Handle player bankruptcy
                print(e)
                print("Player does not have enough balance to pay rent")
                return -1

        # Check if the player landed on an unowned property
        elif tile not in self.game_state.is_owned:
            if current_player.should_buy_property(self.game_state, tile):
                try:
                    self.game_state.buy_property(current_player, tile)
                except NotEnoughBalanceException as e:
                    # TODO: Handle player bankruptcy
                    print(e)
                    print("Player does not have enough balance to buy the property")
                    return -1

        # TODO: Implement the logic for auctioning the property if the player does not buy it


        suggestions = current_player.get_downgrading_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.downgrade_property_group(current_player, suggestion)
            except NotEnoughBalanceException as e:
                # TODO: Handle player bankruptcy
                print(e)
                print("Player does not have enough balance to downgrade the property")
                return -1


        # Check if the player wants to mortgage properties
        suggestions = current_player.get_mortgaging_suggestions(self.game_state)
        print("Mortgaging suggestions: ", suggestions)
        for suggestion in suggestions:
            try:
                self.game_state.mortgage_property(current_player, suggestion)
            except NotEnoughBalanceException as e:
                # TODO: Handle player bankruptcy
                print(e)
                print("Player does not have enough balance to mortgage the property")
                return -1
                

        # Check if the player wants to upgrade properties
        suggestions = current_player.get_upgrading_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.update_property_group(current_player, suggestion)
            except NotEnoughBalanceException as e:
                # TODO: Handle player bankruptcy
                print(e)
                print("Player does not have enough balance to upgrade the property")
                return -1


    def change_turn(self):
        self.game_state.change_turn()
        print("\n\n")
        print(f"Next player: {self.players[self.game_state.current_player_index]}")
        print(self.game_state.player_balances)

        
            
            

if __name__ == "__main__":
    from agents.random_agent import RandomAgent
    import time

    players = [RandomAgent("Player 1"), RandomAgent("Player 2")]
    game_manager = GameManager(players)
    can_continue = True

    tourns = 0
    while can_continue:
        tourns += 1
        can_continue = game_manager.play_turn()
        can_continue = True if can_continue == None else False
        game_manager.change_turn()
        print(tourns)
    print(game_manager.game_state.houses)
    print(game_manager.game_state.hotels)
    print(game_manager.game_state.player_balances)
    print(game_manager.game_state.properties)
        # time.sleep(0.1)