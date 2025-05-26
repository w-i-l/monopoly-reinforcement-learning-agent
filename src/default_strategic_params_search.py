import itertools
import multiprocessing as mp
from functools import partial
import pandas as pd
import numpy as np
import os
import json
import time
import gc  # Import garbage collector
from tqdm import tqdm
import traceback
import random
from typing import Dict, List, Any, Tuple

# Import required agent types and tournament manager
from agents.default_strategic_player import DefaultStrategicPlayer
from agents.default_strategic_player import (
    AggressiveInvestor, CautiousAccumulator, CompletionistBuilder, 
    UtilityKing, OrangeRedSpecialist, LateGameDeveloper, 
    Trademaster, BalancedPlayer, DynamicAdapter
)
from managers.tournament_manager import TournamentManager
from agents.random_agent import RandomAgent
from agents.strategic_agent import StrategicAgent

# Global configuration variables
OUTPUT_DIR = "default_strategic_agents_search"
PHASE1_NUM_CONFIGS = 100        # Number of random configurations to generate
PHASE1_GAMES_PER_MATCHUP = 20   # Games per matchup in phase 1
PHASE1_MAX_TURNS = 300          # Maximum turns per game in phase 1

PHASE2_TOP_CONFIGS = 10         # Number of top configurations to take from phase 1
PHASE2_GAMES_PER_MATCHUP = 30   # Games per matchup in phase 2
PHASE2_MAX_TURNS = 500          # Maximum turns per game in phase 2

PHASE3_TOP_CONFIGS = 5          # Number of top configurations to take from phase 2
PHASE3_GAMES_PER_MATCHUP = 40   # Games per matchup in phase 3
PHASE3_MAX_TURNS = 600          # Maximum turns per game in phase 3

PHASE4_TOP_CONFIGS = 3          # Number of top configurations to take from phase 3
PHASE4_GAMES_PER_MATCHUP = 50   # Games per matchup in phase 4
PHASE4_MAX_TURNS = 750          # Maximum turns per game in phase 4

NUM_PROCESSES = 4               # Number of parallel processes to use

def convert_to_serializable(obj):
    """Convert NumPy types to Python native types for JSON serialization."""
    if isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_to_serializable(obj.tolist())
    elif isinstance(obj, bool):
        return bool(obj)
    else:
        return obj

def run_tournament_vs_default(params_config, games_per_matchup=20, max_turns=300, output_dir="phase1_results"):
    """Run a tournament against the default strategic player."""
    try:
        # Create player with specified parameters
        player_name = f"GridSearch_Player_{params_config['id']}"
        player = DefaultStrategicPlayer(player_name, params_config['params'])
        
        # Create default strategic player as opponent
        opponent = DefaultStrategicPlayer("Default_Strategic")
        
        # Create tournament directory
        config_dir = os.path.join(output_dir, f"config_{params_config['id']}")
        os.makedirs(config_dir, exist_ok=True)
        
        # Run tournament
        tournament_manager = TournamentManager(output_dir=config_dir)
        results = tournament_manager.run_2player_tournament(
            players=[player, opponent],
            games_per_matchup=games_per_matchup,
            max_turns=max_turns,
            parallel=False,  # No nested parallelism to avoid memory issues
            collect_turn_data=False,
            save_event_log=False
        )
        
        # Extract only essential metrics
        win_rate = next((r["win_rate"] for r in results["overall_stats"]["player_rankings"] 
                         if player_name in r["player"]), 0)
        avg_net_worth = next((r["avg_net_worth"] for r in results["overall_stats"]["player_rankings"] 
                             if player_name in r["player"]), 0)
        survival_rate = next((r["survival_rate"] for r in results["overall_stats"]["player_rankings"] 
                             if player_name in r["player"]), 0)
        
        # Calculate combined score (weighted metrics)
        score = win_rate * 0.5 + (survival_rate * 0.3) + (avg_net_worth / 5000) * 0.2
        
        # Clean up to free memory
        del tournament_manager
        del results
        gc.collect()
        
        return {
            "config_id": params_config['id'],
            "params": params_config['params'],
            "win_rate": win_rate,
            "avg_net_worth": avg_net_worth,
            "survival_rate": survival_rate,
            "score": score
        }
    except Exception as e:
        # Log error and return failed result
        print(f"Error in tournament {params_config['id']}: {e}")
        traceback.print_exc()
        
        return {
            "config_id": params_config['id'],
            "params": params_config['params'],
            "win_rate": 0.0,
            "avg_net_worth": 0.0,
            "survival_rate": 0.0,
            "score": 0.0,
            "error": str(e)
        }

def create_random_param_configs(num_configs=100):
    """Create random parameter configurations for initial search with all parameters."""
    # Get default parameters as reference
    default_params = DefaultStrategicPlayer("Default")._get_default_params()
    
    # Define parameter ranges - more extreme to explore wider space
    param_ranges = {
        # Property acquisition
        "min_cash_reserve": (50, 500),
        "property_value_multiplier": (0.8, 2.0),
        "complete_set_bonus": (0.1, 1.0),
        "railway_value_multiplier": (0.8, 2.0),
        "utility_value_multiplier": (0.7, 2.0),
        "first_property_eagerness": (0.3, 1.0),
        
        # Development strategy
        "min_cash_for_houses": (150, 800),
        "house_build_threshold": (0.05, 0.4),
        "min_houses_before_hotel": (1, 4),
        "hotel_roi_threshold": (0.8, 2.0),
        
        # Cash management
        "mortgage_emergency_threshold": (50, 300),
        "mortgage_property_threshold": (0.4, 0.9),
        "unmortgage_threshold": (200, 1000),
        "unmortgage_roi_threshold": (0.8, 1.8),
        
        # Trading strategy
        "trade_eagerness": (0.1, 1.0),
        "trade_profit_threshold": (0.8, 1.8),
        "trade_monopoly_bonus": (100, 800),
        
        # Jail strategy
        "jail_stay_threshold": (0.2, 0.9),
        "use_jail_card_threshold": (0.1, 0.8),
        
        # Bankruptcy strategy
        "bankruptcy_mortgage_first": (True, False),
        "bankruptcy_property_value_weight": (0.8, 2.0),
        "bankruptcy_group_completion_weight": (0.8, 2.5),
        
        # Property valuation
        "early_game_turns": (5, 30),
        "orange_red_property_bonus": (0.8, 1.8),
        "green_blue_property_bonus": (0.8, 1.6),
        "jail_adjacent_bonus": (0.9, 1.5),
        
        # Risk assessment
        "risk_tolerance": (0.2, 1.0),
        "danger_zone_weight": (0.8, 2.0)
    }
    
    # Generate random configurations
    configs = []
    for i in range(num_configs):
        # Start with default parameters
        params = default_params.copy()
        
        # Override with random values
        for param, value_range in param_ranges.items():
            if param == "bankruptcy_mortgage_first":
                # Handle boolean parameter
                params[param] = random.choice(value_range)
            elif isinstance(params[param], int):
                params[param] = random.randint(value_range[0], value_range[1])
            else:
                params[param] = round(random.uniform(value_range[0], value_range[1]), 2)
        
        configs.append({"id": i, "params": params})
    
    return configs

def phase1_random_search(num_processes=4):
    """Phase 1: Generate and evaluate random configurations against default player."""
    # Create output directory
    output_dir = os.path.join(OUTPUT_DIR, "phase1_results")
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate random configurations
    configs = create_random_param_configs(PHASE1_NUM_CONFIGS)
    print(f"Phase 1: Generated {len(configs)} random parameter configurations")
    
    # Save configurations
    with open(os.path.join(output_dir, "phase1_configs.json"), "w") as f:
        json.dump(convert_to_serializable(configs), f, indent=2)
    
    # Run tournaments in parallel
    with mp.Pool(processes=num_processes) as pool:
        run_func = partial(run_tournament_vs_default, 
                          games_per_matchup=PHASE1_GAMES_PER_MATCHUP, 
                          max_turns=PHASE1_MAX_TURNS,
                          output_dir=output_dir)
        
        # Process results as they complete to avoid storing all in memory
        results = []
        for result in tqdm(pool.imap(run_func, configs), total=len(configs)):
            # Add to our minimal results list
            results.append(result)
            
            # Force garbage collection after each tournament
            gc.collect()
    
    # Free memory from configs
    del configs
    gc.collect()
    
    # Save all results to disk
    with open(os.path.join(output_dir, "phase1_results.json"), "w") as f:
        json.dump(convert_to_serializable(results), f, indent=2)
    
    # Create DataFrame only for analysis
    df = pd.DataFrame(results)
    
    # Remove rows with errors
    if "error" in df.columns:
        df = df[df["error"].isna()]
    
    # Extract just the top configurations
    df = df.sort_values("score", ascending=False)
    best_configs = df.head(PHASE2_TOP_CONFIGS)
    
    # Print summary without storing complete results
    print("\nBest configurations from Phase 1 (Random Search):")
    print(best_configs[["config_id", "win_rate", "avg_net_worth", "survival_rate", "score"]])
    
    # Save best configurations
    best_configs.to_csv(os.path.join(output_dir, "phase1_best_configs.csv"), index=False)
    
    # Clean up memory before returning only necessary data
    best_params = best_configs[["config_id", "params", "score"]].copy()
    
    # Free memory
    del df
    del best_configs
    del results
    gc.collect()
    
    return best_params

def run_tournament_with_players(players, games_per_matchup, max_turns, output_dir, phase_name, num_processes):
    """Run a tournament with the given players and return minimal results."""
    # Create directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"{phase_name}: Running tournament with {len(players)} players")
    
    # Run tournament
    tournament_manager = TournamentManager(output_dir=output_dir)
    
    try:
        # Run tournament
        results = tournament_manager.run_2player_tournament(
            players=players,
            games_per_matchup=games_per_matchup,
            max_turns=max_turns,
            parallel=True,
            num_workers=num_processes,
            collect_turn_data=False,
            save_event_log=False
        )
        
        # Extract only essential results to minimize memory usage
        minimal_rankings = []
        for ranking in results["overall_stats"]["player_rankings"]:
            minimal_rankings.append({
                "player": ranking["player"],
                "win_rate": ranking["win_rate"],
                "survival_rate": ranking["survival_rate"],
                "avg_net_worth": ranking["avg_net_worth"]
            })
        
        # Save rankings only (not full results)
        rankings_df = pd.DataFrame(minimal_rankings)
        rankings_df.to_csv(os.path.join(output_dir, f"{phase_name.lower()}_rankings.csv"), index=False)
        
        # Print rankings
        print(f"\n{phase_name} Rankings:")
        print(rankings_df[["player", "win_rate", "avg_net_worth", "survival_rate"]])
        
        # Free memory
        del results
        del tournament_manager
        gc.collect()
        
        return rankings_df
        
    except Exception as e:
        print(f"Error in {phase_name} tournament: {e}")
        traceback.print_exc()
        return None

def phase2_variant_tournament(best_params_from_phase1, num_processes=4):
    """Phase 2: Run tournament with best configs from phase 1 against default variants."""
    output_dir = os.path.join(OUTPUT_DIR, "phase2_results")
    
    # Create mapping between player names and parameters
    player_params_map = {}
    
    # Create players from best parameters
    best_players = []
    for i, row in best_params_from_phase1.iterrows():
        player_name = f"Phase1_Best_{i+1}"
        params = row["params"]
        player = DefaultStrategicPlayer(player_name, params)
        best_players.append(player)
        
        # Store mapping for later retrieval
        player_params_map[player_name] = params
    
    # Save this mapping for later phases
    with open(os.path.join(output_dir, "player_params_map.json"), "w") as f:
        json.dump(convert_to_serializable(player_params_map), f, indent=2)
    
    # Create default variant players
    variant_players = [
        DefaultStrategicPlayer("DefaultStrategic"),
        AggressiveInvestor("Aggressive"),
        CautiousAccumulator("Cautious"),
        CompletionistBuilder("Completionist"),
        UtilityKing("UtilityKing"),
        OrangeRedSpecialist("OrangeRed"),
        LateGameDeveloper("LateGame"),
        Trademaster("Trademaster"),
        BalancedPlayer("Balanced"),
        DynamicAdapter("Dynamic")
    ]
    
    # All players for the tournament
    all_players = best_players + variant_players
    
    # Run tournament and get rankings
    rankings = run_tournament_with_players(
        all_players, PHASE2_GAMES_PER_MATCHUP, PHASE2_MAX_TURNS, 
        output_dir, "Phase 2", num_processes
    )
    
    if rankings is None:
        return {"error": "Failed to complete Phase 2 tournament"}
    
    # Extract top Phase1_Best players for next phase
    top_configs = []
    for i, row in rankings.iterrows():
        if "Phase1_Best" in row["player"]:
            player_name = row["player"]
            
            if player_name in player_params_map:
                top_configs.append({
                    "player": player_name,
                    "params": player_params_map[player_name],
                    "win_rate": row["win_rate"],
                    "survival_rate": row["survival_rate"],
                    "avg_net_worth": row["avg_net_worth"]
                })
                
                if len(top_configs) >= PHASE3_TOP_CONFIGS:
                    break
    
    # If we couldn't find enough ranked Phase1_Best players
    if len(top_configs) < PHASE3_TOP_CONFIGS:
        # Use more from the original best configs
        for i, (player, params) in enumerate(player_params_map.items()):
            if player not in [config["player"] for config in top_configs]:
                top_configs.append({
                    "player": player,
                    "params": params,
                    "win_rate": 0,  # Default values
                    "survival_rate": 0,
                    "avg_net_worth": 0
                })
                
                if len(top_configs) >= PHASE3_TOP_CONFIGS:
                    break
    
    # Save just the essential data for the next phase
    top_configs_df = pd.DataFrame(top_configs)
    top_configs_df.to_csv(os.path.join(output_dir, "top_configs_for_phase3.csv"), index=False)
    
    # Free memory
    del rankings
    del player_params_map
    del best_players
    del variant_players
    del all_players
    gc.collect()
    
    return top_configs_df

def phase3_refinement_tournament(top_configs_from_phase2, num_processes=4):
    """Phase 3: Run tournament with only top configurations to refine rankings."""
    output_dir = os.path.join(OUTPUT_DIR, "phase3_results")
    
    # Create players from top configurations
    players = []
    player_params_map = {}
    
    for i, row in top_configs_from_phase2.iterrows():
        player_name = f"Top_Config_{i+1}"
        params = row["params"]
        player = DefaultStrategicPlayer(player_name, params)
        players.append(player)
        
        # Store mapping
        player_params_map[player_name] = params
    
    # Save mapping for reference
    with open(os.path.join(output_dir, "player_params_map.json"), "w") as f:
        json.dump(convert_to_serializable(player_params_map), f, indent=2)
    
    # Run tournament and get rankings
    rankings = run_tournament_with_players(
        players, PHASE3_GAMES_PER_MATCHUP, PHASE3_MAX_TURNS, 
        output_dir, "Phase 3", num_processes
    )
    
    if rankings is None:
        return {"error": "Failed to complete Phase 3 tournament"}
    
    # Extract top performers for final phase
    top_configs = []
    for i, row in rankings.iterrows():
        player_name = row["player"]
        
        if player_name in player_params_map:
            top_configs.append({
                "player": player_name,
                "params": player_params_map[player_name],
                "win_rate": row["win_rate"],
                "survival_rate": row["survival_rate"],
                "avg_net_worth": row["avg_net_worth"]
            })
            
            if len(top_configs) >= PHASE4_TOP_CONFIGS:
                break
    
    # Save for next phase
    top_configs_df = pd.DataFrame(top_configs)
    top_configs_df.to_csv(os.path.join(output_dir, "top_configs_for_phase4.csv"), index=False)
    
    # Free memory
    del rankings
    del player_params_map
    del players
    gc.collect()
    
    return top_configs_df

def phase4_final_tournament(top_configs_from_phase3, num_processes=4):
    """Phase 4: Final tournament with best configs and all default variants."""
    output_dir = os.path.join(OUTPUT_DIR, "phase4_results")
    
    # Create players from best configurations
    best_players = []
    for i, row in top_configs_from_phase3.iterrows():
        player_name = f"Optimized_{i+1}"
        params = row["params"]
        player = DefaultStrategicPlayer(player_name, params)
        best_players.append(player)
        
        # Save each optimal configuration for reference
        with open(os.path.join(output_dir, f"optimized_config_{i+1}.json"), "w") as f:
            json.dump(convert_to_serializable(params), f, indent=2)
    
    # Create all default variant players
    variant_players = [
        DefaultStrategicPlayer("DefaultStrategic"),
        AggressiveInvestor("Aggressive"),
        CautiousAccumulator("Cautious"),
        CompletionistBuilder("Completionist"),
        UtilityKing("UtilityKing"),
        OrangeRedSpecialist("OrangeRed"),
        LateGameDeveloper("LateGame"),
        Trademaster("Trademaster"),
        BalancedPlayer("Balanced"),
        DynamicAdapter("Dynamic"),
        StrategicAgent("Strategic"),
        RandomAgent("Random")
    ]
    
    # All players for the final tournament
    all_players = best_players + variant_players
    
    # Run tournament and get rankings
    rankings = run_tournament_with_players(
        all_players, PHASE4_GAMES_PER_MATCHUP, PHASE4_MAX_TURNS, 
        output_dir, "Phase 4", num_processes
    )
    
    if rankings is None:
        return {"error": "Failed to complete Phase 4 tournament"}
    
    # Generate final report with just the rankings
    generate_final_report(rankings, top_configs_from_phase3, output_dir)
    
    # Free memory before returning
    result = {"completed": True}
    
    del rankings
    del best_players
    del variant_players
    del all_players
    gc.collect()
    
    return result

def generate_final_report(rankings, top_configs, output_dir):
    """Generate detailed report of the optimized configurations."""
    report_path = os.path.join(output_dir, "final_report.txt")
    
    with open(report_path, "w") as f:
        f.write("=== MONOPOLY AI PARAMETER OPTIMIZATION - FINAL REPORT ===\n\n")
        
        f.write("== FINAL RANKINGS ==\n")
        f.write(rankings[["player", "win_rate", "survival_rate", "avg_net_worth"]].to_string(index=False))
        f.write("\n\n")
        
        # Check how optimized configurations performed
        optimized_rankings = rankings[rankings["player"].str.contains("Optimized")].copy()
        f.write(f"Optimized Configurations Performance:\n")
        f.write(optimized_rankings[["player", "win_rate", "survival_rate", "avg_net_worth"]].to_string(index=False))
        f.write("\n\n")
        
        # Analyze top performer
        if not optimized_rankings.empty:
            top_idx = optimized_rankings.index[0]
            top_config_idx = int(optimized_rankings.iloc[0]["player"].split("_")[-1]) - 1
            
            if top_config_idx < len(top_configs):
                top_config = top_configs.iloc[top_config_idx]
                
                f.write("== TOP PERFORMING CONFIGURATION ==\n")
                f.write(f"Player: {optimized_rankings.iloc[0]['player']}\n")
                f.write(f"Win Rate: {optimized_rankings.iloc[0]['win_rate']:.2%}\n")
                f.write(f"Survival Rate: {optimized_rankings.iloc[0]['survival_rate']:.2%}\n")
                f.write(f"Average Net Worth: ${optimized_rankings.iloc[0]['avg_net_worth']:.2f}\n\n")
                
                f.write("Parameter Configuration:\n")
                for param, value in top_config["params"].items():
                    f.write(f"  {param}: {value}\n")
                
                f.write("\n\n")
                
                # Compare with default strategic player
                default_idx = rankings[rankings["player"] == "DefaultStrategic"].index
                if len(default_idx) > 0:
                    default_idx = default_idx[0]
                    default_rank = default_idx + 1
                    
                    win_rate_diff = optimized_rankings.iloc[0]['win_rate'] - rankings.iloc[default_idx]['win_rate']
                    survival_diff = optimized_rankings.iloc[0]['survival_rate'] - rankings.iloc[default_idx]['survival_rate']
                    networth_diff = optimized_rankings.iloc[0]['avg_net_worth'] - rankings.iloc[default_idx]['avg_net_worth']
                    
                    f.write("== COMPARISON WITH DEFAULT STRATEGIC PLAYER ==\n")
                    f.write(f"Default Strategic Rank: {default_rank}\n")
                    f.write(f"Win Rate Improvement: {win_rate_diff:.2%}\n")
                    f.write(f"Survival Rate Improvement: {survival_diff:.2%}\n")
                    f.write(f"Net Worth Improvement: ${networth_diff:.2f}\n")
                    f.write("\n")
        
        f.write("=== END OF REPORT ===\n")
    
    print(f"Final report generated at {report_path}")

def main():
    """Main function to run the multi-phase parameter optimization process."""
    try:
        # Create main output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"Starting parameter optimization for DefaultStrategicPlayer")
        print(f"Results will be saved to {OUTPUT_DIR}")
        print(f"Using {NUM_PROCESSES} worker processes")
        
        # Phase 1: Random Search
        print("\n=== Phase 1: Random Search vs Default Player ===")
        phase1_results = phase1_random_search(num_processes=NUM_PROCESSES)
        
        # Force cleanup after phase 1
        gc.collect()
        
        # Phase 2: Tournament with Default Variants
        print("\n=== Phase 2: Tournament with Default Variants ===")
        phase2_results = phase2_variant_tournament(
            phase1_results,
            num_processes=NUM_PROCESSES
        )
        
        # Free phase 1 data
        del phase1_results
        gc.collect()
        
        if isinstance(phase2_results, dict) and "error" in phase2_results:
            print(f"Error in Phase 2: {phase2_results['error']}")
            return
        
        # Phase 3: Refinement Tournament
        print("\n=== Phase 3: Refinement Tournament ===")
        phase3_results = phase3_refinement_tournament(
            phase2_results,
            num_processes=NUM_PROCESSES
        )
        
        # Free phase 2 data
        del phase2_results
        gc.collect()
        
        if isinstance(phase3_results, dict) and "error" in phase3_results:
            print(f"Error in Phase 3: {phase3_results['error']}")
            return
        
        # Phase 4: Final Tournament
        print("\n=== Phase 4: Final Tournament ===")
        phase4_results = phase4_final_tournament(
            phase3_results,
            num_processes=NUM_PROCESSES
        )
        
        # Final cleanup
        final_top_configs = phase3_results
        del phase3_results
        gc.collect()
        
        # Generate final summary with minimal data
        summary_path = os.path.join(OUTPUT_DIR, "optimization_summary.txt")
        with open(summary_path, "w") as f:
            f.write("=== MONOPOLY AI PARAMETER OPTIMIZATION SUMMARY ===\n\n")
            
            f.write("Optimization complete! See individual phase directories for detailed results.\n\n")
            
            f.write("Top performing configurations are stored in the phase4_results directory.\n")
            f.write("See final_report.txt for detailed analysis of the best configuration.\n\n")
            
            # Report minimal info about top configs
            if len(final_top_configs) > 0:
                f.write("=== TOP CONFIGURATION PARAMETERS ===\n")
                for i, row in final_top_configs.head(1).iterrows():
                    f.write(f"Configuration from: {row.get('player', f'Optimized_{i+1}')}\n")
                    for param, value in row["params"].items():
                        f.write(f"{param}: {value}\n")
            
        print(f"\nOptimization complete! Summary saved to {summary_path}")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        # Ensure garbage collection even on error
        gc.collect()

if __name__ == "__main__":
    main()
