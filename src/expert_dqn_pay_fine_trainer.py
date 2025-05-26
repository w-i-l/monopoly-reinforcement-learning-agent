import os
import time
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from tqdm import tqdm
import multiprocessing as mp
from collections import deque
import random
import json
import gc
from math import log, ceil

from managers.game_manager import GameManager
from agents.random_agent import RandomAgent
from agents.strategic_agent import StrategicAgent
from agents.default_strategic_player import DefaultStrategicPlayer, CautiousAccumulator, DynamicAdapter, LateGameDeveloper
from agents.expert_dqn_agent import DQNAgent  # Your updated DQN agent
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from exceptions.exceptions import BankrupcyException
from models.property_group import PropertyGroup
from game.game_state import GameState

# Set TensorFlow to only show errors
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def play_single_game_jail_focus(agent_types, max_turns=200, dqn_observer=None):
    """
    Play a single game and collect jail-related experiences.
    FIXED VERSION: Better jail decision detection
    """
    # Create agent instances
    players = [agent_type(f"{agent_type.__name__}_{i}") for i, agent_type in enumerate(agent_types)]
    
    # Create game manager
    game_manager = GameManager(players)
    
    # Game tracking
    turn_counter = 0
    active_players = len(players)
    jail_decisions = []
    
    try:
        while active_players > 1 and turn_counter < max_turns:
            current_player_idx = game_manager.game_state.current_player_index
            current_player = players[current_player_idx]
            
            # Check if current player is in jail before turn
            if game_manager.game_state.in_jail.get(current_player, False) and dqn_observer:
                try:
                    # Only collect data if player can actually pay
                    jail_fine = game_manager.game_state.board.get_jail_fine()
                    can_pay = game_manager.game_state.player_balances[current_player] >= jail_fine
                    
                    if can_pay:  # Only analyze meaningful decisions
                        # Encode current state for the observer
                        current_state = dqn_observer.encode_state(game_manager.game_state)
                        
                        # Check what the player would decide
                        # We need to call the actual method to see what they decide
                        jail_decision = current_player.should_pay_get_out_of_jail_fine(game_manager.game_state)
                        
                        jail_decision_data = {
                            'state': current_state,
                            'player': current_player,
                            'turn': turn_counter,
                            'action': int(jail_decision),  # 1 if pay, 0 if don't pay
                            'jail_fine': jail_fine,
                            'cash_before': game_manager.game_state.player_balances[current_player],
                            'turns_in_jail': game_manager.game_state.turns_in_jail.get(current_player, 0)
                        }
                        
                        jail_decisions.append(jail_decision_data)
                        
                except Exception as e:
                    print(f"Error collecting jail decision: {e}")
            
            # Play a turn
            try:
                game_manager.play_turn()
            except BankrupcyException:
                # Handle bankruptcy properly
                active_players -= 1
            except Exception as e:
                print(f"Game error: {e}")
            
            # Change turn
            game_manager.change_turn()
            turn_counter += 1
    
    except Exception as e:
        print(f"Game exception: {e}")
    
    # Calculate outcome for each player
    outcomes = {}
    for player in players:
        # Calculate final net worth
        net_worth = game_manager.game_state.get_player_net_worth(player)
        
        # Determine winner
        is_winner = True
        for other_player in players:
            if other_player != player and game_manager.game_state.player_balances[other_player] >= 0:
                is_winner = False
                break
        
        outcomes[player.name] = {
            'net_worth': net_worth,
            'winner': is_winner,
            'balance': game_manager.game_state.player_balances[player]
        }
    
    # SIMPLIFIED REWARD FUNCTION - much cleaner
    for decision in jail_decisions:
        player = decision['player']
        outcome = outcomes.get(player.name, {'net_worth': 0, 'winner': False, 'balance': 0})
        
        # Simple, clear reward logic
        base_reward = 0.0
        
        # Primary factor: Game outcome
        if outcome['winner']:
            base_reward = 0.4  # Good outcome
        elif outcome['balance'] < 0:
            base_reward = -0.4  # Bad outcome (bankrupt)
        else:
            # Neutral outcome based on final net worth
            base_reward = np.clip((outcome['net_worth'] - 1500) / 2000.0, -0.3, 0.3)
        
        # Secondary factor: Cash management
        cash_ratio = decision['cash_before'] / decision['jail_fine']
        
        if decision['action'] == 1:  # Paid to get out
            if cash_ratio >= 4.0:  # Had plenty of cash
                base_reward += 0.1  # Good decision to maintain mobility
            elif cash_ratio < 2.0:  # Tight on cash
                base_reward -= 0.2  # Risky decision
        else:  # Stayed in jail
            if cash_ratio < 3.0:  # Low cash
                base_reward += 0.1  # Good decision to preserve cash
            elif decision['turns_in_jail'] >= 2:  # Been in jail too long
                base_reward -= 0.1  # Should have paid to get out
        
        # Clip final reward
        decision['reward'] = np.clip(base_reward, -1.0, 1.0)
    
    return {
        'turns': turn_counter,
        'outcomes': outcomes,
        'jail_decisions': jail_decisions
    }

def collect_jail_experiences(num_games=100, use_multiprocessing=True, num_processes=None):
    """
    Collect learning experiences focused on jail decisions from games between various agent types.
    
    Args:
        num_games: Number of games to play
        use_multiprocessing: Whether to use multiprocessing
        num_processes: Number of processes to use
        
    Returns:
        List of jail decision experiences
    """
    print(f"Collecting jail experiences from {num_games} games...")
    
    # Agent types to use
    agent_types = [
        CautiousAccumulator,
        DynamicAdapter,
        StrategicAgent,
        DefaultStrategicPlayer
    ]
    
    # Create DQN observer to encode states
    dqn_observer = DQNAgent(
        "DQN_Observer", 
        training=False,
        dqn_methods={}  # Use parent class methods only
    )
    
    # Run games
    if use_multiprocessing and num_games > 10:
        # Set up multiprocessing
        if num_processes is None:
            num_processes = min(mp.cpu_count() - 1, 8)
            num_processes = max(num_processes, 1)
        
        print(f"Using {num_processes} processes for jail data collection")
        
        # Create arguments for each process
        games_per_process = num_games // num_processes
        remaining_games = num_games % num_processes
        
        process_args = []
        for i in range(num_processes):
            n_games = games_per_process
            if i < remaining_games:
                n_games += 1
            process_args.append((n_games, agent_types, i))
        
        # Start multiprocessing pool
        with mp.Pool(processes=num_processes) as pool:
            results = pool.map(_collect_jail_games_worker, process_args)
        
        # Combine results
        all_jail_decisions = []
        for result in results:
            all_jail_decisions.extend(result)
        
        return all_jail_decisions
    else:
        # Single process collection
        all_jail_decisions = []
        
        for i in tqdm(range(num_games), desc="Playing games"):
            # Select random agent types for this game
            game_agents = random.choices(agent_types, k=2)
            
            # Play a game
            game_result = play_single_game_jail_focus(game_agents, dqn_observer=dqn_observer)
            
            # Add jail decisions to collection
            if 'jail_decisions' in game_result:
                all_jail_decisions.extend(game_result['jail_decisions'])
        
        return all_jail_decisions

def _collect_jail_games_worker(args):
    """
    Worker function for parallel jail game collection.
    
    Args:
        args: Tuple of (num_games, agent_types, process_id)
        
    Returns:
        List of jail decisions from games
    """
    num_games, agent_types, process_id = args
    
    # Create a dedicated DQN observer for this process
    dqn_observer = DQNAgent(
        f"DQN_Observer_{process_id}", 
        state_dim=100, 
        training=False,
        dqn_methods={}  # Use parent class methods only
    )
    
    jail_decisions = []
    
    try:
        for i in tqdm(range(num_games), desc=f"Process {process_id}", position=process_id):
            try:
                # Select random agent types for this game
                game_agents = random.choices(agent_types, k=2)
                
                # Play a game
                game_result = play_single_game_jail_focus(game_agents, dqn_observer=dqn_observer)
                
                # Add jail decisions to collection
                if 'jail_decisions' in game_result:
                    jail_decisions.extend(game_result['jail_decisions'])
                    
            except Exception as e:
                print(f"Process {process_id}, Game {i} error: {e}")
                continue
                
    except Exception as e:
        print(f"Process {process_id} critical error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Process {process_id} collected {len(jail_decisions)} jail decisions")
    return jail_decisions

def prepare_jail_experiences_for_training(jail_decisions):
    """
    Convert jail decisions into training examples.
    
    Args:
        jail_decisions: List of jail decision dictionaries
        
    Returns:
        List of experience tuples (state, action, reward, next_state, done)
    """
    if not jail_decisions:
        return []
    
    experiences = []
    
    for decision in jail_decisions:
        # Basic structure of an experience
        state = decision['state']
        action = decision['action']
        reward = decision['reward']
        
        # Use the same state as next_state since we don't track it
        next_state = decision['state']
        
        # Always done since these are isolated decisions
        done = 1.0
        
        experiences.append((state, action, reward, next_state, done))
    
    return experiences

def pretrain_jail_dqn_from_experiences(dqn_agent, experiences, batch_size=32, epochs=5):
    """
    Pretrain the DQN agent from collected jail experiences.
    
    Args:
        dqn_agent: DQN agent to train
        experiences: List of experience tuples
        batch_size: Batch size for training
        epochs: Number of training epochs
        
    Returns:
        Training statistics
    """
    print(f"Pretraining DQN agent on {len(experiences)} jail experiences...")
    
    # Initialize training stats
    stats = {
        'loss': []
    }
    
    # Add all experiences to agent's memory
    for exp in experiences:
        dqn_agent.memory['should_pay_get_out_of_jail_fine'].append(exp)
    
    # Train for multiple epochs
    for epoch in range(epochs):
        print(f"Epoch {epoch+1}/{epochs}")
        
        # Calculate number of batches
        num_batches = len(experiences) // batch_size
        
        # Track epoch stats
        epoch_loss = []
        
        # Train on batches
        for _ in tqdm(range(num_batches), desc="Training batches"):
            # Train on a batch and get loss
            loss = dqn_agent.train_on_batch('should_pay_get_out_of_jail_fine')
            if loss is not None:
                epoch_loss.append(loss)
        
        # Add average loss for this epoch
        if epoch_loss:
            stats['loss'].append(np.mean(epoch_loss))
        else:
            stats['loss'].append(0.0)
    
    return stats

def train_jail_dqn_through_gameplay(
        dqn_agent, 
        num_games=500, 
        max_turns=200, 
        batch_size=32, 
        evaluation_games=350,
        evaluation_interval=100, 
        save_interval=150, 
        save_path='models/jail_fine'
        ):
    """
    Train the DQN agent through actual gameplay focusing on jail decisions.
    
    Args:
        dqn_agent: DQN agent to train
        num_games: Number of games to play
        max_turns: Maximum turns per game
        batch_size: Batch size for training
        evaluation_interval: How often to evaluate
        save_interval: How often to save the model
        save_path: Path to save models
        
    Returns:
        Training statistics
    """
    # Create directory for saving models
    os.makedirs(save_path, exist_ok=True)
    
    print(f"Training DQN agent on jail decisions through {num_games} games of gameplay...")
    
    # Opponents
    opponents = [
        DefaultStrategicPlayer,
        LateGameDeveloper,
        CautiousAccumulator
    ]
    
    # Training stats
    stats = {
        'game_returns': [],
        'win_rate': [],
        'epsilon': [],
        'jail_decisions_per_game': []
    }
    
    # Rolling stats
    returns_window = deque(maxlen=100)
    wins_window = deque(maxlen=100)
    jail_decisions_window = deque(maxlen=100)
    
    # Play games
    for game_idx in tqdm(range(num_games), desc="Training games"):
        # Set agent to training mode
        dqn_agent.training = True
        
        # Select opponent
        opponent_type = random.choice(opponents)
        opponent = opponent_type(f"{opponent_type.__name__}_{game_idx}")
        
        # Alternate who goes first
        if game_idx % 2 == 0:
            players = [dqn_agent, opponent]
        else:
            players = [opponent, dqn_agent]
        
        # Create game
        game_manager = GameManager(players)
        
        # Track game progress
        turn_counter = 0
        active_players = len(players)
        game_return = 0.0
        jail_decisions_count = 0
        
        try:
            while active_players > 1 and turn_counter < max_turns:
                current_player_idx = game_manager.game_state.current_player_index
                current_player = players[current_player_idx]
                
                # If it's the DQN agent's turn and they're in jail
                if current_player == dqn_agent and game_manager.game_state.in_jail.get(dqn_agent, False):
                    jail_decisions_count += 1
                    # Update previous jail decision with current state if exists
                    if dqn_agent.current_decisions['should_pay_get_out_of_jail_fine']:
                        dqn_agent.update_decision('should_pay_get_out_of_jail_fine', game_manager.game_state)
                
                # Play a turn
                try:
                    game_manager.play_turn()
                except BankrupcyException:
                    # Handle bankruptcy properly
                    active_players -= 1
                except Exception as e:
                    print(f"Game error: {e}")
                
                # Change turn
                game_manager.change_turn()
                turn_counter += 1
            
            # Game ended - calculate final outcome
            is_winner = False
            agent_net_worth = game_manager.game_state.get_player_net_worth(dqn_agent)
            opponent_net_worth = game_manager.game_state.get_player_net_worth(opponent)
            if agent_net_worth > opponent_net_worth:
                is_winner = True
            
            # Calculate game return
            game_return = agent_net_worth / 3000.0  # Normalize
            if is_winner:
                game_return += 1.0
            
            # Update rolling stats
            returns_window.append(game_return)
            wins_window.append(1.0 if is_winner else 0.0)
            jail_decisions_window.append(jail_decisions_count)
            
            # Update overall stats
            stats['game_returns'].append(game_return)
            stats['win_rate'].append(np.mean(wins_window))
            stats['epsilon'].append(dqn_agent.epsilon)
            stats['jail_decisions_per_game'].append(np.mean(jail_decisions_window))
            
            # Finalize any pending jail decision
            if dqn_agent.current_decisions['should_pay_get_out_of_jail_fine']:
                dqn_agent.update_decision('should_pay_get_out_of_jail_fine', game_manager.game_state, done=True)
            
            # Evaluate periodically
            if (game_idx + 1) % evaluation_interval == 0:
                eval_stats = play_evaluation_games(dqn_agent, num_games=evaluation_games)
                print(f"Evaluation after {game_idx+1} games:")
                print(f"  Win rate: {eval_stats['overall_win_rate']:.2%}")
                print(f"  Average jail decisions per game: {np.mean(jail_decisions_window):.1f}")
            
            # Save periodically
            if (game_idx + 1) % save_interval == 0:
                model_path = os.path.join(save_path, f"dqn_agent_game_{game_idx+1}")
                dqn_agent.save_model_for_method('should_pay_get_out_of_jail_fine', model_path)
                print(f"Model saved to {model_path}")
                
                # Plot and save stats
                plot_training_stats(stats, filename=os.path.join(save_path, f"training_stats_{game_idx+1}.png"))
                
                # Save stats to JSON
                stats_path = os.path.join(save_path, f"training_stats_{game_idx+1}.json")
                with open(stats_path, 'w') as f:
                    json.dump(stats, f)

                # clear memory
                gc.collect()
        
        except Exception as e:
            print(f"Error in game {game_idx}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save final model
    final_model_path = os.path.join(save_path, "dqn_agent_final")
    dqn_agent.save_model_for_method('should_pay_get_out_of_jail_fine', final_model_path)
    print(f"Final model saved to {final_model_path}")
    
    # Plot final stats
    plot_training_stats(stats, filename=os.path.join(save_path, "training_stats_final.png"))
    
    # Save final stats to JSON
    final_stats_path = os.path.join(save_path, "training_stats_final.json")
    with open(final_stats_path, 'w') as f:
        json.dump(stats, f)
    
    return stats

def play_evaluation_games(dqn_agent, num_games=50, max_turns=200):
    """
    Evaluate the DQN agent's performance against other agents.
    
    Args:
        dqn_agent: DQN agent to evaluate
        num_games: Number of evaluation games
        max_turns: Maximum number of turns per game
        
    Returns:
        Evaluation statistics
    """
    print(f"Evaluating DQN agent over {num_games} games...")
    
    # Set the agent to evaluation mode
    dqn_agent.training = False
    
    # Opponents to test against
    opponents = [
        DefaultStrategicPlayer("Default"),
        LateGameDeveloper("LateGame"),
        CautiousAccumulator("Cautious")
    ]
    
    # Stats to track
    stats = {
        opponent.__class__.__name__: {
            'wins': 0,
            'losses': 0,
            'draws': 0,
            'avg_net_worth': 0,
            'games_played': 0
        } for opponent in opponents
    }
    
    # Play games
    game_count = 0
    for opponent in opponents:
        for i in tqdm(range(num_games), desc=f"vs {opponent.__class__.__name__}"):
            # Reset opponent for each game
            opponent_instance = opponent.__class__(f"{opponent.__class__.__name__}_{i}")
            
            # Alternate who goes first
            if i % 2 == 0:
                players = [dqn_agent, opponent_instance]
            else:
                players = [opponent_instance, dqn_agent]
            
            # Create game
            game_manager = GameManager(players)
            
            # Play the game
            turn_counter = 0
            active_players = len(players)
            
            try:
                while active_players > 1 and turn_counter < max_turns:
                    try:
                        # Play a turn
                        game_manager.play_turn()
                    except BankrupcyException:
                        # Handle bankruptcy properly
                        active_players -= 1
                    except Exception as e:
                        print(f"Game error: {e}")
                    
                    # Change turn
                    game_manager.change_turn()
                    turn_counter += 1
            except Exception as e:
                print(f"Game error: {e}")
            
            # Record outcome
            opponent_key = opponent.__class__.__name__
            stats[opponent_key]['games_played'] += 1
            
            # Calculate net worths
            dqn_net_worth = game_manager.game_state.get_player_net_worth(dqn_agent)
            opponent_net_worth = game_manager.game_state.get_player_net_worth(opponent_instance)
            
            stats[opponent_key]['avg_net_worth'] += dqn_net_worth
            
            # Determine winner
            if game_manager.game_state.player_balances[dqn_agent] < 0:
                stats[opponent_key]['losses'] += 1
            elif game_manager.game_state.player_balances[opponent_instance] < 0:
                stats[opponent_key]['wins'] += 1
            else:
                # Draw - compare net worth
                if dqn_net_worth > opponent_net_worth:
                    stats[opponent_key]['wins'] += 1
                elif dqn_net_worth < opponent_net_worth:
                    stats[opponent_key]['losses'] += 1
                else:
                    stats[opponent_key]['draws'] += 1
            
            game_count += 1
    
    # Calculate average net worth
    for opponent_key in stats:
        if stats[opponent_key]['games_played'] > 0:
            stats[opponent_key]['avg_net_worth'] /= stats[opponent_key]['games_played']
    
    # Calculate overall stats
    total_games = sum(stats[k]['games_played'] for k in stats)
    total_wins = sum(stats[k]['wins'] for k in stats)
    
    overall_win_rate = total_wins / total_games if total_games > 0 else 0
    
    print("\nEvaluation Results:")
    print(f"Overall win rate: {overall_win_rate:.2%}")
    for opponent_key, opponent_stats in stats.items():
        win_rate = opponent_stats['wins'] / opponent_stats['games_played'] if opponent_stats['games_played'] > 0 else 0
        print(f"  vs {opponent_key}: {win_rate:.2%} win rate, ${opponent_stats['avg_net_worth']:.2f} avg net worth")
    
    # Set the agent back to training mode
    dqn_agent.training = True
    
    return {
        'overall_win_rate': overall_win_rate,
        'opponent_stats': stats
    }

def plot_training_stats(stats, filename='training_stats.png'):
    """
    Plot training statistics.
    
    Args:
        stats: Dictionary of training statistics
        filename: Filename to save the plot
    """
    plt.figure(figsize=(12, 10))
    
    # Plot each statistic
    for i, (key, values) in enumerate(stats.items(), 1):
        plt.subplot(len(stats), 1, i)
        plt.plot(values)
        plt.title(key)
        plt.grid(True)
        
        # Add smoother trend line
        if len(values) > 10:
            window_size = min(len(values) // 5, 10)
            smoothed = np.convolve(values, np.ones(window_size)/window_size, mode='valid')
            plt.plot(range(window_size-1, len(values)), smoothed, 'r--', linewidth=2)
    
    plt.tight_layout()
    plt.savefig(filename)
    print(f"Training stats saved to {filename}")
    plt.close()

class EpsilonConfig:
    def __init__(
            self, 
            start=1.0,
            end=0.1,
            decay=0.995, 
            num_games=10_000, 
            stop_exploration_after=0.7):
        """
        Configuration for epsilon decay in DQN training.

        Args:
            start: Starting value of epsilon
            end: Ending value of epsilon
            decay: Decay rate for epsilon
            num_games: Total number of games to play
            stop_exploration_after: Percentage of games after which to reach epsilon_end
        """

        self.start = start
        self.end = end
        self.decay = decay
        self.num_games = num_games
        self.stop_exploration_after = stop_exploration_after

def calculate_epsilon_update_freq(epsilon_config: EpsilonConfig) -> int:
    """
    Calculate the frequency of epsilon updates based on the number of games.

    Returns:    
        int: Frequency of epsilon updates
    """

    # Calculate the number of games to reach the end epsilon
    games_to_reach_end_epsilon = int(epsilon_config.num_games * epsilon_config.stop_exploration_after)

    # Calculate the number of updates needed to reach the end epsilon
    num_updates = log(epsilon_config.end / epsilon_config.start) / log(epsilon_config.decay)
    num_updates = ceil(num_updates)

    # Calculate the frequency of updates
    update_freq = games_to_reach_end_epsilon // num_updates
    update_freq = max(update_freq, 1)  # Ensure at least one update

    return update_freq

def run_jail_training_pipeline(
        pretraining_iteration_games=1000, 
        pretraining_iteration_epochs=3, 
        pretraining_iterations=5, 
        evaluation_games=350,
        training_games=500, 
        max_turns=200,
        batch_size=32, 
        save_path='models/jail_fine', 
        load_path=None,
        buy_property_model_path=None,
        upgrading_model_path=None,
        epsilon_config=None
        ):
    """
    Run the complete DQN training pipeline for jail fine decisions.
    
    Args:
        pretraining_iteration_games: Number of games for pretraining per iteration
        pretraining_iteration_epochs: Number of epochs for pretraining per iteration
        pretraining_iterations: Number of pretraining iterations
        training_games: Number of games for training
        evaluation_games: Number of games for evaluation
        max_turns: Maximum turns per game
        batch_size: Batch size for training
        save_path: Path to save models
        load_path: Path to load pretrained jail model (optional)
        buy_property_model_path: Path to load buy property model (optional)
        upgrading_model_path: Path to load upgrading model (optional)
        
    Returns:
        Trained DQN agent and statistics
    """
    
    print("Starting DQN jail fine training pipeline")
    start_time = time.time()
    
    # Configure which methods use DQN
    dqn_methods = {
        'buy_property': buy_property_model_path,
        'get_upgrading_suggestions': upgrading_model_path,
        'should_pay_get_out_of_jail_fine': load_path
    }
    
    NUM_PROCESSES = 8
    baseline = 510_000 # updates for 8 processes 5k training games
    num_games = int(training_games * NUM_PROCESSES / baseline)
    if epsilon_config is None:
        epsilon_config = EpsilonConfig(
            start=1.0,
            end=0.1,
            decay=0.995,
            num_games=num_games,
            stop_exploration_after=0.7
        )

    # Calculate epsilon update frequency
    epsilon_update_freq = calculate_epsilon_update_freq(epsilon_config)

    # Create DQN agent
    dqn_agent = DQNAgent(
        "DQN_Agent", 
        state_dim=100, 
        hidden_dims=[128, 64, 32],
        learning_rate=0.001,
        gamma=0.99,
        epsilon_start=epsilon_config.start,
        epsilon_end=epsilon_config.end,
        epsilon_decay=epsilon_config.decay,
        epsilon_update_freq=epsilon_update_freq,
        batch_size=batch_size,
        training=True,
        dqn_methods=dqn_methods,
        active_training_method='should_pay_get_out_of_jail_fine',
        can_use_defaults_methods= {
            'buy_property': True,  # TODO: Set to False if you want to load buy_property model
            'get_upgrading_suggestions': True,  # TODO: Set to False if you want to load upgrading model
            'should_pay_get_out_of_jail_fine': False,  # Training this method
        }
    )

    # Create save directory
    os.makedirs(save_path, exist_ok=True)
    
    for i in tqdm(range(pretraining_iterations), desc="Training iterations"):
        # Step 1: Collect experiences from other agents
        experiences = collect_jail_experiences(
            num_games=pretraining_iteration_games,
            use_multiprocessing=True
        )
        
        # Prepare experiences for training
        training_data = prepare_jail_experiences_for_training(experiences)
        
        # Step 2: Pretrain on collected experiences
        if training_data:
            print(f"Pretraining on {len(training_data)} jail experiences")
            pretrain_stats = pretrain_jail_dqn_from_experiences(
                dqn_agent,
                training_data,
                batch_size=batch_size,
                epochs=pretraining_iteration_epochs
            )
            
            # Save pretrained model
            pretrain_model_path = os.path.join(save_path, "dqn_agent_pretrained")
            dqn_agent.save_model_for_method('should_pay_get_out_of_jail_fine', pretrain_model_path)
            print(f"Pretrained model saved to {pretrain_model_path}")
            
            # Plot pretraining stats
            plot_training_stats(pretrain_stats, filename=os.path.join(save_path, "pretrain_stats.png"))
        else:
            print("No pretraining data available, skipping pretraining")
        
        # Clean up memory
        del experiences
        gc.collect()

        # Step 3: Evaluate pretrained agent
        print("Evaluating pretrained agent")
        pretrain_eval_stats = play_evaluation_games(dqn_agent, num_games=evaluation_games)
        
    # Step 4: Train through gameplay
    print("Starting training through gameplay")
    gameplay_stats = train_jail_dqn_through_gameplay(
        dqn_agent,
        num_games=training_games,
        max_turns=max_turns,
        evaluation_games=evaluation_games,
        batch_size=batch_size,
        save_path=save_path
    )
    
    # Calculate training time
    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.2f} seconds")
    
    return dqn_agent, gameplay_stats

if __name__ == "__main__":
    baseline_num_games = 40_000 # updates for 8 processes 5k training games
    baseline_num_processes = 8
    baseline_training_games = 2_000

    num_processes = 3
    training_games = 10_000
    num_games = int(training_games * baseline_num_games / baseline_training_games * num_processes / baseline_num_processes)

    epsilon_config = EpsilonConfig(
        start=1.0,
        end=0.1,
        decay=0.995,
        num_games=num_games,
        stop_exploration_after=0.7
    )

    print(f"Update frequency for epsilon: {calculate_epsilon_update_freq(epsilon_config)}")

    # Run the training pipeline
    agent, gameplay_stats = run_jail_training_pipeline(
        pretraining_iteration_games=5_000,  # Start with a reasonable number of games
        pretraining_iteration_epochs=1,
        pretraining_iterations=15,
        training_games=training_games,
        evaluation_games=100,
        max_turns=500,
        batch_size=64,
        save_path='saved_models/dqn/jail_fine/v2/',
        epsilon_config=epsilon_config,
        # TODO: Uncomment and provide paths when you have trained models for other methods
        # buy_property_model_path='path/to/buy_property_model',
        # upgrading_model_path='path/to/upgrading_model',
    )
    
    print("Training complete!")