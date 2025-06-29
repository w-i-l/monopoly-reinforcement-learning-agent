import numpy as np
import random
import tensorflow as tf
import traceback
import time
import os

from managers.game_manager import GameManager
from agents.human_agent import HumanAgent
from agents.strategic_agent import *
from exceptions.exceptions import *
from agents.dqn_agent import DQNAgent

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

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
    turn_count = 0
    max_turns = 2000
    
    try:
        while can_continue and turn_count < max_turns:
            try:
                turn_count += 1
                can_continue = game_manager.play_turn()

                if turn_count == 5:
                    raise BankrupcyException(expert_dqn_agent.name)
                
            except BankrupcyException as e:
                print(f"Game ended due to bankruptcy: {e}")
                
                bankrupt_player_name = e.player_name
                winner = None
                for p in players:
                    if p.name != bankrupt_player_name:
                        winner = p.name
                        break
                
                # Set game ended state
                human_player.set_game_ended(
                    winner=winner,
                    bankrupt_players=[bankrupt_player_name],
                    turn_count=turn_count
                )
                break

            except Exception as e:
                print(f"Game ended due to error: {e}")
                
                # Try to determine winner by net worth
                try:
                    player_worths = {
                        p.name: game_manager.game_state.get_player_net_worth(p)
                        for p in players
                    }
                    
                    max_worth = max(player_worths.values())
                    winners = [name for name, worth in player_worths.items() if worth == max_worth]
                    
                    if len(winners) == 1:
                        winner = winners[0]
                        human_player.set_game_ended(
                            winner=winner,
                            turn_count=turn_count,
                            error=str(e)
                        )
                    else:
                        # Draw or unclear winner
                        human_player.set_game_ended(
                            turn_count=turn_count,
                            is_draw=len(winners) > 1,
                            error=str(e)
                        )
                        if len(winners) > 1:
                            human_player.game_result["draw_players"] = winners
                except:
                    human_player.set_game_ended(
                        turn_count=turn_count,
                        error=str(e)
                    )
                break

            can_continue = True if can_continue == None else False
            if can_continue:
                game_manager.change_turn()
        
        # Handle max turns reached
        if turn_count >= max_turns and can_continue:
            handle_max_turns_reached(human_player, game_manager, players, turn_count)
            
    except Exception as e:
        print(f"Fatal error in game loop: {e}")
        human_player.set_game_ended(
            turn_count=turn_count,
            error=str(e)
        )

    print("\n\nGame ended. Server will continue running to display results...")
    print("Game result:", human_player.game_result)
    print("\n\nPress Ctrl+C to exit when ready.")
    
    # Keep the process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


def handle_max_turns_reached(human_player, game_manager, players, turn_count):
    """Handle game end when maximum turns are reached"""
    print(f"Maximum turns ({turn_count}) reached")
    
    # Calculate net worth for each player
    player_worths = {}
    for player in players:
        try:
            player_worths[player.name] = game_manager.game_state.get_player_net_worth(player)
        except Exception as e:
            print(f"Error calculating net worth for {player.name}: {e}")
            player_worths[player.name] = game_manager.game_state.player_balances.get(player, 0)
    
    print("Final net worths:", player_worths)
    
    # Determine winner(s)
    if player_worths:
        max_worth = max(player_worths.values())
        winners = [name for name, worth in player_worths.items() if worth == max_worth]
        
        if len(winners) > 1:
            # It's a draw
            human_player.set_game_ended(
                turn_count=turn_count,
                is_draw=True,
                max_turns_reached=True
            )
            human_player.game_result["draw_players"] = winners
        else:
            # Single winner
            winner = winners[0]
            human_player.set_game_ended(
                winner=winner,
                turn_count=turn_count,
                max_turns_reached=True
            )
    else:
        # No valid players (shouldn't happen)
        human_player.set_game_ended(
            turn_count=turn_count,
            max_turns_reached=True,
            error="No valid players found"
        )


def extract_player_name_from_exception(exception_str):
    """Extract player name from exception message"""
    # Handle different exception message formats
    if "is bankrupt" in exception_str:
        return exception_str.replace("BankrupcyException: ", "").replace(" is bankrupt", "")
    elif "NotEnoughBalanceException:" in exception_str:
        # Extract player name from balance exception if format allows
        return exception_str.split(":")[0].replace("NotEnoughBalanceException", "").strip()
    else:
        # Fallback - try to extract any player name from the string
        for player_name in ["Human Player", "DQN Player", "DQN player"]:
            if player_name in exception_str:
                return player_name
        return "Unknown Player"
    

if __name__ == "__main__":
    dqn_methods = {
        'buy_property': "../misc/saved_models/should_buy/dqn_agent_final",
        'get_upgrading_suggestions': "../misc/saved_models/upgrading/dqn_upgrading_final",
        'should_pay_get_out_of_jail_fine': "../misc/saved_models/jail_fine/dqn_agent_final",
        "get_downgrading_suggestions": "../misc/saved_models/downgrade/dqn_downgrading_final",
        'get_mortgaging_suggestions': "../misc/saved_models/mortgaging/dqn_mortgaging_final",
        'get_unmortgaging_suggestions': "../misc/saved_models/unmortgaging/dqn_unmortgaging_final",
        'should_use_escape_jail_card': "../misc/saved_models/escape_jail_card/dqn_escape_jail_card_final",
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
