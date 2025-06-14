import os
import sys
import argparse
from typing import List, Dict, Any

# Import player types
from agents.strategic_agent import StrategicAgent
from agents.default_strategic_player import (
    AggressiveInvestor,
    CautiousAccumulator,
    CompletionistBuilder,
    UtilityKing,
    OrangeRedSpecialist,
    LateGameDeveloper,
    Trademaster,
    BalancedPlayer,
    DynamicAdapter,
    DefaultStrategicPlayer
)
from agents.random_agent import RandomAgent
from managers.tournament_manager import TournamentManager
from game.player import Player

def run_player_comparison(args):
    """Run a tournament comparing different player types."""
    # Create specified player types
    players = []
    
    # Create players based on type names
    player_types = {
        "aggressive": AggressiveInvestor,
        "cautious": CautiousAccumulator,
        "completionist": CompletionistBuilder,
        "utility": UtilityKing,
        "orange_red": OrangeRedSpecialist,
        "late_game": LateGameDeveloper,
        "trademaster": Trademaster,
        "balanced": BalancedPlayer,
        "dynamic": DynamicAdapter,
        "strategic": StrategicAgent,  # Default strategic with standard params
        "random": RandomAgent,
        "default_strategic": DefaultStrategicPlayer
    }
    
    for i, player_type in enumerate(args.player_types):
        if player_type in player_types:
            player_class = player_types[player_type]
            players.append(player_class(f"{player_type.capitalize()}_Player"))
        else:
            print(f"Warning: Unknown player type '{player_type}'. Using default StrategicAgent.")
            players.append(StrategicAgent(f"Strategic_Player_{i}"))
    
    # Create tournament manager
    tournament_manager = TournamentManager(output_dir=args.output_dir)
    
    # Run tournament
    if args.two_player:
        # Run 2-player round-robin tournament
        results = tournament_manager.run_2player_tournament(
            players=players,
            games_per_matchup=args.games_per_matchup,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    else:
        # Run regular tournament
        results = tournament_manager.run_tournament(
            players=players,
            num_games=args.num_games,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    
    # Print summary
    print("\n=== Tournament Summary ===")
    print(f"Players: {[p.name for p in players]}")
    
    if args.two_player:
        print(f"Tournament type: 2-player round-robin")
        print(f"Games per matchup: {args.games_per_matchup}")
        total_games = len(results["games"])
        print(f"Total games played: {total_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / total_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / total_games:.2%})")
    else:
        print(f"Games played: {args.num_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / args.num_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / args.num_games:.2%})")

    print("\nOverall Rankings:")
    
    for i, ranking in enumerate(results["overall_stats"]["player_rankings"]):
        print(f"{i+1}. {ranking['player']} - Win Rate: {ranking['win_rate']:.2%}, " +
              f"Draw Rate: {ranking['draw_rate']:.2%}, " +
              f"Net Worth: {int(ranking['avg_net_worth'])}₩, " +
              f"Survival Rate: {ranking['survival_rate']:.2%}")
    
    print("\nCheck the output directory for detailed results and visualizations.")

def run_custom_parameter_experiment(args):
    """Run a tournament with custom parameter variations of strategic agent."""
    # Create players with custom parameters
    players = []
    
    # Example custom parameter variations
    param_variations = [
        {
            "name": "High_Risk",
            "params": {
                "risk_tolerance": 0.9,
                "min_cash_reserve": 100,
                "property_value_multiplier": 1.0
            }
        },
        {
            "name": "Low_Risk",
            "params": {
                "risk_tolerance": 0.3,
                "min_cash_reserve": 300,
                "property_value_multiplier": 1.4
            }
        },
        {
            "name": "Development_Focus",
            "params": {
                "min_cash_for_houses": 250,
                "house_build_threshold": 0.25,
                "hotel_roi_threshold": 1.2
            }
        },
        {
            "name": "Acquisition_Focus",
            "params": {
                "property_value_multiplier": 1.1,
                "complete_set_bonus": 0.6,
                "min_cash_reserve": 150
            }
        },
        {
            "name": "Trading_Focus",
            "params": {
                "trade_eagerness": 0.9,
                "trade_profit_threshold": 1.0,
                "trade_monopoly_bonus": 500
            }
        }
    ]
    
    # Create players with custom parameters
    for variation in param_variations:
        players.append(DefaultStrategicPlayer(variation["name"], variation["params"]))
    
    # Create tournament manager
    tournament_manager = TournamentManager(output_dir=args.output_dir)
    
    # Run tournament
    if args.two_player:
        # Run 2-player round-robin tournament
        results = tournament_manager.run_2player_tournament(
            players=players,
            games_per_matchup=args.games_per_matchup,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    else:
        # Run regular tournament
        results = tournament_manager.run_tournament(
            players=players,
            num_games=args.num_games,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    
    # Print summary
    print("\n=== Parameter Experiment Summary ===")
    print(f"Players: {[p.name for p in players]}")
    
    if args.two_player:
        print(f"Tournament type: 2-player round-robin")
        print(f"Games per matchup: {args.games_per_matchup}")
        total_games = len(results["games"])
        print(f"Total games played: {total_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / total_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / total_games:.2%})")
    else:
        print(f"Games played: {args.num_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / args.num_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / args.num_games:.2%})")
    
    print("\nOverall Rankings:")
    
    for i, ranking in enumerate(results["overall_stats"]["player_rankings"]):
        print(f"{i+1}. {ranking['player']} - Win Rate: {ranking['win_rate']:.2%}, " +
              f"Draw Rate: {ranking['draw_rate']:.2%}, " +
              f"Net Worth: {int(ranking['avg_net_worth'])}₩, " +
              f"Survival Rate: {ranking['survival_rate']:.2%}")
    
    print("\nCheck the output directory for detailed results and visualizations.")

def run_versus_random_benchmark(args):
    """Run a tournament comparing strategic agents against random agents."""
    from agents.random_agent import RandomAgent
    
    # Create strategic players (one of each type)
    strategic_players = [
        AggressiveInvestor("Aggressive_Player"),
        CautiousAccumulator("Cautious_Player"),
        CompletionistBuilder("Completionist_Player"),
        UtilityKing("Utility_Player"),
        BalancedPlayer("Balanced_Player")
    ]
    
    # Create random agents
    random_players = [RandomAgent(f"Random_Player_{i}") for i in range(3)]
    
    # Combine players
    all_players = strategic_players + random_players
    
    # Create tournament manager
    tournament_manager = TournamentManager(output_dir=args.output_dir)
    
    # Run tournament
    if args.two_player:
        # Run 2-player round-robin tournament
        results = tournament_manager.run_2player_tournament(
            players=all_players,
            games_per_matchup=args.games_per_matchup,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    else:
        # Run regular tournament
        results = tournament_manager.run_tournament(
            players=all_players,
            num_games=args.num_games,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    
    # Print summary
    print("\n=== Strategic vs Random Benchmark Summary ===")
    print(f"Strategic Players: {[p.name for p in strategic_players]}")
    print(f"Random Players: {[p.name for p in random_players]}")
    
    if args.two_player:
        print(f"Tournament type: 2-player round-robin")
        print(f"Games per matchup: {args.games_per_matchup}")
        total_games = len(results["games"])
        print(f"Total games played: {total_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / total_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / total_games:.2%})")
    else:
        print(f"Games played: {args.num_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / args.num_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / args.num_games:.2%})")
    
    # Group by player type
    strategic_rankings = [r for r in results["overall_stats"]["player_rankings"] 
                          if any(player in r["player"] for player in ["Aggressive", "Cautious", "Completionist", "Utility", "Balanced", "Dynamic", "OrangeRed", "LateGame", "Trademaster", "Strategic", "NewStrategic"])]
    random_rankings = [r for r in results["overall_stats"]["player_rankings"] 
                       if "Random" in r["player"]]
    
    print("\nStrategic Player Rankings:")
    for i, ranking in enumerate(strategic_rankings):
        print(f"{i+1}. {ranking['player']} - Win Rate: {ranking['win_rate']:.2%}, " +
              f"Draw Rate: {ranking['draw_rate']:.2%}, " +
              f"Net Worth: {int(ranking['avg_net_worth'])}₩, " +
              f"Survival Rate: {ranking['survival_rate']:.2%}")
    
    print("\nRandom Player Rankings:")
    for i, ranking in enumerate(random_rankings):
        print(f"{i+1}. {ranking['player']} - Win Rate: {ranking['win_rate']:.2%}, " +
              f"Draw Rate: {ranking['draw_rate']:.2%}, " +
              f"Net Worth: {int(ranking['avg_net_worth'])}₩, " +
              f"Survival Rate: {ranking['survival_rate']:.2%}")
    
    # Calculate averages for each group
    strategic_win_rate = sum(r["win_rate"] for r in strategic_rankings) / len(strategic_rankings)
    random_win_rate = sum(r["win_rate"] for r in random_rankings) / len(random_rankings)
    
    strategic_net_worth = sum(r["avg_net_worth"] for r in strategic_rankings) / len(strategic_rankings)
    random_net_worth = sum(r["avg_net_worth"] for r in random_rankings) / len(random_rankings)
    
    print("\nGroup Comparison:")
    print(f"Strategic Players - Avg Win Rate: {strategic_win_rate:.2%}, Avg Net Worth: {int(strategic_net_worth)}₩")
    print(f"Random Players - Avg Win Rate: {random_win_rate:.2%}, Avg Net Worth: {int(random_net_worth)}₩")
    
    print("\nCheck the output directory for detailed results and visualizations.")

def compare_all_players(args):
    """Run a comprehensive tournament comparing all available player types."""
    # Create one instance of each player type
    players = [
        AggressiveInvestor("Aggressive_Player"),
        CautiousAccumulator("Cautious_Player"),
        CompletionistBuilder("Completionist_Player"),
        UtilityKing("Utility_Player"),
        OrangeRedSpecialist("OrangeRed_Player"),
        LateGameDeveloper("LateGame_Player"),
        Trademaster("Trademaster_Player"),
        BalancedPlayer("Balanced_Player"),
        DynamicAdapter("Dynamic_Player"),
        StrategicAgent("Strategic_Player"),
        DefaultStrategicPlayer("DefaultStrategic_Player"),
        RandomAgent("Random_Player")
    ]
    
    # Create tournament manager
    tournament_manager = TournamentManager(output_dir=args.output_dir)
    
    # Run tournament
    if args.two_player:
        # Run 2-player round-robin tournament
        results = tournament_manager.run_2player_tournament(
            players=players,
            games_per_matchup=args.games_per_matchup,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    else:
        # Run regular tournament
        results = tournament_manager.run_tournament(
            players=players,
            num_games=args.num_games,
            max_turns=args.max_turns,
            parallel=args.parallel,
            num_workers=args.workers,
            collect_turn_data=not args.no_turn_data,
            save_event_log=args.save_events
        )
    
    # Print summary
    print("\n=== All Players Comparison Summary ===")
    print(f"Players: {[p.name for p in players]}")
    
    if args.two_player:
        print(f"Tournament type: 2-player round-robin")
        print(f"Games per matchup: {args.games_per_matchup}")
        total_games = len(results["games"])
        print(f"Total games played: {total_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / total_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / total_games:.2%})")
    else:
        print(f"Games played: {args.num_games}")
        print(f"Draws: {results['draws']} ({results['draws'] / args.num_games:.2%})")
        print(f"Errors: {results['errors']} ({results['errors'] / args.num_games:.2%})")
    
    print("\nOverall Rankings:")
    
    for i, ranking in enumerate(results["overall_stats"]["player_rankings"]):
        print(f"{i+1}. {ranking['player']} - Win Rate: {ranking['win_rate']:.2%}, " +
              f"Draw Rate: {ranking['draw_rate']:.2%}, " +
              f"Net Worth: {int(ranking['avg_net_worth'])}₩, " +
              f"Survival Rate: {ranking['survival_rate']:.2%}")
    
    print("\nCheck the output directory for detailed results and visualizations.")

if __name__ == "__main__":
    # delete old results
    if os.path.exists("tournament_results"):
        import shutil
        shutil.rmtree("tournament_results")
    os.makedirs("tournament_results", exist_ok=True)

    parser = argparse.ArgumentParser(description="Monopoly Tournament Manager")
    
    # Create subparsers for different experiment types
    subparsers = parser.add_subparsers(dest="experiment_type", help="Type of experiment to run")
    
    # Player comparison experiment
    player_comparison_parser = subparsers.add_parser("player_comparison", help="Compare different player types")
    player_comparison_parser.add_argument("--player-types", nargs="+", required=True,
                                         choices=["aggressive", "cautious", "completionist", "utility", 
                                                  "orange_red", "late_game", "trademaster", "balanced", 
                                                  "dynamic", "strategic", "random", "default_strategic"],
                                         help="Types of players to include in the tournament")
    
    # Custom parameter experiment
    param_experiment_parser = subparsers.add_parser("param_experiment", help="Test custom parameter variations")
    
    # Benchmark against random agents
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark strategic agents against random agents")
    
    # Compare all players
    all_players_parser = subparsers.add_parser("compare_all", help="Run tournament with all player types")
    
    # Common arguments for all experiment types
    for subparser in [player_comparison_parser, param_experiment_parser, benchmark_parser, all_players_parser]:
        subparser.add_argument("--two-player", action="store_true",
                             help="Run a 2-player round-robin tournament instead of regular tournament")
        subparser.add_argument("--num-games", type=int, default=100,
                             help="Number of games to run (for regular tournament, default: 100)")
        subparser.add_argument("--games-per-matchup", type=int, default=50,
                             help="Number of games per matchup (for 2-player tournament, default: 50)")
        subparser.add_argument("--max-turns", type=int, default=1000,
                             help="Maximum number of turns per game (default: 1000)")
        subparser.add_argument("--output-dir", type=str, default="tournament_results",
                             help="Directory to store results (default: tournament_results)")
        subparser.add_argument("--parallel", action="store_true",
                             help="Run games in parallel for faster processing")
        subparser.add_argument("--workers", type=int, default=None,
                             help="Number of parallel workers (default: CPU count)")
        subparser.add_argument("--no-turn-data", action="store_true",
                             help="Don't collect per-turn data (makes simulation faster)")
        subparser.add_argument("--save-events", action="store_true",
                             help="Save full event log (can generate large files)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate experiment
    if args.experiment_type == "player_comparison":
        run_player_comparison(args)
    elif args.experiment_type == "param_experiment":
        run_custom_parameter_experiment(args)
    elif args.experiment_type == "benchmark":
        run_versus_random_benchmark(args)
    elif args.experiment_type == "compare_all":
        compare_all_players(args)
    else:
        parser.print_help()
        sys.exit(1)

    # Example commands:
    
    # Compare specific players in a standard tournament:
    # python tournament.py player_comparison --player-types aggressive cautious balanced strategic random --num-games 100 --max-turns 1000 --parallel
    
    # Run a 2-player round-robin tournament with all players:
    # python tournament.py compare_all --two-player --games-per-matchup 50 --max-turns 1000 --parallel --workers 6