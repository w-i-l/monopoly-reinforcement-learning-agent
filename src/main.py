from models.property import Property
from models.property_group import PropertyGroup
import json
from utils.helper_functions import format_path
from models.railway import Railway
from models.utility import Utility
from models.other_tiles import Taxes, Chance, CommunityChest, GoToJail, Jail, FreeParking, Go
from managers.game_manager import GameManager
from agents.random_agent import RandomAgent
from agents.human_agent import HumanAgent
from agents.strategic_agent import StrategicAgent
import time
from models.property_group import PropertyGroup
from exceptions.exceptions import NotEnoughBalanceException


if __name__ == "__main__":

    random_agent = RandomAgent("Random player")
    random_agent2 = RandomAgent("Random player 2")
    random_agent3 = RandomAgent("Random player 3")
    random_agent4 = RandomAgent("Random player 4")

    strategic_agent = StrategicAgent("Strategic player")
    human_player = HumanAgent("Human Player", port=6060)
    players = [strategic_agent, human_player]
    game_manager = GameManager(players)
    
    # game_manager.game_state.in_jail[human_player] = True
    # game_manager.game_state.player_positions[human_player] = 10
    # brown = game_manager.game_state.board.get_properties_by_group(PropertyGroup.BROWN)
    # game_manager.game_state.properties[human_player] = brown
    # game_manager.game_state.is_owned.update(brown)
    # game_manager.game_state.place_house(human_player, PropertyGroup.BROWN)

    human_player.game_state = game_manager.game_state
    can_continue = True

    for _ in range(1):
        tourns = 0
        while can_continue:
            tourns += 1
            try:
                can_continue = game_manager.play_turn()
            except NotEnoughBalanceException as e:
                print(e)
                print("GAME OVER")
                break
            can_continue = True if can_continue == None else False
            game_manager.change_turn()
            print(tourns)

    print(game_manager.game_state.houses)
    print(game_manager.game_state.hotels)
    print(game_manager.game_state.player_balances)
    print(game_manager.game_state.properties)
        # time.sleep(0.1)