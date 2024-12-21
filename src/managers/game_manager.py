from typing import List
from game.player import Player
from game.game_state import GameState
from managers.dice_manager import DiceManager
from managers.chance_manager import ChanceManager
from managers.community_chest_manager import CommunityChestManager
from exceptions.exceptions import *
from models.other_tiles import Chance, CommunityChest
from utils.logger import ErrorLogger

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
        
        dice_roll = None

        # TODO: Verify if the player can play - check if the player is in jail
        if self.game_state.in_jail[current_player]:
            # try to roll a double
            dice_roll = self.dice_manager.roll()
            if dice_roll[0] == dice_roll[1]:
                self.game_state.get_out_of_jail(current_player)

            # if the player has been in jail for 3 turns, he must pay the fine
            elif self.game_state.turns_in_jail[current_player] == 2:
                self.game_state.pay_get_out_of_jail_fine(current_player)

            # try to use the escape jail card
            elif current_player.should_use_escape_jail_card(self.game_state):
                self.game_state.use_escape_jail_card(current_player)

            # TODO: implement the logic for buying the escape jail card from other players

            # try to pay the fine
            elif current_player.should_pay_get_out_of_jail_fine(self.game_state):
                self.game_state.pay_get_out_of_jail_fine(current_player)

            # count the turn in jail
            else:
                self.game_state.count_turn_in_jail(current_player)
                self.__handle_in_jail_actions(current_player)
                return

        # Roll the dice if the player did not roll a double in attempt to get out of jail
        if dice_roll is None:
            dice_roll = self.dice_manager.roll()
        print(f"{current_player} rolled {dice_roll[0]} and {dice_roll[1]}")

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
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                ErrorLogger.log_error(e)
                print("Error in chance card action")
                return -1

        elif isinstance(tile, CommunityChest):
            community_chest_card = self.community_chest_manager.draw_card(self.game_state, current_player)
            try:
                print("Performing community chest card action", community_chest_card)
                community_chest_card.action(*community_chest_card.args)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                ErrorLogger.log_error(e)
                print("Error in community chest card action")
                return -1
        
        # Check if the player landed on an owned property
        print(tile)
        print(self.game_state.is_owned)
        if tile in self.game_state.is_owned and\
           tile not in self.game_state.properties[current_player] and\
           tile not in self.game_state.mortgaged_properties:
            try:
                dice_roll = self.dice_manager.roll()
                self.game_state.pay_rent(current_player, tile, dice_roll)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                print("Player does not have enough balance to pay rent")
                return -1

        # Check if the player landed on an unowned property
        elif tile not in self.game_state.is_owned:
            if current_player.should_buy_property(self.game_state, tile):
                try:
                    self.game_state.buy_property(current_player, tile)
                except Exception as e:
                    if isinstance(e, NotEnoughBalanceException):
                        raise e
                
                    # TODO: Handle player bankruptcy
                    ErrorLogger.log_error(e)
                    print("Player does not have enough balance to buy the property")
                    return -1

        # TODO: Implement the logic for auctioning the property if the player does not buy it


        # Check if the player wants to downgrade properties
        self.__handle_downgrading_suggestions(current_player)

        # Check if the player wants to mortgage properties
        self.__handle_mortgaging_suggestions(current_player)

        # Check if the player wants to unmortgage properties
        self.__handle_unmortgaging_suggestions(current_player)

        # Check if the player wants to upgrade properties
        self.__handle_upgrading_suggestions(current_player)
            

    def __handle_downgrading_suggestions(self, current_player):
        suggestions = current_player.get_downgrading_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.downgrade_property_group(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                return -1
            

    def __handle_unmortgaging_suggestions(self, current_player):
        suggestions = current_player.get_unmortgaging_suggestions(self.game_state)
        for suggestion in suggestions:
            try:
                self.game_state.unmortgage_property(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle error
                ErrorLogger.log_error(e)
                return -1
    
            
    def __handle_mortgaging_suggestions(self, current_player):
        suggestions = current_player.get_mortgaging_suggestions(self.game_state)
        # print("Mortgaging suggestions: ", suggestions)
        for suggestion in suggestions:
            try:
                self.game_state.mortgage_property(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                print("Player does not have enough balance to mortgage the property")
                return -1
            
    def __handle_upgrading_suggestions(self, current_player):
        suggestions = current_player.get_upgrading_suggestions(self.game_state)
        # print("Upgrading suggestions: ", suggestions)
        for suggestion in suggestions:
            try:
                self.game_state.update_property_group(current_player, suggestion)
            except Exception as e:
                if isinstance(e, NotEnoughBalanceException):
                    raise e
                
                # TODO: Handle player bankruptcy
                ErrorLogger.log_error(e)
                print("Player does not have enough balance to upgrade the property")
                return -1
            
    
    def __handle_in_jail_actions(self, current_player):
        self.__handle_downgrading_suggestions(current_player)
        self.__handle_mortgaging_suggestions(current_player)
        self.__handle_unmortgaging_suggestions(current_player)
        self.__handle_upgrading_suggestions(current_player)


    def change_turn(self):
        self.game_state.change_turn()
        print("\n\n")
        print(f"Next player: {self.players[self.game_state.current_player_index]}")
        print(self.game_state.player_balances)