import os
import argparse
import json
import time
from datetime import datetime
import random  # Make sure to import random properly

# Import your existing code
from agents.expert_dqn_agent import DQNAgent
from agents.random_agent import RandomAgent
from agents.strategic_agent import StrategicAgent
from agents.default_strategic_player import (
    DefaultStrategicPlayer,
    AggressiveInvestor,
    CautiousAccumulator,
    CompletionistBuilder,
    UtilityKing,
    OrangeRedSpecialist,
    LateGameDeveloper,
    Trademaster,
    BalancedPlayer,
    DynamicAdapter
)
from managers.tournament_manager import TournamentManager
from game.game_validation import GameValidation
from game.game_state import GameState

# Add ControllDQNAgent for comparison
class ControllDQNAgent(DefaultStrategicPlayer):
    '''
    DQN comparing agent for tournament, having all methods of DQNAgent
    but one is set to random for the sake of comparison.
    '''

    def __init__(self, name, random_method='should_pay_get_out_of_jail_fine'):
        super().__init__(name)
        self.random_method = random_method

    def should_buy_property(self, game_state, property_tile):
        if self.random_method == 'should_buy_property':
            if error := GameValidation.validate_buy_property(game_state, self, property_tile):
                return False
            return random.choice([True, False])
        return super().should_buy_property(game_state, property_tile)
    
    def should_pay_get_out_of_jail_fine(self, game_state):
        if self.random_method == 'should_pay_get_out_of_jail_fine':
            if not game_state.in_jail.get(self, False):
                return False
            jail_fine = game_state.board.get_jail_fine()
            can_afford = game_state.player_balances[self] >= jail_fine
            return random.choice([True, False]) and can_afford
        return super().should_pay_get_out_of_jail_fine(game_state)

from collections import deque
import random

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

def modify_dqn_for_compatibility():
    """
    Modify DQN agent to prevent multiple initializations and make it compatible with TournamentManager.
    """
    # Store the original __init__ method
    original_init = DQNAgent.__init__
    
    # Define a new __init__ method that caches networks
    def new_init(self, name, **kwargs):
        # Call the original __init__ but suppress multiple 'initialized' messages

         # Configure DQN methods
        buy_property_path = kwargs.get('buy_property_path')
        upgrading_model_path = kwargs.get('upgrading_model_path')
        jail_fine_path = kwargs.get('jail_fine_path')

        if not hasattr(DQNAgent, '_initialized_once'):
            original_init(self, name, **kwargs)
            DQNAgent._initialized_once = True
            
            # Store shared parameters at class level
            DQNAgent._state_dim = self.state_dim
            DQNAgent._hidden_dims = self.hidden_dims
            DQNAgent._learning_rate = self.learning_rate
            DQNAgent._gamma = self.gamma
            DQNAgent._epsilon_end = self.epsilon_end
            DQNAgent._epsilon_decay = self.epsilon_decay
            DQNAgent._target_update_freq = self.target_update_freq
            DQNAgent._batch_size = self.batch_size
            DQNAgent._action_dims = self.action_dims
            
            # Cache networks
            for method in self.q_networks:
                setattr(DQNAgent, f'_shared_q_network_{method}', self.q_networks[method])
                setattr(DQNAgent, f'_shared_target_network_{method}', self.target_networks[method])
                setattr(DQNAgent, f'_shared_optimizer_{method}', self.optimizers[method])
            
            print(f"DQN Agent '{name}' initialized (networks will be reused)")
        else:
            # Skip redundant initialization
            # Call DefaultStrategicPlayer's __init__ directly
            DefaultStrategicPlayer.__init__(self, name, kwargs.get('strategy_params'))
            
            # Copy parameters from class attributes
            self.state_dim = getattr(DQNAgent, '_state_dim', 100)
            self.hidden_dims = getattr(DQNAgent, '_hidden_dims', [128, 64, 32])
            self.learning_rate = getattr(DQNAgent, '_learning_rate', 0.001)
            self.gamma = getattr(DQNAgent, '_gamma', 0.99)
            self.epsilon = kwargs.get('epsilon', 0.05)  # Use low epsilon for evaluation
            self.epsilon_end = getattr(DQNAgent, '_epsilon_end', 0.1)
            self.epsilon_decay = getattr(DQNAgent, '_epsilon_decay', 0.995)
            self.target_update_freq = getattr(DQNAgent, '_target_update_freq', 10)
            self.batch_size = getattr(DQNAgent, '_batch_size', 64)
            self.training = kwargs.get('training', False)
            self.update_counter = 0
            self.action_dims = getattr(DQNAgent, '_action_dims', {
                'buy_property': 2, 
                'get_upgrading_suggestions': 8,
                'should_pay_get_out_of_jail_fine': 2
            })
            
            self.dqn_methods = {
                'buy_property': buy_property_path,
                'get_upgrading_suggestions': upgrading_model_path,
                'should_pay_get_out_of_jail_fine': jail_fine_path
            }
            self.active_training_method = None  # Not training
            
            # Initialize network dictionaries
            self.q_networks = {}
            self.target_networks = {}
            self.optimizers = {}
            
            # Use class-level cached networks if available
            for method in self.dqn_methods:
                if self.dqn_methods[method] is not None or method == self.active_training_method:
                    q_net_attr = f'_shared_q_network_{method}'
                    target_net_attr = f'_shared_target_network_{method}'
                    opt_attr = f'_shared_optimizer_{method}'
                    
                    if hasattr(DQNAgent, q_net_attr) and hasattr(DQNAgent, target_net_attr):
                        self.q_networks[method] = getattr(DQNAgent, q_net_attr)
                        self.target_networks[method] = getattr(DQNAgent, target_net_attr)
                        self.optimizers[method] = getattr(DQNAgent, opt_attr)
            
            # Basic memory setup
            self.memory = {
                'buy_property': deque(maxlen=10000),
                'get_upgrading_suggestions': deque(maxlen=10000),
                'should_pay_get_out_of_jail_fine': deque(maxlen=10000)
            }
            
            # For tracking decisions during a game
            self.current_decisions = {
                'buy_property': None,
                'get_upgrading_suggestions': None,
                'should_pay_get_out_of_jail_fine': None
            }
            
            self.game_state = None

        # Set up can_use_defaults_methods based on provided paths
        self.can_use_defaults_methods = {
            'buy_property': buy_property_path is None,
            'get_upgrading_suggestions': upgrading_model_path is None,
            'should_pay_get_out_of_jail_fine': jail_fine_path is None
        }
    
    # Replace the __init__ method
    DQNAgent.__init__ = new_init
    
    # Add set_train_mode method for compatibility with the tournament script
    if not hasattr(DQNAgent, 'set_train_mode'):
        def set_train_mode(self, training):
            self.training = training
            # Set low epsilon for evaluation mode
            if not training:
                self.epsilon = 0.05
        DQNAgent.set_train_mode = set_train_mode

def run_dqn_tournament(model_paths, config):
    """
    Run a tournament including the DQN agent against other agent types.
    
    Args:
        model_paths: Dictionary containing paths to saved DQN agent models
        config: Configuration dictionary
        
    Returns:
        Tournament results dictionary
    """
    # Extract parameters from config
    output_dir = config['output_dir']
    two_player = config.get('two_player', True)
    games_per_matchup = config.get('games_per_matchup', 50)
    num_games = config.get('num_games', 100)
    max_turns = config.get('max_turns', 1000)
    parallel = config.get('parallel', False)
    num_workers = config.get('num_workers', None)
    
    # Initialize DQN agent
    dqn_methods = {
        'buy_property': model_paths.get('buy_property'),
        'get_upgrading_suggestions': model_paths.get('upgrading'),
        'should_pay_get_out_of_jail_fine': model_paths.get('jail_fine')
    }
    
    dqn_agent = DQNAgent(
        "DQN_Player",
        training=False,  # Set to evaluation mode
        dqn_methods=dqn_methods,  # Pass the methods configuration directly
    )
    dqn_agent.epsilon = 0.05  # Low epsilon for evaluation
    
    # Load models explicitly and ensure q_networks contains the methods
    for method, path in model_paths.items():
        if path is not None:
            method_name = {
                'buy_property': 'buy_property',
                'upgrading': 'get_upgrading_suggestions',
                'jail_fine': 'should_pay_get_out_of_jail_fine'
            }.get(method, method)
            
            print(f"Loading model for {method_name} method from {path}...")
            dqn_agent.load_model_for_method(method_name, path)
    
    # Debug - check if the methods are in q_networks after loading
    print(f"Available methods in q_networks: {list(dqn_agent.q_networks.keys())}")
    for method, path in model_paths.items():
        if path is not None:
            method_name = {
                'buy_property': 'buy_property',
                'upgrading': 'get_upgrading_suggestions',
                'jail_fine': 'should_pay_get_out_of_jail_fine'
            }.get(method, method)
            print(f"Is {method_name} loaded: {'Yes' if method_name in dqn_agent.q_networks else 'No'}")
    
    # Ensure the methods are properly added to q_networks
    for method, path in model_paths.items():
        if path is not None:
            method_name = {
                'buy_property': 'buy_property',
                'upgrading': 'get_upgrading_suggestions',
                'jail_fine': 'should_pay_get_out_of_jail_fine'
            }.get(method, method)
            
            if method_name not in dqn_agent.q_networks:
                print(f"Warning: {method_name} not in q_networks after loading. Adding it now...")
                # Rebuild the network and load weights if needed
                dqn_agent._init_networks()
        
    # Another check after initialization
    print(f"After initialization, q_networks contains: {list(dqn_agent.q_networks.keys())}")
    
    # Initialize control DQN agents for comparison
    control_agents = []
    
    # Create control agents for each method that has a model
    for method, path in model_paths.items():
        if path is not None:
            method_name = {
                'buy_property': 'should_buy_property',
                'upgrading': 'get_upgrading_suggestions',
                'jail_fine': 'should_pay_get_out_of_jail_fine'
            }.get(method, method)
            
            control_agent = ControllDQNAgent(f"Control_{method.title()}_Player", random_method=method_name)
            control_agents.append(control_agent)
    
    # Create all player types
    players = [
        dqn_agent,
        *control_agents,
        RandomAgent("Random_Player"),
        StrategicAgent("Strategic_Player"),
        DefaultStrategicPlayer("DefaultStrategic_Player"),
        AggressiveInvestor("Aggressive_Player"),
        CautiousAccumulator("Cautious_Player"),
        CompletionistBuilder("Completionist_Player"),
        UtilityKing("Utility_Player"),
        OrangeRedSpecialist("OrangeRed_Player"),
        LateGameDeveloper("LateGame_Player"),
        Trademaster("Trademaster_Player"),
        BalancedPlayer("Balanced_Player"),
        DynamicAdapter("Dynamic_Player")
    ]
    
    # Identify TensorFlow-based players that cannot be pickled
    # These will be excluded from parallel processing and handled sequentially
    excluded_parallel_players = [dqn_agent]
    
    # Create tournament manager
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tournament_dir = os.path.join(output_dir, f"tournament_{timestamp}")
    tournament_manager = TournamentManager(output_dir=tournament_dir)
    
    print(f"Starting tournament with {len(players)} players...")
    print(f"Players: {[player.name for player in players]}")
    
    # Run tournament
    start_time = time.time()
    
    if two_player:
        print(f"Running 2-player round-robin tournament with {games_per_matchup} games per matchup...")
        
        # We're using the excluded_parallel_players parameter
        if parallel:
            print(f"Running in hybrid mode: {len(excluded_parallel_players)} players will be processed sequentially, others in parallel")
        
        results = tournament_manager.run_2player_tournament(
            players=players,
            games_per_matchup=games_per_matchup,
            max_turns=max_turns,
            parallel=True,
            num_workers=num_workers,
            collect_turn_data=False,  # Disable to speed up simulation
            save_event_log=False,     # Disable to save space
            excluded_parallel_players=excluded_parallel_players  # Using our parameter
        )
    else:
        print(f"Running standard tournament with {num_games} games...")
        results = tournament_manager.run_tournament(
            players=players,
            num_games=num_games,
            max_turns=max_turns,
            parallel=parallel,
            num_workers=num_workers,
            collect_turn_data=False,
            save_event_log=False,
            excluded_parallel_players=excluded_parallel_players  # Using our parameter
        )
    
    elapsed_time = time.time() - start_time
    
    # Save DQN-specific results separately
    dqn_results = {
        'timestamp': timestamp,
        'model_paths': model_paths,
        'two_player': two_player,
        'games_per_matchup': games_per_matchup if two_player else None,
        'num_games': num_games if not two_player else None,
        'max_turns': max_turns,
        'elapsed_time': elapsed_time,
        'dqn_ranking': None,
        'dqn_stats': None,
        'matchup_results': {},
        'control_comparisons': {}
    }
    
    # Extract DQN ranking and stats
    for i, ranking in enumerate(results["overall_stats"]["player_rankings"]):
        if ranking["player"] == "DQN_Player":
            dqn_results['dqn_ranking'] = {
                'position': i + 1,
                'total_players': len(players),
                'win_rate': ranking["win_rate"],
                'draw_rate': ranking["draw_rate"],
                'avg_net_worth': ranking["avg_net_worth"],
                'survival_rate': ranking["survival_rate"]
            }
            dqn_results['dqn_stats'] = ranking
    
    # Extract control agent comparisons
    for ranking in results["overall_stats"]["player_rankings"]:
        if ranking["player"].startswith("Control_"):
            control_type = ranking["player"].replace("Control_", "").replace("_Player", "").lower()
            dqn_results['control_comparisons'][control_type] = {
                'win_rate': ranking["win_rate"],
                'draw_rate': ranking["draw_rate"],
                'avg_net_worth': ranking["avg_net_worth"],
                'survival_rate': ranking["survival_rate"]
            }
    
    # Extract matchup results for DQN (if 2-player tournament)
    if two_player and 'matchup_stats' in results:
        for matchup_key, matchup_data in results['matchup_stats'].items():
            if "DQN_Player" in matchup_key:
                opponent = matchup_key.replace("DQN_Player_vs_", "").replace("_vs_DQN_Player", "")
                
                # Extract DQN-specific stats
                dqn_results['matchup_results'][opponent] = {
                    'games_played': matchup_data['games_played'],
                    'win_rate': matchup_data['by_player']["DQN_Player"]['win_rate'] 
                        if "DQN_Player" in matchup_data['by_player'] else 0,
                    'bankrupt_rate': matchup_data['by_player']["DQN_Player"]['bankrupt_rate'] 
                        if "DQN_Player" in matchup_data['by_player'] else 0,
                    'avg_net_worth': matchup_data['by_player']["DQN_Player"]['avg_net_worth'] 
                        if "DQN_Player" in matchup_data['by_player'] else 0,
                    'draws': matchup_data['draws']
                }
    
    # Save DQN results
    dqn_results_path = os.path.join(tournament_dir, "dqn_tournament_results.json")
    with open(dqn_results_path, 'w') as f:
        json.dump(dqn_results, f, indent=2)
    
    print(f"\nTournament completed in {elapsed_time:.1f} seconds!")
    print(f"Results saved to {tournament_dir}")
    
    # Print summary of DQN performance
    if dqn_results['dqn_ranking']:
        print(f"\nDQN Agent Ranking: {dqn_results['dqn_ranking']['position']} out of {dqn_results['dqn_ranking']['total_players']}")
        print(f"Win Rate: {dqn_results['dqn_ranking']['win_rate']:.4f}")
        print(f"Draw Rate: {dqn_results['dqn_ranking']['draw_rate']:.4f}")
        print(f"Survival Rate: {dqn_results['dqn_ranking']['survival_rate']:.4f}")
        print(f"Average Net Worth: ${dqn_results['dqn_ranking']['avg_net_worth']:.2f}")
    
    # Print control agent comparisons
    if dqn_results['control_comparisons']:
        print("\nControl Agent Comparisons:")
        for control_type, stats in dqn_results['control_comparisons'].items():
            print(f"  {control_type.title()} Control: {stats['win_rate']:.4f} win rate, ${stats['avg_net_worth']:.2f} avg net worth")
    
    # Print matchup results if available
    if dqn_results['matchup_results'] and two_player:
        print("\nMatchup Win Rates:")
        for opponent, stats in sorted(dqn_results['matchup_results'].items(), 
                                      key=lambda x: x[1]['win_rate'], 
                                      reverse=True):
            print(f"  vs {opponent}: {stats['win_rate']:.4f} win rate ({stats['games_played']} games)")
    
    return results, dqn_results

def main():
    """Main function to parse arguments and run tournament."""
    parser = argparse.ArgumentParser(description='Run tournament with DQN Agent for Monopoly')
    
    # Model paths
    parser.add_argument('--buy-property-model', type=str, default=None,
                       help='Path to saved model for buy property decision (without suffixes)')
    parser.add_argument('--upgrading-model', type=str, default=None,
                       help='Path to saved model for upgrading suggestions decision (without suffixes)')
    parser.add_argument('--jail-fine-model', type=str, default=None,
                       help='Path to saved model for jail fine decision (without suffixes)')
    
    # Tournament type
    parser.add_argument('--two-player', action='store_true', default=True,
                       help='Run a 2-player round-robin tournament (default)')
    parser.add_argument('--standard', action='store_true',
                       help='Run a standard tournament with all players in each game')
    
    # Tournament parameters
    parser.add_argument('--games-per-matchup', type=int, default=300,
                       help='Number of games per matchup in 2-player tournament')
    parser.add_argument('--num-games', type=int, default=300,
                       help='Number of games in standard tournament')
    parser.add_argument('--max-turns', type=int, default=1000,
                       help='Maximum turns per game')
    
    # Multiprocessing
    parser.add_argument('--sequential', action='store_true',
                       help='Run games sequentially (no parallelism)')
    parser.add_argument('--hybrid', action='store_true', default=True,
                       help='Run in hybrid mode - sequential for DQN agents, parallel for others (default)')
    parser.add_argument('--workers', type=int, default=None,
                       help='Number of parallel workers (defaults to CPU count - 1)')
    
    # Output directory
    parser.add_argument('--output-dir', type=str, default='tournament_results/dqn/pay_fine',
                       help='Directory to save tournament results')
    
    args = parser.parse_args()
    
    # Apply DQN compatibility modifications
    modify_dqn_for_compatibility()
    
    # Check if at least one model is provided
    model_paths = {
        'buy_property': args.buy_property_model,
        'upgrading': args.upgrading_model,
        'jail_fine': args.jail_fine_model
    }
    
    if not any(model_paths.values()):
        print("Error: At least one model path must be provided")
        parser.print_help()
        return
    
    # Determine tournament type (two_player is default)
    two_player = not args.standard
    
    # Determine parallelization mode
    parallel = False
    if args.hybrid and not args.sequential:
        parallel = True  # Use hybrid parallelization
    
    # Set up tournament configuration
    config = {
        'output_dir': args.output_dir,
        'two_player': two_player,
        'games_per_matchup': args.games_per_matchup,
        'num_games': args.num_games,
        'max_turns': args.max_turns,
        'parallel': parallel,
        'num_workers': args.workers
    }
    
    # Print configuration
    print("Tournament configuration:")
    print(f"  Tournament type: {'2-player round-robin' if two_player else 'Standard'}")
    if two_player:
        print(f"  Games per matchup: {config['games_per_matchup']}")
    else:
        print(f"  Number of games: {config['num_games']}")
    print(f"  Maximum turns per game: {config['max_turns']}")
    print(f"  Execution mode: {'Hybrid parallel' if parallel else 'Sequential'}")
    
    # Print model configurations
    print("Model configurations:")
    for method, path in model_paths.items():
        if path:
            print(f"  {method.replace('_', ' ').title()} model: {path}")
        else:
            print(f"  {method.replace('_', ' ').title()} model: Using default strategy")
    
    # Start tournament
    print(f"Starting tournament with DQN agent...")
    try:
        run_dqn_tournament(model_paths, config)
        print("\nTournament completed successfully!")
    except KeyboardInterrupt:
        print("Tournament interrupted by user.")
    except Exception as e:
        print(f"Error during tournament: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 