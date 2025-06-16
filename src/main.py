from managers.game_manager import GameManager
from agents.human_agent import HumanAgent
from agents.strategic_agent import *
from exceptions.exceptions import *
from agents.dqn_agent import DQNAgent
import numpy as np
import random
import tensorflow as tf
import traceback

def set_seed(seed):
    np.random.seed(seed)
    random.seed(seed)
    tf.random.set_seed(seed)

# set_seed(7379100)

def play_against_human_agent(player):
    human_player = HumanAgent("Human Player", port=6060)
    players = [player, human_player]
    game_manager = GameManager(players)
    game_manager.game_state.configure_debug_mode(can_print=False)

    human_player.game_state = game_manager.game_state

    can_continue = True
    while can_continue:
        try:
            can_continue = game_manager.play_turn()
        except BankrupcyException as e:
            print(e)
            print("GAME OVER")
            break

        except NotEnoughBalanceException as e:
            print(e)
            print("GAME OVER")
            break

        except ValueError as e:
            print(e)
            print("GAME OVER")
            break

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            traceback.print_exc()

        can_continue = True if can_continue == None else False
        game_manager.change_turn()

if __name__ == "__main__":
    dqn_methods = {
        'buy_property': "misc/saved_models/dqn/should_buy/v6/dqn_agent_final",
        'get_upgrading_suggestions': "misc/saved_models/dqn/upgrading/v5/dqn_upgrading_final",
        'should_pay_get_out_of_jail_fine': "misc/saved_models/dqn/jail_fine/v2/dqn_agent_final",
        "get_downgrading_suggestions": "misc/saved_models/dqn/downgrade/v2/dqn_downgrading_final",
        'get_mortgaging_suggestions': "misc/saved_models/dqn/mortgaging/v2/dqn_mortgaging_final",
        'get_unmortgaging_suggestions': "misc/saved_models/dqn/unmortgaging/v1/dqn_unmortgaging_final",
        'should_use_escape_jail_card': "misc/saved_models/dqn/escape_jail_card/v2/dqn_escape_jail_card_final",
    }

    can_use_defaults_methods = {
        'should_buy_property': False,
        'get_upgrading_suggestions': False,
        'should_pay_get_out_of_jail_fine': False,
        'get_downgrading_suggestions': False,
        'get_mortgaging_suggestions': False,
        'get_unmortgaging_suggestions': False,
        'should_use_escape_jail_card': False,
    }

    expert_dqn_agent = DQNAgent(
        "DQN player",
        training=False,
        dqn_methods=dqn_methods,
        can_use_defaults_methods=can_use_defaults_methods,
    )

    expert_dqn_agent.epsilon = 0.05

    play_against_human_agent(expert_dqn_agent)
