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
from agents.algorithmic_agent import AlgorithmicAgent
from agents.strategic_agent import StrategicAgent, CautiousAccumulator, DynamicAdapter, LateGameDeveloper
from agents.dqn_agent import DQNAgent  # Your updated DQN agent
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from exceptions.exceptions import BankrupcyException
from models.property_group import PropertyGroup

# Set TensorFlow to only show errors
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def play_single_game_for_downgrading(agent_types, max_turns=200, dqn_observer=None):
    """
    Play a single game and collect downgrading experiences.
    
    Args:
        agent_types: List of agent types to use (not instances)
        max_turns: Maximum number of turns
        dqn_observer: Optional DQN agent to observe and learn
        
    Returns:
        Game data and collected experiences
    """
    # Create agent instances
    players = [agent_type(f"{agent_type.__name__}_{i}") for i, agent_type in enumerate(agent_types)]
    
    # Create game manager
    game_manager = GameManager(players)
    
    # Game tracking
    turn_counter = 0
    active_players = len(players)
    downgrading_decisions = []
    
    try:
        while active_players > 1 and turn_counter < max_turns:
            current_player_idx = game_manager.game_state.current_player_index
            current_player = players[current_player_idx]
            
            # Record state before turn for downgrading decisions
            if dqn_observer:
                try:
                    # Encode current state
                    current_state = dqn_observer.encode_state(game_manager.game_state)
                    
                    # Get the player's downgrading decision using a temporary DefaultStrategicPlayer
                    # This way we collect data on how the strategic agent makes decisions
                    temp_player = StrategicAgent(f"Temp_{current_player.name}")
                    # Copy current player's properties and position to temp player
                    game_manager.game_state.properties[temp_player] = game_manager.game_state.properties[current_player]
                    game_manager.game_state.player_positions[temp_player] = game_manager.game_state.player_positions[current_player]
                    game_manager.game_state.player_balances[temp_player] = game_manager.game_state.player_balances[current_player]
                    
                    # Get suggestions from the temp player
                    downgrade_groups = temp_player.get_downgrading_suggestions(game_manager.game_state)
                    
                    # Convert decision to action index
                    if downgrade_groups:
                        # Use the first group (in case multiple are returned)
                        selected_group = downgrade_groups[0]
                        # Use the enum's ordinal (index) instead of trying to convert the string value
                        action = selected_group.ordinal if hasattr(selected_group, 'ordinal') else list(PropertyGroup).index(selected_group)
                    else:
                        action = -1  # No downgrade
                    
                    # Remove temp player from game state to avoid side effects
                    if temp_player in game_manager.game_state.properties:
                        del game_manager.game_state.properties[temp_player]
                    if temp_player in game_manager.game_state.player_positions:
                        del game_manager.game_state.player_positions[temp_player]
                    if temp_player in game_manager.game_state.player_balances:
                        del game_manager.game_state.player_balances[temp_player]
                    
                    # Record downgrading decision
                    downgrading_decisions.append({
                        'state': current_state,
                        'action': action,
                        'player': current_player,
                        'turn': turn_counter
                    })
                except Exception as e:
                    print(f"Error recording downgrading decision: {e}")
                    import traceback
                    traceback.print_exc()
            
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
    
    # Calculate rewards for downgrading decisions
    for decision in downgrading_decisions:
        player = decision['player']
        outcome = outcomes.get(player.name, {'net_worth': 0, 'winner': False, 'balance': 0})
        
        # Reward calculation for downgrading - focus on financial stability and strategic management
        if outcome['winner']:
            decision['reward'] = 1.0
        elif outcome['balance'] < 0:
            # Bankruptcy - but downgrading might have delayed it, so less severe penalty
            decision['reward'] = -0.7
        else:
            # Base reward on net worth, but consider cash management
            net_worth_reward = np.clip(outcome['net_worth'] / 3000.0 - 0.5, -1.0, 1.0)
            
            # Bonus for maintaining positive cash balance (key for downgrading decisions)
            cash_bonus = 0.0
            if outcome['balance'] > 500:
                cash_bonus = 0.2  # Good cash management
            elif outcome['balance'] > 200:
                cash_bonus = 0.1  # Adequate cash management
            elif outcome['balance'] < 50:
                cash_bonus = -0.3  # Poor cash management
            
            decision['reward'] = net_worth_reward + cash_bonus
    
    return {
        'turns': turn_counter,
        'outcomes': outcomes,
        'downgrading_decisions': downgrading_decisions
    }

def collect_downgrading_experiences(num_games=100, use_multiprocessing=True, num_processes=None):
    """
    Collect downgrading decision experiences from games between various agent types.
    
    Args:
        num_games: Number of games to play
        use_multiprocessing: Whether to use multiprocessing
        num_processes: Number of processes to use
        
    Returns:
        List of downgrading decision experiences
    """
    print(f"Collecting downgrading experiences from {num_games} games...")
    
    # Agent types to use
    agent_types = [
        CautiousAccumulator,
        DynamicAdapter,
        StrategicAgent,
        StrategicAgent
    ]
    
    # Create DQN observer to encode states
    # Use parent class implementation for all methods (no DQN)
    dqn_observer = DQNAgent(
        "DQN_Observer", 
        training=False,
        dqn_methods={}  # Use parent class methods only
    )
    
    # Run games
    if use_multiprocessing and num_games > 10:
        # Set up multiprocessing
        if num_processes is None:
            num_processes = min(mp.cpu_count() - 1, 8)  # Use at most 8 processes
            num_processes = max(num_processes, 1)  # At least 1 process
        
        print(f"Using {num_processes} processes for data collection")
        
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
            results = pool.map(_collect_downgrading_games_worker, process_args)
        
        # Combine results
        all_downgrading_decisions = []
        for result in results:
            all_downgrading_decisions.extend(result)
        
        return all_downgrading_decisions
    else:
        # Single process collection
        all_downgrading_decisions = []
        
        for i in tqdm(range(num_games), desc="Playing games"):
            # Select random agent types for this game
            game_agents = random.choices(agent_types, k=2)
            
            # Play a game
            game_result = play_single_game_for_downgrading(game_agents, dqn_observer=dqn_observer)
            
            # Add downgrading decisions to collection
            if 'downgrading_decisions' in game_result:
                all_downgrading_decisions.extend(game_result['downgrading_decisions'])
        
        return all_downgrading_decisions

def _collect_downgrading_games_worker(args):
    """
    Worker function for parallel game collection.
    
    Args:
        args: Tuple of (num_games, agent_types, process_id)
        
    Returns:
        List of downgrading decisions from games
    """
    num_games, agent_types, process_id = args
    
    # Create a dedicated DQN observer for this process
    dqn_observer = DQNAgent(
        f"DQN_Observer_{process_id}", 
        state_dim=100, 
        training=False,
        dqn_methods={}  # Use parent class methods only
    )
    
    downgrading_decisions = []
    
    # Create a mapping of property group values to indices
    property_group_indices = {group.value: i for i, group in enumerate(PropertyGroup)}
    
    try:
        for i in tqdm(range(num_games), desc=f"Process {process_id}", position=process_id):
            try:
                # Select random agent types for this game
                game_agents = random.choices(agent_types, k=2)
                
                # Play a game
                game_result = play_single_game_for_downgrading(game_agents, dqn_observer=dqn_observer)
                
                # Add downgrading decisions to collection
                if 'downgrading_decisions' in game_result:
                    # Normalize actions to indices
                    for decision in game_result['downgrading_decisions']:
                        action = decision.get('action')
                        
                        # Convert string property group values to indices
                        if isinstance(action, str) and action in property_group_indices:
                            decision['action'] = property_group_indices[action]
                        # Keep numeric actions as-is (including -1 for no downgrade)
                        elif isinstance(action, (int, float)):
                            decision['action'] = int(action)
                        else:
                            # Default to no downgrade if action is invalid
                            decision['action'] = -1
                    
                    downgrading_decisions.extend(game_result['downgrading_decisions'])
                    
            except Exception as e:
                print(f"Process {process_id}, Game {i} error: {e}")
                import traceback
                traceback.print_exc()
                continue
                
    except Exception as e:
        print(f"Process {process_id} critical error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"Process {process_id} collected {len(downgrading_decisions)} downgrading decisions")
    return downgrading_decisions

def prepare_downgrading_experiences_for_training(downgrading_decisions):
    """
    Convert downgrading decisions into training examples.
    
    Args:
        downgrading_decisions: List of downgrading decision dictionaries
        
    Returns:
        List of experience tuples (state, action, reward, next_state, done)
    """
    if not downgrading_decisions:
        return []
    
    experiences = []
    
    # Create a mapping of property group names to indices
    property_group_indices = {group.value: i for i, group in enumerate(PropertyGroup)}
    
    for decision in downgrading_decisions:
        # Basic structure of an experience
        state = decision['state']
        
        # Handle different action types
        action = decision['action']
        
        # Convert string property group values to indices
        if isinstance(action, str) and action in property_group_indices:
            action = property_group_indices[action]
        # Keep numeric actions as-is (including -1 for no downgrade)
        elif isinstance(action, (int, float)):
            action = int(action)
        else:
            # Default to no downgrade if action is invalid
            action = -1
            
        reward = decision['reward']
        
        # Use the same state as next_state since we don't track it
        next_state = decision['state']
        
        # Always done since these are isolated decisions
        done = 1.0
        
        experiences.append((state, action, reward, next_state, done))
    
    return experiences

def pretrain_dqn_for_downgrading(dqn_agent, experiences, batch_size=32, epochs=5):
    """
    Pretrain the DQN agent for downgrading decisions from collected experiences.
    
    Args:
        dqn_agent: DQN agent to train
        experiences: List of experience tuples
        batch_size: Batch size for training
        epochs: Number of training epochs
        
    Returns:
        Training statistics
    """
    print(f"Pretraining DQN agent for downgrading on {len(experiences)} experiences...")
    
    # Initialize training stats
    stats = {
        'loss': []
    }
    
    # Add all experiences to agent's memory
    for exp in experiences:
        dqn_agent.memory['get_downgrading_suggestions'].append(exp)
    
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
            loss = dqn_agent.train_on_batch('get_downgrading_suggestions')
            if loss is not None:
                epoch_loss.append(loss)
        
        # Add average loss for this epoch
        if epoch_loss:
            stats['loss'].append(np.mean(epoch_loss))
        else:
            stats['loss'].append(0.0)
    
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
        StrategicAgent("Strategic"),
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
        print(f"  vs {opponent_key}: {win_rate:.2%} win rate, {opponent_stats['avg_net_worth']:.2f}₩ avg net worth")
    
    # Set the agent back to training mode
    dqn_agent.training = True
    
    return {
        'overall_win_rate': overall_win_rate,
        'opponent_stats': stats
    }

def train_dqn_downgrading_through_gameplay(
        dqn_agent: DQNAgent, 
        num_games=500, 
        max_turns=200, 
        batch_size=32, 
        evaluation_games=350,
        evaluation_interval=100, 
        save_interval=150, 
        save_path='models/downgrading'
        ):
    """
    Train the DQN agent's downgrading decision through actual gameplay.
    
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
    
    print(f"Training DQN agent's downgrading decisions through {num_games} games of gameplay...")
    
    # Opponents
    opponents = [
        StrategicAgent,
        LateGameDeveloper,
        CautiousAccumulator
    ]
    
    # Training stats
    stats = {
        'game_returns': [],
        'win_rate': [],
        'epsilon': []
    }
    
    # Rolling stats
    returns_window = deque(maxlen=100)
    wins_window = deque(maxlen=100)
    
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
        
        try:
            while active_players > 1 and turn_counter < max_turns:
                current_player_idx = game_manager.game_state.current_player_index
                current_player = players[current_player_idx]
                
                # If it's the DQN agent's turn
                if current_player == dqn_agent:
                    # Update previous downgrading decision with current state
                    if dqn_agent.current_decisions['get_downgrading_suggestions']:
                        dqn_agent.update_decision('get_downgrading_suggestions', game_manager.game_state)
                
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
            if dqn_agent in game_manager.game_state.players and game_manager.game_state.player_balances[dqn_agent] >= 0:
                for p in game_manager.game_state.players:
                    if p != dqn_agent and game_manager.game_state.player_balances[p] < 0:
                        is_winner = True
                        break
            
            # Calculate game return
            agent_net_worth = game_manager.game_state.get_player_net_worth(dqn_agent)
            game_return = agent_net_worth / 3000.0  # Normalize
            if is_winner:
                game_return += 1.0
            
            # Update rolling stats
            returns_window.append(game_return)
            wins_window.append(1.0 if is_winner else 0.0)
            
            # Update overall stats
            stats['game_returns'].append(game_return)
            stats['win_rate'].append(np.mean(wins_window))
            stats['epsilon'].append(dqn_agent.epsilon)
            
            # Finalize any pending downgrading decision
            if dqn_agent.current_decisions['get_downgrading_suggestions']:
                dqn_agent.update_decision('get_downgrading_suggestions', game_manager.game_state, done=True)
            
            # Evaluate periodically
            if (game_idx + 1) % evaluation_interval == 0:
                eval_stats = play_evaluation_games(dqn_agent, num_games=evaluation_games)
                print(f"Evaluation after {game_idx+1} games:")
                print(f"  Win rate: {eval_stats['overall_win_rate']:.2%}")
            
            # Save periodically
            if (game_idx + 1) % save_interval == 0:
                model_path = os.path.join(save_path, f"dqn_downgrading_game_{game_idx+1}")
                dqn_agent.save_model_for_method('get_downgrading_suggestions', model_path)
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
    final_model_path = os.path.join(save_path, "dqn_downgrading_final")
    dqn_agent.save_model_for_method('get_downgrading_suggestions', final_model_path)
    print(f"Final model saved to {final_model_path}")
    
    # Plot final stats
    plot_training_stats(stats, filename=os.path.join(save_path, "training_stats_final.png"))
    
    # Save final stats to JSON
    final_stats_path = os.path.join(save_path, "training_stats_final.json")
    with open(final_stats_path, 'w') as f:
        json.dump(stats, f)
    
    return stats

def plot_training_stats(stats, filename='training_stats.png'):
    """
    Plot training statistics.
    
    Args:
        stats: Dictionary of training statistics
        filename: Filename to save the plot
    """
    plt.figure(figsize=(12, 8))
    
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
    # epsilon_end = epsilon_start * (epsilon_decay ** num_updates)
    num_updates = log(epsilon_config.end / epsilon_config.start) / log(epsilon_config.decay)
    num_updates = ceil(num_updates)

    # Calculate the frequency of updates
    update_freq = games_to_reach_end_epsilon // num_updates
    update_freq = max(update_freq, 1)  # Ensure at least one update

    return update_freq

def plot_epsilon_decay(epsilon_config: EpsilonConfig) -> None:
    """
    Plot the decay of epsilon over the number of games.

    Args:
        epsilon_config: Configuration object for epsilon decay
    """
    # Calculate the number of games to reach the end epsilon
    epsilon_update_freq = calculate_epsilon_update_freq(epsilon_config)

    epsilon_updates = []
    epsilon = epsilon_config.start
    for game in range(epsilon_config.num_games):
        if game % epsilon_update_freq == 0:
            epsilon = max(epsilon * epsilon_config.decay, epsilon_config.end)
        epsilon_updates.append(epsilon)

    plt.figure(figsize=(10, 6))
    plt.plot(range(epsilon_config.num_games), epsilon_updates, label='Epsilon Decay')
    plt.title('Epsilon Decay Over Games')
    plt.xlabel('Games Played')
    plt.ylabel('Epsilon Value')
    plt.axhline(y=epsilon_config.end, color='r', linestyle='--', label='Epsilon End')
    plt.legend()
    plt.grid()
    plt.show()

def run_downgrading_training_pipeline(
        pretraining_iteration_games=1000, 
        pretraining_iteration_epochs=3, 
        pretraining_iterations=5, 
        evaluation_games=350,
        training_games=500, 
        max_turns=200,
        batch_size=32, 
        save_path='models/downgrading', 
        load_path=None,
        property_buy_model_path=None,
        upgrading_model_path=None,
        jail_fine_model_path=None,
        epsilon_config=None
        ):
    """
    Run the complete DQN training pipeline for downgrading suggestions.
    
    Args:
        pretraining_iteration_games: Number of games for pretraining per iteration
        pretraining_iteration_epochs: Number of epochs for pretraining per iteration
        pretraining_iterations: Number of pretraining iterations
        training_games: Number of games for training
        evaluation_games: Number of games for evaluation
        max_turns: Maximum turns per game
        batch_size: Batch size for training
        save_path: Path to save models
        load_path: Path to load pretrained downgrading model (optional)
        property_buy_model_path: Path to load property buying model (optional)
        upgrading_model_path: Path to load upgrading model (optional)
        jail_fine_model_path: Path to load jail fine model (optional)
        epsilon_config: Configuration for epsilon decay (optional)
        
    Returns:
        Trained DQN agent and statistics
    """
    
    print("Starting DQN downgrading suggestions training pipeline")
    start_time = time.time()
    
    # Configure which methods use DQN
    dqn_methods = {
        'buy_property': property_buy_model_path,  # None means use parent class method
        'get_upgrading_suggestions': upgrading_model_path,  # None means use parent class method
        'get_downgrading_suggestions': load_path,
        'should_pay_get_out_of_jail_fine': jail_fine_model_path  # None means use parent class method
    }
    
    NUM_PROCESSES = 8
    baseline = 700_000 # updates for 8 processes 5k training games
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
        active_training_method='get_downgrading_suggestions',
        can_use_defaults_methods= {
            'buy_property': property_buy_model_path is None,
            'get_upgrading_suggestions': upgrading_model_path is None,
            'get_downgrading_suggestions': False,
            'should_pay_get_out_of_jail_fine': jail_fine_model_path is None
        }
    )

    print(dqn_agent.active_training_method)
    print(dqn_agent.can_use_defaults_methods)
    print(dqn_agent.dqn_methods)
    print(dqn_agent.q_networks)

    # Create save directory
    os.makedirs(save_path, exist_ok=True)
    
    for i in tqdm(range(pretraining_iterations), desc="Training iterations"):
        # Step 1: Collect experiences from other agents
        experiences = collect_downgrading_experiences(
            num_games=pretraining_iteration_games,
            use_multiprocessing=True
        )
        
        # Prepare experiences for training
        training_data = prepare_downgrading_experiences_for_training(experiences)
        
        # Step 2: Pretrain on collected experiences
        if training_data:
            print(f"Pretraining on {len(training_data)} experiences")
            pretrain_stats = pretrain_dqn_for_downgrading(
                dqn_agent,
                training_data,
                batch_size=batch_size,
                epochs=pretraining_iteration_epochs
            )
            
            # Save pretrained model
            pretrain_model_path = os.path.join(save_path, f"dqn_downgrading_pretrained_{i+1}")
            dqn_agent.save_model_for_method('get_downgrading_suggestions', pretrain_model_path)
            print(f"Pretrained model saved to {pretrain_model_path}")
            
            # Plot pretraining stats
            plot_training_stats(pretrain_stats, filename=os.path.join(save_path, f"pretrain_stats_{i+1}.png"))
        else:
            print("No pretraining data available, skipping pretraining")
        
        # Clean up memory
        del experiences
        gc.collect()

        # Step 3: Evaluate pretrained agent
        print("Evaluating pretrained agent")
        pretrain_eval_stats = play_evaluation_games(dqn_agent, num_games=evaluation_games)
        
    gc.collect()

    # Step 4: Train through gameplay    
    print("Starting training through gameplay")
    gameplay_stats = train_dqn_downgrading_through_gameplay(
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
    baseline_num_games = 700_000 # updates for 8 processes 5k training games
    baseline_num_processes = 8
    baseline_training_games = 5_500

    num_processes = 8
    training_games = 3_000
    num_games = int(training_games * baseline_num_games / baseline_training_games * num_processes / baseline_num_processes)

    epsilon_config = EpsilonConfig(
        start=1.0,
        end=0.1,
        decay=0.998,
        num_games=num_games,
        stop_exploration_after=0.7
    )

    print(f"Update frequency for epsilon: {calculate_epsilon_update_freq(epsilon_config)}")

    # Run the training pipeline with other methods using previously trained models
    agent, gameplay_stats = run_downgrading_training_pipeline(
        pretraining_iteration_games=5_000,  # Start with a reasonable number of games
        pretraining_iteration_epochs=1,
        pretraining_iterations=5,
        training_games=training_games,
        evaluation_games=0,
        max_turns=500,
        batch_size=64,
        save_path='saved_models/dqn/downgrade/v2/',
        property_buy_model_path='saved_models/dqn/should_buy/v6/dqn_agent_final',  # Use trained buy property model
        upgrading_model_path='saved_models/dqn/upgrading/v5/dqn_upgrading_final',  # Use trained upgrading model
        jail_fine_model_path='saved_models/dqn/jail_fine/v2/dqn_agent_final',  # Use parent class for jail fine method
        epsilon_config=epsilon_config,
    )
    
    print("Training complete!")