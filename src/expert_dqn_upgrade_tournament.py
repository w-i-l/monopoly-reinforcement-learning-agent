import os
import argparse
import json
import time
from datetime import datetime
import random
from collections import deque

# Import your existing code
from agents.dqn_agent import DQNAgent
from agents.random_agent import RandomAgent
from agents.algorithmic_agent import AlgorithmicAgent
from agents.strategic_agent import (
    StrategicAgent,
    AggressiveInvestor,
    CautiousAccumulator,
    CompletionistBuilder,
    UtilityKing,
    OrangeRedSpecialist,
    LateGameDeveloper,
    Trademaster,
    BalancedAgent,
    DynamicAdapter
)
from managers.tournament_manager import TournamentManager
from game.game_validation import GameValidation
from game.game_state import GameState
from models.property_group import PropertyGroup
from models.property import Property

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings

def modify_dqn_for_compatibility():
    """
    FIXED VERSION: Modify DQN agent to prevent multiple initializations and make it compatible with TournamentManager.
    """
    # Store the original __init__ method
    original_init = DQNAgent.__init__
    
    # Define a new __init__ method that caches networks
    def new_init(self, name, **kwargs):
        # Call the original __init__ but suppress multiple 'initialized' messages
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
            
            # CRITICAL FIX: Store the configuration properly
            DQNAgent._dqn_methods = self.dqn_methods.copy()
            DQNAgent._can_use_defaults_methods = self.can_use_defaults_methods.copy()
            
            # Cache networks
            for method in self.q_networks:
                setattr(DQNAgent, f'_shared_q_network_{method}', self.q_networks[method])
                setattr(DQNAgent, f'_shared_target_network_{method}', self.target_networks[method])
                setattr(DQNAgent, f'_shared_optimizer_{method}', self.optimizers[method])
            
            print(f"DQN Agent '{name}' initialized (networks will be reused)")
        else:
            # Skip redundant initialization
            # Call StrategicAgent's __init__ directly
            StrategicAgent.__init__(self, name, kwargs.get('strategy_params'))
            
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
                'get_downgrading_suggestions': 8,
                'should_pay_get_out_of_jail_fine': 2,
                'should_use_escape_jail_card': 2,
                "get_mortgaging_suggestions": 40,
                'get_unmortgaging_suggestions': 40
            })
            
            # CRITICAL FIX: Use stored configuration instead of parameters
            self.dqn_methods = getattr(DQNAgent, '_dqn_methods', {}).copy()
            self.can_use_defaults_methods = getattr(DQNAgent, '_can_use_defaults_methods', {}).copy()
            
            # Override with any explicitly passed parameters
            if 'dqn_methods' in kwargs:
                self.dqn_methods.update(kwargs['dqn_methods'])
            if 'can_use_defaults_methods' in kwargs:
                self.can_use_defaults_methods.update(kwargs['can_use_defaults_methods'])
            
            self.active_training_method = None  # Not training
            
            # Initialize network dictionaries
            self.q_networks = {}
            self.target_networks = {}
            self.optimizers = {}

            self.epsilon_counter = {
                'buy_property': 0,
                'get_upgrading_suggestions': 0,
                'get_downgrading_suggestions': 0,
                'should_pay_get_out_of_jail_fine': 0,
                'should_use_escape_jail_card': 0,
                'get_mortgaging_suggestions': 0,
                'get_unmortgaging_suggestions': 0
            }
            
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
                'get_downgrading_suggestions': deque(maxlen=10000),
                'should_pay_get_out_of_jail_fine': deque(maxlen=10000),
                'should_use_escape_jail_card': deque(maxlen=10000),
                'get_mortgaging_suggestions': deque(maxlen=10000),
                'get_unmortgaging_suggestions': deque(maxlen=10000) 
            }
            
            # For tracking decisions during a game
            self.current_decisions = {
                'buy_property': None,
                'get_upgrading_suggestions': None,
                'get_downgrading_suggestions': None,
                'should_pay_get_out_of_jail_fine': None,
                'should_use_escape_jail_card': None,
                'get_mortgaging_suggestions': None,
                'get_unmortgaging_suggestions': None
            }

            self.game_state = None

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

def create_tournament_dqn_agent(original_agent, name_suffix=""):
    """
    Create a clean DQN agent instance for tournament use.
    
    Args:
        original_agent: The original trained DQN agent
        name_suffix: Suffix to add to the agent name
        
    Returns:
        Clean DQN agent ready for tournament
    """
    # Create new instance with same configuration
    tournament_agent = DQNAgent(
        name=f"{original_agent.name}{name_suffix}",
        state_dim=original_agent.state_dim,
        hidden_dims=original_agent.hidden_dims,
        learning_rate=original_agent.learning_rate,
        gamma=original_agent.gamma,
        epsilon_start=0.05,  # Low epsilon for evaluation
        epsilon_end=original_agent.epsilon_end,
        epsilon_decay=original_agent.epsilon_decay,
        epsilon_update_freq=original_agent.epsilon_update_freq,
        target_update_freq=original_agent.target_update_freq,
        memory_size=1000,  # Smaller memory for tournament
        batch_size=original_agent.batch_size,
        training=False,  # Evaluation mode
        dqn_methods=original_agent.dqn_methods.copy(),
        active_training_method=None,
        can_use_defaults_methods=original_agent.can_use_defaults_methods.copy()
    )
    
    # Copy trained networks
    for method in original_agent.q_networks:
        if method in tournament_agent.q_networks:
            tournament_agent.q_networks[method].set_weights(
                original_agent.q_networks[method].get_weights()
            )
            tournament_agent.target_networks[method].set_weights(
                original_agent.target_networks[method].get_weights()
            )
    
    return tournament_agent

def determine_dqn_configuration(
    buy_model_path,
    upgrade_model_path, 
    downgrade_model_path,
    pay_fine_model_path,
    escape_jail_card_model_path,
    get_mortgaging_suggestions_model_path,
    get_unmortgaging_suggestions_model_path
):
    """
    Dynamically determine DQN configuration based on provided model paths.

    Args:
        buy_model_path: Path to buy property model (None if not using DQN)
        upgrade_model_path: Path to upgrading model (None if not using DQN)
        downgrade_model_path: Path to downgrading model (None if not using DQN)
        pay_fine_model_path: Path to jail fine model (None if not using DQN)
        
    Returns:
        Tuple of (dqn_methods, can_use_defaults_methods, active_methods)
    """
    # All available methods
    all_methods = [
        'buy_property',
        'get_upgrading_suggestions', 
        'get_downgrading_suggestions',
        'should_pay_get_out_of_jail_fine',
        'should_use_escape_jail_card',
        'get_mortgaging_suggestions',
        'get_unmortgaging_suggestions'
    ]
    
    # Map model paths to methods
    model_paths = {
        'buy_property': buy_model_path,
        'get_upgrading_suggestions': upgrade_model_path,
        'get_downgrading_suggestions': downgrade_model_path,
        'should_pay_get_out_of_jail_fine': pay_fine_model_path,
        'should_use_escape_jail_card': escape_jail_card_model_path,
        'get_mortgaging_suggestions': get_mortgaging_suggestions_model_path,
        'get_unmortgaging_suggestions': get_unmortgaging_suggestions_model_path
    }

    # Configure DQN methods and defaults based on model availability
    dqn_methods = {}
    can_use_defaults_methods = {}
    active_methods = []
    
    for method in all_methods:
        model_path = model_paths[method]
        if model_path is not None:
            # Use DQN for this method
            dqn_methods[method] = model_path
            can_use_defaults_methods[method] = False
            active_methods.append(method)
        else:
            # Use parent class method
            dqn_methods[method] = None
            can_use_defaults_methods[method] = True
    
    return dqn_methods, can_use_defaults_methods, active_methods

def run_dqn_tournament(
        buy_model_path: str, 
        upgrade_model_path: str,
        downgrade_model_path: str,
        pay_fine_model_path: str,
        escape_jail_card_model_path: str,
        get_mortgaging_suggestions_model_path: str,
        get_unmortgaging_suggestions_model_path: str,
        config):
    """
    Run a tournament including the DQN agent against other agent types.
    
    Args:
        buy_model_path: Path to the saved DQN agent model for property buying (None if not using)
        upgrade_model_path: Path to the saved DQN agent model for upgrading suggestions (None if not using)
        downgrade_model_path: Path to the saved DQN agent model for downgrading suggestions (None if not using)
        pay_fine_model_path: Path to the saved DQN agent model for jail fine decisions (None if not using)
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
    
    # Determine DQN configuration dynamically
    dqn_methods, can_use_defaults_methods, active_methods = determine_dqn_configuration(
        buy_model_path, 
        upgrade_model_path, 
        downgrade_model_path, 
        pay_fine_model_path, 
        escape_jail_card_model_path,
        get_mortgaging_suggestions_model_path,
        get_unmortgaging_suggestions_model_path
    )
    
    # Check if at least one DQN method is being used
    if not active_methods:
        print("Error: No valid model paths provided. At least one DQN method must be specified.")
        return None, None
    
    print(f"DQN methods configuration:")
    for method, path in dqn_methods.items():
        status = "DQN" if path is not None else "Parent Class"
        print(f"  {method}: {status}")
    
    # Initialize DQN agent
    dqn_agent = DQNAgent(
        "DQN_Player",
        training=False,  # Set to evaluation mode
        dqn_methods=dqn_methods,
        can_use_defaults_methods=can_use_defaults_methods
    )
    dqn_agent.epsilon = 0.05  # Low epsilon for evaluation

    tournament_dqn_agent = create_tournament_dqn_agent(dqn_agent)
    tournament_dqn_agent.can_be_referenced = False  # Force new instances
    
    # Load models explicitly to ensure they're available
    for method, model_path in dqn_methods.items():
        if model_path is not None:
            print(f"\n\nLoading model for {method} method...")
            dqn_agent.load_model_for_method(method, model_path)
    
    # Debug - check if the methods are in q_networks after loading
    print(f"\nDQN agent active methods: {active_methods}")
    print(f"Available methods in q_networks: {list(dqn_agent.q_networks.keys())}\n")
    
    # Create all player types
    players = [
        tournament_dqn_agent,
        RandomAgent("Random_Player"),
        AlgorithmicAgent("Algorithmic_Player"),
        StrategicAgent("Strategic_Player"),
        AggressiveInvestor("Aggressive_Player"),
        CautiousAccumulator("Cautious_Player"),
        CompletionistBuilder("Completionist_Player"),
        UtilityKing("Utility_Player"),
        OrangeRedSpecialist("OrangeRed_Player"),
        LateGameDeveloper("LateGame_Player"),
        Trademaster("Trademaster_Player"),
        BalancedAgent("Balanced_Player"),
        DynamicAdapter("Dynamic_Player")
    ]
    
    # Identify TensorFlow-based players that cannot be pickled
    # These will be excluded from parallel processing and handled sequentially
    excluded_parallel_players = [tournament_dqn_agent]
    
    # Create tournament manager
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tournament_dir = os.path.join(output_dir, f"tournament_{timestamp}")
    tournament_manager = TournamentManager(output_dir=tournament_dir)
    
    print(f"\nStarting tournament with {len(players)} players...")
    print(f"Players: {[player.name for player in players]}\n")
    
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
        'model_paths': {
            'buy_property': buy_model_path,
            'upgrading': upgrade_model_path,
            'downgrading': downgrade_model_path,
            'jail_fine': pay_fine_model_path,
            'escape_jail_card': escape_jail_card_model_path,
            'get_mortgaging_suggestions': get_mortgaging_suggestions_model_path,
            'get_unmortgaging_suggestions': get_unmortgaging_suggestions_model_path
        },
        'dqn_configuration': {
            method: 'DQN' if dqn_methods[method] is not None else 'Parent'
            for method in dqn_methods.keys()
        },
        'active_dqn_methods': active_methods,
        'two_player': two_player,
        'games_per_matchup': games_per_matchup if two_player else None,
        'num_games': num_games if not two_player else None,
        'max_turns': max_turns,
        'elapsed_time': elapsed_time,
        'dqn_ranking': None,
        'dqn_stats': None,
        'matchup_results': {}
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
        print(f"\nDQN Agent Performance:")
        print(f"Ranking: {dqn_results['dqn_ranking']['position']} out of {dqn_results['dqn_ranking']['total_players']}")
        print(f"Win Rate: {dqn_results['dqn_ranking']['win_rate']:.4f}")
        print(f"Draw Rate: {dqn_results['dqn_ranking']['draw_rate']:.4f}")
        print(f"Survival Rate: {dqn_results['dqn_ranking']['survival_rate']:.4f}")
        print(f"Average Net Worth: {dqn_results['dqn_ranking']['avg_net_worth']:.2f}₩")
        
        # Print DQN configuration
        print("\nDQN Configuration:")
        for method, mode in dqn_results['dqn_configuration'].items():
            print(f"  {method}: {mode}")
    
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
    
    # Model paths - all optional, dynamically configured
    parser.add_argument('--buy-model-path', type=str, default=None,
                       help='Path to saved model for buy property decision (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--upgrade-model-path', type=str, default=None,
                       help='Path to saved model for upgrading suggestions (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--downgrade-model-path', type=str, default=None,
                       help='Path to saved model for downgrading suggestions (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--pay-fine-model-path', type=str, default=None,
                       help='Path to saved model for paying get out of jail fine decision (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--escape-jail-card-model-path', type=str, default=None,
                          help='Path to saved model for using escape jail card decision (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--get-mortgaging-suggestions-model-path', type=str, default=None,
                            help='Path to saved model for getting mortgaging suggestions (without suffixes). If not provided, uses parent class method.')
    parser.add_argument('--get-unmortgaging-suggestions-model-path', type=str, default=None,
                            help='Path to saved model for getting unmortgaging suggestions (without suffixes). If not provided, uses parent class method.')
    
    # Tournament type
    parser.add_argument('--two-player', action='store_true', default=True,
                       help='Run a 2-player round-robin tournament (default)')
    parser.add_argument('--standard', action='store_true',
                       help='Run a standard tournament with all players in each game')
    
    # Tournament parameters
    parser.add_argument('--games-per-matchup', type=int, default=100,
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
    parser.add_argument('--output-dir', type=str, default='tournament_results',
                       help='Directory to save tournament results')
    
    args = parser.parse_args()
    
    # Apply DQN compatibility modifications
    modify_dqn_for_compatibility()
    
    # Check if at least one model path is provided
    model_paths = [
        args.buy_model_path, 
        args.upgrade_model_path, 
        args.downgrade_model_path, 
        args.pay_fine_model_path, 
        args.escape_jail_card_model_path,
        args.get_mortgaging_suggestions_model_path, 
        args.get_unmortgaging_suggestions_model_path
    ]
    if not any(path is not None for path in model_paths):
        print("Error: At least one model path must be provided.")
        print("Available options: --buy-model-path, --upgrade-model-path, --downgrade-model-path, --pay-fine-model-path")
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
    
    # Print model configuration
    print("\nModel configuration:")
    print(f"  Buy property model: {args.buy_model_path if args.buy_model_path else 'Parent class method'}")
    print(f"  Upgrading model: {args.upgrade_model_path if args.upgrade_model_path else 'Parent class method'}")
    print(f"  Downgrading model: {args.downgrade_model_path if args.downgrade_model_path else 'Parent class method'}")
    print(f"  Pay fine model: {args.pay_fine_model_path if args.pay_fine_model_path else 'Parent class method'}")
    print(f"  Escape jail card model: {args.escape_jail_card_model_path if args.escape_jail_card_model_path else 'Parent class method'}")
    print(f"  Get mortgaging suggestions model: {args.get_mortgaging_suggestions_model_path if args.get_mortgaging_suggestions_model_path else 'Parent class method'}")
    print(f"  Get unmortgaging suggestions model: {args.get_unmortgaging_suggestions_model_path if args.get_unmortgaging_suggestions_model_path else 'Parent class method'}")
    
    # Start tournament
    print("\nStarting tournament with DQN agent...")
    try:
        results, dqn_results = run_dqn_tournament(
            buy_model_path=args.buy_model_path,
            upgrade_model_path=args.upgrade_model_path,
            downgrade_model_path=args.downgrade_model_path,
            pay_fine_model_path=args.pay_fine_model_path,
            escape_jail_card_model_path=args.escape_jail_card_model_path,
            get_mortgaging_suggestions_model_path=args.get_mortgaging_suggestions_model_path,
            get_unmortgaging_suggestions_model_path=args.get_unmortgaging_suggestions_model_path,
            config=config
        )
        
        if results is not None:
            print("\nTournament completed successfully!")
        else:
            print("Tournament failed to run.")
            
    except KeyboardInterrupt:
        print("Tournament interrupted by user.")
    except Exception as e:
        print(f"Error during tournament: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()