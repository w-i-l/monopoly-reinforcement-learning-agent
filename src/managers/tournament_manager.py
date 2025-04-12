import json
import os
import time
import datetime
import itertools
from typing import List, Dict, Any, Optional, Tuple
import random
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
from tqdm import tqdm
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed

from game.player import Player
from managers.game_manager import GameManager
from game.game_state import GameState
from models.property_group import PropertyGroup
from exceptions.exceptions import *
from events.events import EventType
from utils.logger import ErrorLogger


class TournamentManager:
    """
    Manages tournaments between different Monopoly player agents,
    collecting comprehensive statistics for comparison and analysis.
    """
    
    def __init__(self, output_dir: str = "tournament_results"):
        """
        Initialize the tournament manager.
        
        Args:
            output_dir: Directory to store tournament results and graphs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "json"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "graphs"), exist_ok=True)  # Add this line
        
        # Create improved folder structure
        os.makedirs(os.path.join(output_dir, "matchups"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "player_metrics"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "comparison_metrics"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "explanations"), exist_ok=True)
        
        self.tournament_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def run_tournament(
            self, 
            players: List[Player], 
            num_games: int, 
            max_turns: int,
            parallel: bool = False,
            num_workers: int = None,
            collect_turn_data: bool = True,
            save_event_log: bool = False
        ) -> Dict[str, Any]:
        """
        Run a tournament with the specified players.
        
        Args:
            players: List of player agents to participate
            num_games: Number of games to simulate
            max_turns: Maximum number of turns per game
            parallel: Whether to run games in parallel for faster processing
            num_workers: Number of parallel workers (defaults to CPU count if None)
            collect_turn_data: Whether to collect detailed per-turn data (may slow down simulation)
            save_event_log: Whether to save the full event log (can generate large files)
            
        Returns:
            Dictionary containing tournament results and statistics
        """
        print(f"Starting tournament with {len(players)} players: {[p.name for p in players]}")
        print(f"Running {num_games} games with max {max_turns} turns per game")
        
        # Create a timestamp for this tournament
        timestamp = int(time.time())
        
        # Prepare tournament results structure
        tournament_results = {
            "tournament_id": self.tournament_id,
            "timestamp": timestamp,
            "date": datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "num_games": num_games,
            "max_turns": max_turns,
            "players": [player.name for player in players],
            "player_types": [type(player).__name__ for player in players],
            "games": [],
            "player_stats": {player.name: {} for player in players},
            "overall_stats": {},
            "draws": 0,  # New: Track total number of draws
            "errors": 0  # New: Track total number of errors
        }
        
        if parallel and num_games > 1:
            # Run games in parallel
            game_results = self._run_games_parallel(
                players, num_games, max_turns, collect_turn_data, save_event_log, num_workers
            )
        else:
            # Run games sequentially
            game_results = self._run_games_sequential(
                players, num_games, max_turns, collect_turn_data, save_event_log
            )
        
        # Add game results to tournament results
        tournament_results["games"] = game_results
        
        # Count draws and errors
        tournament_results["draws"] = sum(1 for game in game_results if game.get("is_draw", False))
        tournament_results["errors"] = sum(1 for game in game_results if "error" in game)
        
        # Compute aggregate statistics
        self._compute_player_statistics(tournament_results)
        self._compute_overall_statistics(tournament_results)
        
        # Save results to JSON file
        self._save_tournament_results(tournament_results)
        
        # Generate explanations about metrics
        self._generate_metrics_explanation(tournament_results)
        
        # Generate visualizations
        self._generate_visualizations(tournament_results)
        
        print("Tournament completed successfully!")
        print(f"Results saved to {self.output_dir}")
        
        return tournament_results
    
    def run_2player_tournament(
            self, 
            players: List[Player], 
            games_per_matchup: int, 
            max_turns: int,
            parallel: bool = False,
            num_workers: int = None,
            collect_turn_data: bool = False,
            save_event_log: bool = False
        ) -> Dict[str, Any]:
        """
        Run a round-robin tournament with 2-player games for all combinations of players.
        
        Args:
            players: List of player agents to participate
            games_per_matchup: Number of games to simulate for each pair of players
            max_turns: Maximum number of turns per game
            parallel: Whether to run games in parallel for faster processing
            num_workers: Number of parallel workers (defaults to CPU count if None)
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            
        Returns:
            Dictionary containing tournament results and statistics
        """
        player_names = [p.name for p in players]
        player_types = [type(p).__name__ for p in players]
        num_players = len(players)
        num_matchups = (num_players * (num_players - 1)) // 2  # Number of unique player pairs
        total_games = num_matchups * games_per_matchup
        
        print(f"Starting 2-player tournament with {num_players} players: {player_names}")
        print(f"Running {total_games} games ({games_per_matchup} games per matchup) with max {max_turns} turns per game")
        
        # Create a timestamp for this tournament
        timestamp = int(time.time())
        
        # Prepare tournament results structure with extra matchup data
        tournament_results = {
            "tournament_id": self.tournament_id,
            "timestamp": timestamp,
            "date": datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "tournament_type": "2-player round-robin",
            "games_per_matchup": games_per_matchup,
            "max_turns": max_turns,
            "players": player_names,
            "player_types": player_types,
            "games": [],
            "player_stats": {player_name: {} for player_name in player_names},
            "matchup_stats": {},  # New: Store head-to-head results
            "overall_stats": {},
            "draws": 0,  # Track total number of draws
            "errors": 0   # Track total number of errors
        }
        
        # Generate all unique player pairings
        matchups = list(itertools.combinations(range(num_players), 2))
        
        if parallel and total_games > 1:
            # Run games in parallel
            game_results = self._run_2player_games_parallel(
                players, matchups, games_per_matchup, max_turns, 
                collect_turn_data, save_event_log, num_workers
            )
        else:
            # Run games sequentially
            game_results = self._run_2player_games_sequential(
                players, matchups, games_per_matchup, max_turns,
                collect_turn_data, save_event_log
            )
        
        # Add game results to tournament results
        tournament_results["games"] = game_results
        
        # Count draws and errors
        tournament_results["draws"] = sum(1 for game in game_results if game.get("is_draw", False))
        tournament_results["errors"] = sum(1 for game in game_results if "error" in game)
        
        # Compute aggregate statistics
        self._compute_player_statistics(tournament_results)
        self._compute_matchup_statistics(tournament_results)
        self._compute_overall_statistics(tournament_results)
        
        # Generate explanations about metrics
        self._generate_metrics_explanation(tournament_results)
        
        # Save results to JSON file
        self._save_tournament_results(tournament_results)
        
        # Generate visualizations including matchup-specific ones
        self._generate_2player_visualizations(tournament_results)
        
        print("2-player tournament completed successfully!")
        print(f"Results saved to {self.output_dir}")
        
        return tournament_results
    
    def _run_games_sequential(
            self, 
            players: List[Player], 
            num_games: int, 
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool
        ) -> List[Dict[str, Any]]:
        """
        Run games sequentially.
        
        Args:
            players: List of player agents
            num_games: Number of games to run
            max_turns: Maximum turns per game
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            
        Returns:
            List of game result dictionaries
        """
        game_results = []
        
        # Run each game
        for game_idx in tqdm(range(num_games), desc="Running games"):
            # Create a new game with shuffled player order to ensure fairness
            game_players = players.copy()
            random.shuffle(game_players)
            
            # Run the game and get results
            game_result = self._run_single_game(
                game_players, game_idx, max_turns, collect_turn_data, save_event_log
            )
            game_results.append(game_result)
            
        return game_results
    
    def _run_2player_games_sequential(
            self, 
            players: List[Player], 
            matchups: List[Tuple[int, int]],
            games_per_matchup: int,
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool
        ) -> List[Dict[str, Any]]:
        """
        Run 2-player games sequentially for each matchup.
        
        Args:
            players: List of player agents
            matchups: List of tuples with player indices (i, j)
            games_per_matchup: Number of games to run per matchup
            max_turns: Maximum turns per game
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            
        Returns:
            List of game result dictionaries
        """
        game_results = []
        game_idx = 0
        
        # Run games for each matchup
        for player1_idx, player2_idx in tqdm(matchups, desc="Running matchups"):
            for _ in range(games_per_matchup):
                # Create copies of players to avoid state contamination between games
                player1 = type(players[player1_idx])(players[player1_idx].name)
                player2 = type(players[player2_idx])(players[player2_idx].name)
                
                # Randomly decide player order for fairness
                if random.random() < 0.5:
                    game_players = [player1, player2]
                else:
                    game_players = [player2, player1]
                
                # Run the game and get results
                game_result = self._run_single_game(
                    game_players, game_idx, max_turns, collect_turn_data, save_event_log
                )
                
                # Add matchup information to the result
                game_result["matchup"] = (players[player1_idx].name, players[player2_idx].name)
                
                game_results.append(game_result)
                game_idx += 1
            
        return game_results
    
    def _run_games_parallel(
            self, 
            players: List[Player], 
            num_games: int, 
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool,
            num_workers: Optional[int] = None
        ) -> List[Dict[str, Any]]:
        """
        Run games in parallel for faster processing.
        
        Args:
            players: List of player agents
            num_games: Number of games to run
            max_turns: Maximum turns per game
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            num_workers: Number of parallel workers (defaults to CPU count)
            
        Returns:
            List of game result dictionaries
        """
        game_results = []
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            # Submit all games to the executor
            for game_idx in range(num_games):
                # Create a new game with shuffled player order
                game_players = [type(p)(p.name) for p in players]  # Create new instances
                random.shuffle(game_players)
                
                # Submit the game
                future = executor.submit(
                    self._run_single_game,
                    game_players, game_idx, max_turns, collect_turn_data, save_event_log
                )
                futures.append(future)
            
            # Collect results as they complete
            for future in tqdm(as_completed(futures), total=num_games, desc="Running games"):
                try:
                    game_result = future.result()
                    game_results.append(game_result)
                except Exception as e:
                    print(f"Game failed with error: {e}")
                    # Add error result
                    game_results.append({
                        "game_index": len(game_results),
                        "error": str(e),
                        "players": [p.name for p in players]
                    })
        
        # Sort results by game index for consistency
        game_results.sort(key=lambda x: x["game_index"])
        
        return game_results
    
    def _run_2player_games_parallel(
            self, 
            players: List[Player], 
            matchups: List[Tuple[int, int]],
            games_per_matchup: int,
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool,
            num_workers: Optional[int] = None
        ) -> List[Dict[str, Any]]:
        """
        Run 2-player games in parallel for each matchup.
        
        Args:
            players: List of player agents
            matchups: List of tuples with player indices (i, j)
            games_per_matchup: Number of games to run per matchup
            max_turns: Maximum turns per game
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            num_workers: Number of parallel workers (defaults to CPU count)
            
        Returns:
            List of game result dictionaries
        """
        game_results = []
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            game_idx = 0
            
            # Submit all games to the executor
            for player1_idx, player2_idx in matchups:
                for _ in range(games_per_matchup):
                    # Create copies of players to avoid state contamination
                    player1 = type(players[player1_idx])(players[player1_idx].name)
                    player2 = type(players[player2_idx])(players[player2_idx].name)
                    
                    # Randomly decide player order for fairness
                    if random.random() < 0.5:
                        game_players = [player1, player2]
                    else:
                        game_players = [player2, player1]
                    
                    # Store matchup information for later
                    matchup_info = (players[player1_idx].name, players[player2_idx].name)
                    
                    # Submit the game
                    future = executor.submit(
                        self._run_single_game_with_matchup,
                        game_players, game_idx, max_turns, collect_turn_data, save_event_log, matchup_info
                    )
                    futures.append(future)
                    game_idx += 1
            
            # Collect results as they complete
            for future in tqdm(as_completed(futures), total=len(futures), desc="Running games"):
                try:
                    game_result = future.result()
                    game_results.append(game_result)
                except Exception as e:
                    print(f"Game failed with error: {e}")
                    # Add error result
                    game_results.append({
                        "game_index": len(game_results),
                        "error": str(e),
                        "players": [p.name for p in players]
                    })
        
        # Sort results by game index for consistency
        game_results.sort(key=lambda x: x["game_index"])
        
        return game_results
    
    def _run_single_game_with_matchup(
            self, 
            game_players: List[Player], 
            game_idx: int, 
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool,
            matchup_info: Tuple[str, str]
        ) -> Dict[str, Any]:
        """
        Run a single game with matchup information.
        
        Args:
            game_players: List of players for this specific game
            game_idx: Index/ID of the game
            max_turns: Maximum number of turns
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            matchup_info: Tuple containing the players' names in the matchup
            
        Returns:
            Dictionary containing game results
        """
        game_result = self._run_single_game(
            game_players, game_idx, max_turns, collect_turn_data, save_event_log
        )
        game_result["matchup"] = matchup_info
        return game_result
    
    def _run_single_game(
            self, 
            game_players: List[Player], 
            game_idx: int, 
            max_turns: int,
            collect_turn_data: bool,
            save_event_log: bool
        ) -> Dict[str, Any]:
        """
        Run a single game and collect statistics.
        
        Args:
            game_players: List of players for this specific game
            game_idx: Index/ID of the game
            max_turns: Maximum number of turns
            collect_turn_data: Whether to collect detailed per-turn data
            save_event_log: Whether to save the full event log
            
        Returns:
            Dictionary containing game results
        """
        # Initialize game result structure
        game_result = {
            "game_index": game_idx,
            "players": [player.name for player in game_players],
            "turn_count": 0,
            "max_turns_reached": False,
            "winner": None,
            "is_draw": False,  # New: Track if the game ended in a draw
            "bankrupt_players": [],
            "final_state": {},
            "player_stats": {player.name: {} for player in game_players},
            "turn_data": [] if collect_turn_data else None,
            "events": [] if save_event_log else None
        }
        
        try:
            # Initialize game
            game_manager = GameManager(game_players)
            
            # Configure event logging if needed
            if save_event_log:
                self._setup_event_logging(game_manager, game_result)
            
            # Track game state through time
            turn_counter = 0
            active_players = len(game_players)
            
            # Run the game until completion or max turns
            while active_players > 1 and turn_counter < max_turns:
                current_player = game_players[game_manager.game_state.current_player_index]
                
                # Collect per-turn data if enabled
                if collect_turn_data:
                    turn_data = self._collect_turn_data(game_manager.game_state, turn_counter)
                    game_result["turn_data"].append(turn_data)
                
                # Play a turn
                try:
                    game_manager.play_turn()
                except (NotPropertyOwnerException, NotEnoughBalanceException, ExcedingMoneyInTraddingOfferException, NotEnoughJailCardsException) as e:
                    # Handle trading exceptions (overlapping properties in multiple trades)
                    # Just log and continue
                    pass
                except BankrupcyException as e:
                    # Record bankruptcy
                    bankrupt_player = game_manager.game_state.players[game_manager.game_state.current_player_index]
                    game_result["bankrupt_players"].append(bankrupt_player.name)
                    active_players -= 1
                
                # Change turn
                game_manager.change_turn()
                turn_counter += 1
            
            # Record game outcome
            game_result["turn_count"] = turn_counter
            game_result["max_turns_reached"] = turn_counter >= max_turns
            
            # Determine winner
            if active_players == 1:
                # Last player standing is the winner
                for player in game_players:
                    if player.name not in game_result["bankrupt_players"]:
                        game_result["winner"] = player.name
                        break
            else:
                # Max turns reached, determine winner by net worth
                player_worths = {
                    player.name: game_manager.game_state.get_player_net_worth(player)
                    for player in game_players
                    if player.name not in game_result["bankrupt_players"]
                }
                
                if player_worths:
                    # Check for a draw (equal net worth)
                    max_worth = max(player_worths.values())
                    winners = [player for player, worth in player_worths.items() 
                              if worth == max_worth]
                    
                    if len(winners) > 1:
                        game_result["is_draw"] = True
                        game_result["winner"] = None
                        game_result["draw_players"] = winners
                    else:
                        game_result["winner"] = max(player_worths.items(), key=lambda x: x[1])[0]
            
            # Record final game state
            self._record_final_state(game_manager.game_state, game_result)
            
            # Compute per-player statistics for this game
            self._compute_game_player_stats(game_manager.game_state, game_result)
            
        except Exception as e:
            # Handle any unexpected errors
            game_result["error"] = str(e)
            ErrorLogger.log_error(e)
        
        return game_result
    
    def _setup_event_logging(
            self, 
            game_manager: GameManager, 
            game_result: Dict[str, Any]
        ) -> None:
        """
        Set up event logging for a game.
        
        Args:
            game_manager: The game manager instance
            game_result: Dictionary to store game results
        """
        # Create a reference to the original register_event method
        original_register_event = game_manager.event_manager.register_event
        
        # Define a wrapper that logs events to the game result
        def event_logger(event_type, player, **kwargs):
            # Call the original method
            event = original_register_event(event_type, player, **kwargs)
            
            # Log the event
            event_data = {
                "type": event.type.name,
                "player": str(event.player),
                "description": event.description,
                "target_player": str(event.target_player) if event.target_player else None,
                "tile": str(event.tile) if event.tile else None,
                "amount": event.amount,
                "dice": event.dice
            }
            game_result["events"].append(event_data)
            
            return event
        
        # Replace the original method with our wrapper
        game_manager.event_manager.register_event = event_logger
    
    def _collect_turn_data(self, game_state: GameState, turn: int) -> Dict[str, Any]:
        """
        Collect data for a single turn.
        
        Args:
            game_state: Current game state
            turn: Turn number
            
        Returns:
            Dictionary containing turn data
        """
        turn_data = {
            "turn": turn,
            "current_player": str(game_state.players[game_state.current_player_index]),
            "player_data": {}
        }
        
        # Collect data for each player
        for player in game_state.players:
            player_name = str(player)
            
            # Basic state
            player_data = {
                "position": game_state.player_positions[player],
                "cash": game_state.player_balances[player],
                "in_jail": game_state.in_jail[player],
                "jail_cards": game_state.escape_jail_cards[player],
                
                # Property portfolio
                "properties_count": len(game_state.properties[player]),
                "properties": [str(p) for p in game_state.properties[player]],
                "mortgaged_properties": [str(p) for p in game_state.properties[player] 
                                        if p in game_state.mortgaged_properties],
                
                # Development
                "houses": self._count_player_houses(game_state, player),
                "hotels": self._count_player_hotels(game_state, player),
                
                # Monopolies
                "monopolies": self._count_player_monopolies(game_state, player),
                
                # Net worth
                "net_worth": game_state.get_player_net_worth(player)
            }
            
            turn_data["player_data"][player_name] = player_data
        
        return turn_data
    
    def _record_final_state(self, game_state: GameState, game_result: Dict[str, Any]) -> None:
        """
        Record the final state of the game.
        
        Args:
            game_state: Final game state
            game_result: Dictionary to store results
        """
        final_state = {
            "player_positions": {str(p): pos for p, pos in game_state.player_positions.items()},
            "player_balances": {str(p): bal for p, bal in game_state.player_balances.items()},
            "player_properties": {str(p): [str(prop) for prop in props] 
                                for p, props in game_state.properties.items()},
            "player_houses": {str(p): self._count_player_houses(game_state, p) 
                             for p in game_state.players},
            "player_hotels": {str(p): self._count_player_hotels(game_state, p) 
                             for p in game_state.players},
            "player_net_worth": {str(p): game_state.get_player_net_worth(p) 
                                for p in game_state.players},
            "player_monopolies": {str(p): self._count_player_monopolies(game_state, p) 
                                 for p in game_state.players}
        }
        
        game_result["final_state"] = final_state
    
    def _compute_game_player_stats(self, game_state: GameState, game_result: Dict[str, Any]) -> None:
        """
        Compute per-player statistics for a single game.
        
        Args:
            game_state: Final game state
            game_result: Dictionary to store results
        """
        for player in game_state.players:
            player_name = str(player)
            player_stats = {}
            
            # Basic outcomes
            player_stats["is_winner"] = player_name == game_result["winner"]
            player_stats["is_draw"] = game_result.get("is_draw", False) and (
                "draw_players" in game_result and 
                player_name in game_result["draw_players"]
            )
            player_stats["went_bankrupt"] = player_name in game_result["bankrupt_players"]
            player_stats["survived_to_end"] = not player_stats["went_bankrupt"]
            
            # Property acquisition
            player_stats["properties_owned"] = len(game_state.properties[player])
            player_stats["properties_mortgaged"] = sum(1 for p in game_state.properties[player] 
                                                     if p in game_state.mortgaged_properties)
            player_stats["monopolies_owned"] = self._count_player_monopolies(game_state, player)
            
            # Calculate property group distribution
            group_counts = defaultdict(int)
            for prop in game_state.properties[player]:
                if hasattr(prop, 'group'):
                    group_counts[str(prop.group)] += 1
            player_stats["property_groups"] = dict(group_counts)
            
            # Development
            player_stats["houses_built"] = self._count_player_houses(game_state, player)
            player_stats["hotels_built"] = self._count_player_hotels(game_state, player)
            
            # Financial
            player_stats["final_cash"] = game_state.player_balances[player]
            player_stats["final_net_worth"] = game_state.get_player_net_worth(player)
            
            # Store statistics
            game_result["player_stats"][player_name] = player_stats
    
    def _compute_player_statistics(self, tournament_results: Dict[str, Any]) -> None:
        """
        Compute aggregate statistics for each player across all games.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        player_names = tournament_results["players"]
        num_games = len(tournament_results["games"])
        num_draws = tournament_results.get("draws", 0)
        num_errors = tournament_results.get("errors", 0)
        
        # Initialize player statistics
        for player_name in player_names:
            tournament_results["player_stats"][player_name] = {
                "games_played": num_games,
                "wins": 0,
                "draws": 0,  # New: Track draws
                "draw_rate": 0.0,  # New: Draw rate
                "errors": 0,  # New: Track errors
                "error_rate": 0.0,  # New: Error rate
                "bankrupt_games": 0,
                "bankruptcies": 0,
                "survival_rate": 0.0,
                "avg_game_duration": 0.0,
                "avg_properties_owned": 0.0,
                "avg_monopolies_owned": 0.0,
                "avg_houses_built": 0.0,
                "avg_hotels_built": 0.0,
                "avg_final_cash": 0.0,
                "avg_final_net_worth": 0.0,
                "property_group_preferences": {},
                "development_rate": 0.0
            }
        
        # Collect stats from each game
        for game in tournament_results["games"]:
            # Handle error games
            if "error" in game:
                for player_name in game["players"]:
                    if player_name in tournament_results["player_stats"]:
                        tournament_results["player_stats"][player_name]["errors"] += 1
                continue
                
            # Handle normal games
            winner = game.get("winner")
            is_draw = game.get("is_draw", False)
            
            for player_name in player_names:
                if player_name not in game["player_stats"]:
                    continue
                    
                player_game_stats = game["player_stats"][player_name]
                player_tournament_stats = tournament_results["player_stats"][player_name]
                
                # Track wins, draws, and bankrupcies
                if winner == player_name:
                    player_tournament_stats["wins"] += 1
                
                if is_draw and player_name in game.get("draw_players", []):
                    player_tournament_stats["draws"] += 1
                
                if player_game_stats.get("went_bankrupt", False):
                    player_tournament_stats["bankruptcies"] += 1
                
                # Count games where a bankruptcy occurred (by any player)
                if game["bankrupt_players"]:
                    player_tournament_stats["bankrupt_games"] += 1
                
                # Accumulate stats for averaging later
                player_tournament_stats["avg_properties_owned"] += player_game_stats.get("properties_owned", 0)
                player_tournament_stats["avg_monopolies_owned"] += player_game_stats.get("monopolies_owned", 0)
                player_tournament_stats["avg_houses_built"] += player_game_stats.get("houses_built", 0)
                player_tournament_stats["avg_hotels_built"] += player_game_stats.get("hotels_built", 0)
                player_tournament_stats["avg_final_cash"] += player_game_stats.get("final_cash", 0)
                player_tournament_stats["avg_final_net_worth"] += player_game_stats.get("final_net_worth", 0)
                
                # Track property group distribution
                prop_groups = player_game_stats.get("property_groups", {})
                for group, count in prop_groups.items():
                    if group not in player_tournament_stats["property_group_preferences"]:
                        player_tournament_stats["property_group_preferences"][group] = 0
                    player_tournament_stats["property_group_preferences"][group] += count
        
        # Calculate averages and rates
        for player_name in player_names:
            stats = tournament_results["player_stats"][player_name]
            valid_games = num_games - stats["errors"]
            
            if valid_games > 0:
                # Win rate = wins / (total games - errors)
                stats["win_rate"] = stats["wins"] / valid_games
                stats["draw_rate"] = stats["draws"] / valid_games
                stats["error_rate"] = stats["errors"] / num_games if num_games > 0 else 0
                stats["bankruptcy_rate"] = stats["bankruptcies"] / valid_games
                stats["survival_rate"] = 1.0 - stats["bankruptcy_rate"]
                
                # Average stats
                stats["avg_properties_owned"] /= valid_games
                stats["avg_monopolies_owned"] /= valid_games
                stats["avg_houses_built"] /= valid_games
                stats["avg_hotels_built"] /= valid_games
                stats["avg_final_cash"] /= valid_games
                stats["avg_final_net_worth"] /= valid_games
                
                # Calculate development rate (houses+hotels per property)
                if stats["avg_properties_owned"] > 0:
                    stats["development_rate"] = (stats["avg_houses_built"] + 
                                               stats["avg_hotels_built"] * 5) / stats["avg_properties_owned"]
                
                # Normalize property group preferences
                total_properties = sum(stats["property_group_preferences"].values())
                if total_properties > 0:
                    for group in stats["property_group_preferences"]:
                        stats["property_group_preferences"][group] /= total_properties
            else:
                # If all games had errors, set rates to 0
                stats["win_rate"] = 0
                stats["draw_rate"] = 0
    
    def _compute_matchup_statistics(self, tournament_results: Dict[str, Any]) -> None:
        """
        Compute head-to-head statistics for player matchups in 2-player tournaments.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        player_names = tournament_results["players"]
        
        # Initialize matchup statistics
        matchup_stats = {}
        for p1 in player_names:
            for p2 in player_names:
                if p1 != p2:
                    # Use string key instead of tuple
                    matchup_key = f"{p1}_vs_{p2}" if p1 < p2 else f"{p2}_vs_{p1}"
                    if matchup_key not in matchup_stats:
                        matchup_stats[matchup_key] = {
                            "games_played": 0,
                            "draws": 0,
                            "errors": 0,
                            "by_player": {
                                p1: {"wins": 0, "bankrupt": 0, "avg_net_worth": 0},
                                p2: {"wins": 0, "bankrupt": 0, "avg_net_worth": 0}
                            }
                        }
        
        # Collect stats from each game
        for game in tournament_results["games"]:
            if "matchup" not in game:
                continue
                
            player1, player2 = game["matchup"]
            
            # Create string key
            matchup_key = f"{player1}_vs_{player2}" if player1 < player2 else f"{player2}_vs_{player1}"
            
            if matchup_key not in matchup_stats:
                continue
                
            # Update matchup stats
            matchup_stats[matchup_key]["games_played"] += 1
            
            # Handle errors
            if "error" in game:
                matchup_stats[matchup_key]["errors"] += 1
                continue
                
            # Handle draws
            if game.get("is_draw", False):
                matchup_stats[matchup_key]["draws"] += 1
                continue
                
            # Handle wins and bankruptcies
            winner = game.get("winner")
            if winner:
                matchup_stats[matchup_key]["by_player"][winner]["wins"] += 1
            
            # Update other stats
            for player_name in [player1, player2]:
                if player_name in game["player_stats"]:
                    player_game_stats = game["player_stats"][player_name]
                    
                    if player_game_stats.get("went_bankrupt", False):
                        matchup_stats[matchup_key]["by_player"][player_name]["bankrupt"] += 1
                    
                    matchup_stats[matchup_key]["by_player"][player_name]["avg_net_worth"] += (
                        player_game_stats.get("final_net_worth", 0)
                    )
        
        # Calculate averages and rates
        for matchup_key, stats in matchup_stats.items():
            valid_games = stats["games_played"] - stats["errors"]
            
            if valid_games > 0:
                # Calculate win rates and averages for each player
                for player_name, player_stats in stats["by_player"].items():
                    player_stats["win_rate"] = player_stats["wins"] / valid_games
                    player_stats["bankrupt_rate"] = player_stats["bankrupt"] / valid_games
                    player_stats["avg_net_worth"] /= valid_games
        
        # Store matchup statistics
        tournament_results["matchup_stats"] = matchup_stats
    
    def _compute_overall_statistics(self, tournament_results: Dict[str, Any]) -> None:
        """
        Compute overall tournament statistics.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        num_games = len(tournament_results["games"])
        
        # Calculate overall game statistics
        overall_stats = {
            "avg_game_duration": sum(game.get("turn_count", 0) for game in tournament_results["games"] 
                                   if "error" not in game) / 
                           max(1, sum(1 for game in tournament_results["games"] if "error" not in game)),
            "max_game_duration": max((game.get("turn_count", 0) for game in tournament_results["games"] 
                                    if "error" not in game), default=0),
            "min_game_duration": min((game.get("turn_count", 0) for game in tournament_results["games"] 
                                    if "error" not in game), default=0),
            "max_turns_reached_rate": sum(1 for game in tournament_results["games"] 
                                       if game.get("max_turns_reached", False)) / max(1, num_games),
            "draw_rate": tournament_results.get("draws", 0) / max(1, num_games),
            "error_rate": tournament_results.get("errors", 0) / max(1, num_games),
            "player_rankings": self._rank_players(tournament_results)
        }
        
        tournament_results["overall_stats"] = overall_stats

    def _generate_metrics_explanation(self, tournament_results: Dict[str, Any]) -> None:
        """
        Generate a comprehensive explanation of all metrics used in the tournament analysis.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        plt.figure(figsize=(14, 20))
        
        # Create a plot with no data, just for the text
        plt.axis('off')
        
        metrics_explanation = [
            ("Win Rate", "Percentage of games won by a player out of all valid games. A valid game is one that completed without errors."),
            ("Draw Rate", "Percentage of games that ended in a draw. A draw occurs when two or more players have the exact same net worth at the end of the maximum number of turns."),
            ("Error Rate", "Percentage of games that encountered an error during execution. These games are excluded from most statistics calculations."),
            ("Survival Rate", "Percentage of games where the player did not go bankrupt. Equal to (1 - Bankruptcy Rate)."),
            ("Bankruptcy Rate", "Percentage of games where the player went bankrupt. A player goes bankrupt when they cannot pay a debt."),
            ("Average Properties Owned", "Average number of properties owned by the player at the end of the game."),
            ("Average Monopolies Owned", "Average number of complete property sets (monopolies) owned by the player at the end of the game."),
            ("Average Houses Built", "Average number of houses built by the player across all games."),
            ("Average Hotels Built", "Average number of hotels built by the player across all games."),
            ("Average Final Cash", "Average amount of cash the player had at the end of the game."),
            ("Average Final Net Worth", "Average total value of the player at the end of the game, including cash, property value, and building value."),
            ("Development Rate", "Ratio of development (houses and hotels) to owned properties. Formula: (houses + hotels*5) / properties. Higher values indicate more aggressive development."),
            ("Property Group Preferences", "Distribution of properties by color group, showing which property groups the player tends to acquire."),
            ("Head-to-Head Win Rate", "In 2-player tournaments, the percentage of games a player wins against a specific opponent."),
        ]
        
        # Add title
        plt.text(0.5, 0.98, "MONOPOLY TOURNAMENT METRICS EXPLANATION", 
                horizontalalignment='center', fontsize=18, fontweight='bold')
        
        # Add introduction
        intro_text = (
            "This document explains the metrics used to evaluate player performance in the Monopoly tournament. " +
            "Understanding these metrics will help interpret the results and charts generated by the tournament manager."
        )
        plt.text(0.5, 0.94, intro_text, horizontalalignment='center', fontsize=12, wrap=True)
        
        # Add each metric with explanation
        y_pos = 0.90
        for i, (metric, explanation) in enumerate(metrics_explanation):
            # Metric name
            plt.text(0.05, y_pos, f"{i+1}. {metric}", fontsize=14, fontweight='bold')
            y_pos -= 0.02
            
            # Metric explanation (with word wrapping)
            wrapped_explanation = explanation
            plt.text(0.07, y_pos, wrapped_explanation, fontsize=12, wrap=True)
            y_pos -= 0.04
        
        # Add note about overall ranking
        ranking_note = (
            "Overall Player Ranking: Players are ranked based on a weighted combination of the above metrics. " +
            "Win rate has the highest weight (3x), followed by net worth (2x), and then survival rate and development rate (1x each). " +
            "The final ranking score is the sum of these weighted values."
        )
        plt.text(0.05, y_pos, "Note on Overall Ranking:", fontsize=14, fontweight='bold')
        y_pos -= 0.02
        plt.text(0.07, y_pos, ranking_note, fontsize=12, wrap=True)
        
        # Save the figure to a file
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # Make room for title
        plt.savefig(os.path.join(self.output_dir, "explanations", f"{self.tournament_id}_metrics_explanation.png"), 
                   dpi=100, bbox_inches='tight')
        plt.close()
    
    def _rank_players(self, tournament_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Rank players based on various metrics.
        
        Args:
            tournament_results: Tournament results dictionary
            
        Returns:
            List of player rankings
        """
        player_names = tournament_results["players"]
        
        # Rank players by different metrics
        rankings = []
        
        # Win rate ranking
        win_ranking = sorted(
            [(name, tournament_results["player_stats"][name]["win_rate"]) for name in player_names],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Net worth ranking
        networth_ranking = sorted(
            [(name, tournament_results["player_stats"][name]["avg_final_net_worth"]) for name in player_names],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Survival rate ranking
        survival_ranking = sorted(
            [(name, tournament_results["player_stats"][name]["survival_rate"]) for name in player_names],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Development rate ranking
        development_ranking = sorted(
            [(name, tournament_results["player_stats"][name]["development_rate"]) for name in player_names],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Calculate overall ranking (weighted average of ranks)
        overall_scores = {name: 0 for name in player_names}
        
        # Assign scores based on rankings (higher rank = higher score)
        # Win rate has highest weight
        for i, (name, _) in enumerate(win_ranking):
            overall_scores[name] += (len(player_names) - i) * 3  # Weight of 3
            
        # Net worth has second highest weight
        for i, (name, _) in enumerate(networth_ranking):
            overall_scores[name] += (len(player_names) - i) * 2  # Weight of 2
            
        # Survival and development rates have equal weights
        for i, (name, _) in enumerate(survival_ranking):
            overall_scores[name] += (len(player_names) - i)  # Weight of 1
            
        for i, (name, _) in enumerate(development_ranking):
            overall_scores[name] += (len(player_names) - i)  # Weight of 1
        
        # Create final ranking
        overall_ranking = sorted(
            [(name, score) for name, score in overall_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Format rankings for output
        rankings = [
            {
                "player": name,
                "overall_score": score,
                "win_rate": tournament_results["player_stats"][name]["win_rate"],
                "draw_rate": tournament_results["player_stats"][name]["draw_rate"],
                "error_rate": tournament_results["player_stats"][name]["error_rate"],
                "avg_net_worth": tournament_results["player_stats"][name]["avg_final_net_worth"],
                "survival_rate": tournament_results["player_stats"][name]["survival_rate"],
                "development_rate": tournament_results["player_stats"][name]["development_rate"]
            }
            for name, score in overall_ranking
        ]
        
        return rankings
    
    def _save_tournament_results(self, tournament_results: Dict[str, Any]) -> None:
        """
        Save tournament results to a JSON file.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        # Create a filename with the tournament ID
        filename = f"tournament_{self.tournament_id}.json"
        filepath = os.path.join(self.output_dir, "json", filename)
        
        # Prepare a simplified version for JSON export
        json_results = tournament_results.copy()
        
        # Simplify game results to reduce file size
        simplified_games = []
        for game in json_results["games"]:
            simplified_game = {
                "game_index": game["game_index"],
                "players": game["players"],
                "turn_count": game.get("turn_count", 0),
                "winner": game.get("winner"),
                "is_draw": game.get("is_draw", False),
                "bankrupt_players": game.get("bankrupt_players", []),
                "error": game.get("error", None)
            }
            
            # Only include matchup info for 2-player tournaments
            if "matchup" in game:
                simplified_game["matchup"] = game["matchup"]
                
            # Only include final net worth for each player
            if "final_state" in game:
                simplified_game["player_net_worth"] = game["final_state"].get("player_net_worth", {})
                
            simplified_games.append(simplified_game)
            
        json_results["games"] = simplified_games
        
        # Save results to file
        with open(filepath, 'w') as f:
            json.dump(json_results, f, indent=2)
    
    def _generate_visualizations(self, tournament_results: Dict[str, Any]) -> None:
        """
        Generate visualizations from tournament results.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        print("Generating visualizations...")
        
        # Set up plot style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Win rates comparison
        self._plot_win_rates(tournament_results)
        
        # 2. Bankruptcy rates comparison
        self._plot_bankruptcy_rates(tournament_results)
        
        # 3. Property acquisition comparison
        self._plot_property_acquisition(tournament_results)
        
        # 4. Development rate comparison
        self._plot_development_rates(tournament_results)
        
        # 5. Net worth comparison
        self._plot_net_worth(tournament_results)
        
        # 6. Property group preferences
        self._plot_property_group_preferences(tournament_results)
        
        # 7. Overall rankings
        self._plot_overall_rankings(tournament_results)
        
        # 8. Game duration distribution
        self._plot_game_duration(tournament_results)
        
        # 9. Performance radar chart
        self._plot_performance_radar(tournament_results)
        
        # 10. If turn data is available, plot progression graphs
        if tournament_results["games"] and tournament_results["games"][0].get("turn_data"):
            self._plot_performance_over_time(tournament_results)
            
        # 11. Draw and error rates
        self._plot_draw_error_rates(tournament_results)
    
    def _generate_2player_visualizations(self, tournament_results: Dict[str, Any]) -> None:
        """
        Generate visualizations specific to 2-player tournament results.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        # Generate standard visualizations first
        self._generate_visualizations(tournament_results)
        
        # Add matchup-specific visualizations
        self._plot_matchup_win_rates(tournament_results)
        self._plot_matchup_matrix(tournament_results)
        
        # Create player-specific matchup folders and organize visualizations
        self._organize_matchup_visualizations(tournament_results)
    
    def _organize_matchup_visualizations(self, tournament_results: Dict[str, Any]) -> None:
        """
        Organize matchup visualizations into player-specific folders for easier access.
        
        Args:
            tournament_results: Tournament results dictionary
        """
        if "matchup_stats" not in tournament_results:
            return
            
        player_names = tournament_results["players"]
        
        # Create player-specific folders within matchups folder
        for player_name in player_names:
            player_folder = os.path.join(self.output_dir, "matchups", player_name)
            os.makedirs(player_folder, exist_ok=True)
            
    def _plot_win_rates(self, tournament_results: Dict[str, Any]) -> None:
        """Plot win rates for each player, including draws and errors."""
        plt.figure(figsize=(14, 8))
        
        player_names = tournament_results["players"]
        win_rates = [tournament_results["player_stats"][name]["win_rate"] for name in player_names]
        draw_rates = [tournament_results["player_stats"][name]["draw_rate"] for name in player_names]
        error_rates = [tournament_results["player_stats"][name]["error_rate"] for name in player_names]
        
        # Calculate total rates accounting for draws and errors
        totals = [win + draw + error for win, draw, error in zip(win_rates, draw_rates, error_rates)]
        
        # Create bar positions
        x = np.arange(len(player_names))
        width = 0.8
        
        # Create stacked bars
        fig, ax = plt.subplots(figsize=(14, 8))
        error_bars = ax.bar(x, error_rates, width, label='Errors', color='#e74c3c')
        draw_bars = ax.bar(x, draw_rates, width, bottom=error_rates, label='Draws', color='#f39c12')
        win_bars = ax.bar(x, win_rates, width, bottom=[e+d for e, d in zip(error_rates, draw_rates)], 
                         label='Wins', color='#2ecc71')
        
        ax.set_title("Outcome Rates by Player", fontsize=16)
        ax.set_ylabel("Rate", fontsize=12)
        ax.set_xlabel("Player", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(player_names, rotation=45, ha="right")
        ax.legend()
        
        # Add value labels on bars for all players
        def add_labels(bars, rates, offsets=None):
            if offsets is None:
                offsets = [0] * len(bars)
                
            for i, (bar, rate, offset) in enumerate(zip(bars, rates, offsets)):
                if rate > 0:  # Only add labels for rates > 0
                    height = bar.get_height()
                    y_pos = bar.get_y() + height/2 + offset
                    ax.text(bar.get_x() + bar.get_width()/2., y_pos, f'{rate:.1%}',
                           ha='center', va='center', fontsize=10, color='white', fontweight='bold')
        
        # Get bottom positions for win bars to place the text properly
        win_bottoms = [e+d for e, d in zip(error_rates, draw_rates)]
        
        # Add labels for all bars with appropriate positioning
        add_labels(win_bars, win_rates, [0.01 * max(win_rates) for _ in win_rates])
        add_labels(draw_bars, draw_rates)
        add_labels(error_bars, error_rates)
        
        plt.tight_layout()
        
        # Save to main directory as the key visualization
        plt.savefig(os.path.join(self.output_dir, f"{self.tournament_id}_win_rates.png"))
        
        # Also save to comparison_metrics folder
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_win_rates.png"))
        
        plt.close()
    
    def _plot_bankruptcy_rates(self, tournament_results: Dict[str, Any]) -> None:
        """Plot bankruptcy rates for each player."""
        plt.figure(figsize=(10, 6))
        
        player_names = tournament_results["players"]
        bankruptcy_rates = [tournament_results["player_stats"][name]["bankruptcy_rate"] 
                          for name in player_names]
        
        bars = plt.bar(player_names, bankruptcy_rates, color=plt.cm.viridis(np.linspace(0, 1, len(player_names))))
        
        plt.title("Bankruptcy Rates by Player", fontsize=16)
        plt.ylabel("Bankruptcy Rate", fontsize=12)
        plt.xlabel("Player", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        plt.ylim(0, max(bankruptcy_rates) * 1.2 if max(bankruptcy_rates) > 0 else 0.1)
        
        # Add value labels on all bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2%}',
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_bankruptcy_rates.png"))
        plt.close()
    
    def _plot_property_acquisition(self, tournament_results: Dict[str, Any]) -> None:
        """Plot average properties owned and monopolies formed."""
        plt.figure(figsize=(12, 6))
        
        player_names = tournament_results["players"]
        avg_properties = [tournament_results["player_stats"][name]["avg_properties_owned"] 
                        for name in player_names]
        avg_monopolies = [tournament_results["player_stats"][name]["avg_monopolies_owned"] 
                        for name in player_names]
        
        x = np.arange(len(player_names))
        width = 0.35
        
        bars1 = plt.bar(x - width/2, avg_properties, width, label='Avg. Properties Owned', color='#3498db')
        bars2 = plt.bar(x + width/2, avg_monopolies, width, label='Avg. Monopolies Formed', color='#2ecc71')
        
        plt.title("Property Acquisition by Player", fontsize=16)
        plt.ylabel("Average Count per Game", fontsize=12)
        plt.xlabel("Player", fontsize=12)
        plt.xticks(x, player_names, rotation=45, ha="right")
        plt.legend()
        
        # Add value labels on all bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_property_acquisition.png"))
        plt.close()
    
    def _plot_development_rates(self, tournament_results: Dict[str, Any]) -> None:
        """Plot development metrics (houses, hotels, development rate)."""
        plt.figure(figsize=(12, 6))
        
        player_names = tournament_results["players"]
        avg_houses = [tournament_results["player_stats"][name]["avg_houses_built"] for name in player_names]
        avg_hotels = [tournament_results["player_stats"][name]["avg_hotels_built"] for name in player_names]
        dev_rates = [tournament_results["player_stats"][name]["development_rate"] for name in player_names]
        
        x = np.arange(len(player_names))
        width = 0.25
        
        bars1 = plt.bar(x - width, avg_houses, width, label='Avg. Houses Built', color='#3498db')
        bars2 = plt.bar(x, avg_hotels, width, label='Avg. Hotels Built', color='#e74c3c')
        bars3 = plt.bar(x + width, dev_rates, width, label='Development Rate', color='#2ecc71')
        
        plt.title("Property Development by Player", fontsize=16)
        plt.ylabel("Count / Rate", fontsize=12)
        plt.xlabel("Player", fontsize=12)
        plt.xticks(x, player_names, rotation=45, ha="right")
        plt.legend()
        
        # Add value labels on all bars
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                        f'{height:.1f}',
                        ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_development_rates.png"))
        plt.close()
    
    def _plot_net_worth(self, tournament_results: Dict[str, Any]) -> None:
        """Plot average final net worth."""
        plt.figure(figsize=(10, 6))
        
        player_names = tournament_results["players"]
        avg_net_worth = [tournament_results["player_stats"][name]["avg_final_net_worth"] 
                       for name in player_names]
        avg_cash = [tournament_results["player_stats"][name]["avg_final_cash"] 
                  for name in player_names]
        
        x = np.arange(len(player_names))
        width = 0.35
        
        bars1 = plt.bar(x - width/2, avg_net_worth, width, label='Avg. Final Net Worth', color='#3498db')
        bars2 = plt.bar(x + width/2, avg_cash, width, label='Avg. Final Cash', color='#2ecc71')
        
        plt.title("Financial Performance by Player", fontsize=16)
        plt.ylabel("Average Amount ($)", fontsize=12)
        plt.xlabel("Player", fontsize=12)
        plt.xticks(x, player_names, rotation=45, ha="right")
        plt.legend()
        
        # Add value labels on all bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height + 50,
                        f'${int(height)}',
                        ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_net_worth.png"))
        plt.close()
    
    def _plot_property_group_preferences(self, tournament_results: Dict[str, Any]) -> None:
        """Plot property group preferences."""
        plt.figure(figsize=(14, 8))
        
        player_names = tournament_results["players"]
        
        # Get all unique property groups
        all_groups = set()
        for player_name in player_names:
            all_groups.update(tournament_results["player_stats"][player_name]["property_group_preferences"].keys())
        all_groups = sorted(list(all_groups))
        
        # Create a data matrix for the heatmap
        data = []
        for player_name in player_names:
            player_prefs = tournament_results["player_stats"][player_name]["property_group_preferences"]
            player_data = [player_prefs.get(group, 0) for group in all_groups]
            data.append(player_data)
        
        # Create DataFrame for the heatmap
        df = pd.DataFrame(data, index=player_names, columns=all_groups)
        
        # Plot heatmap
        plt.figure(figsize=(14, 8))
        sns.heatmap(df, cmap="YlGnBu", annot=True, fmt=".2f", linewidths=.5)
        
        plt.title("Property Group Preferences by Player", fontsize=16)
        plt.ylabel("Player", fontsize=12)
        plt.xlabel("Property Group", fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_property_preferences.png"))
        plt.close()
    
    def _plot_overall_rankings(self, tournament_results: Dict[str, Any]) -> None:
        """Plot overall player rankings."""
        rankings = tournament_results["overall_stats"]["player_rankings"]
        
        plt.figure(figsize=(12, 6))
        
        player_names = [r["player"] for r in rankings]
        overall_scores = [r["overall_score"] for r in rankings]
        
        bars = plt.bar(player_names, overall_scores, color=plt.cm.viridis(np.linspace(0, 1, len(player_names))))
        
        plt.title("Overall Player Rankings", fontsize=16)
        plt.ylabel("Ranking Score", fontsize=12)
        plt.xlabel("Player", fontsize=12)
        plt.xticks(rotation=45, ha="right")
        
        # Add value labels on all bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_overall_rankings.png"))
        plt.close()
        
        # Also create a table visualization of rankings
        plt.figure(figsize=(14, 7))
        
        # Create data for table
        table_data = [
            [r["player"], 
             f"{r['win_rate']:.2%}", 
             f"{r['draw_rate']:.2%}", 
             f"{r['error_rate']:.2%}",
             f"{r['survival_rate']:.2%}", 
             f"${int(r['avg_net_worth'])}", 
             f"{r['development_rate']:.2f}"] 
            for r in rankings
        ]
        
        # Create table
        table = plt.table(
            cellText=table_data,
            colLabels=["Player", "Win Rate", "Draw Rate", "Error Rate", "Survival Rate", 
                     "Avg Net Worth", "Development Rate"],
            loc='center',
            cellLoc='center',
            colWidths=[0.15, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12]
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Add ranking numbers
        for i in range(len(rankings)):
            plt.text(0.05, 0.87 - i * 0.048, f"{i+1}.", transform=plt.gcf().transFigure)
        
        plt.axis('off')
        plt.title("Detailed Player Rankings", fontsize=16)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_ranking_table.png"))
        plt.close()
        
        # If we have top two players, create a special comparison
        if len(rankings) >= 2:
            self._plot_top_players_comparison(tournament_results, rankings[0]["player"], rankings[1]["player"])
    
    def _plot_top_players_comparison(self, tournament_results: Dict[str, Any], player1: str, player2: str) -> None:
        """
        Create a special comparison of the top two players.
        
        Args:
            tournament_results: Tournament results dictionary
            player1: Name of the first player
            player2: Name of the second player
        """
        plt.figure(figsize=(10, 8))
        
        # Get stats for both players
        p1_stats = tournament_results["player_stats"][player1]
        p2_stats = tournament_results["player_stats"][player2]
        
        # Choose key metrics for comparison
        metrics = [
            "win_rate", 
            "draw_rate",
            "survival_rate", 
            "development_rate",
            "avg_properties_owned", 
            "avg_monopolies_owned",
            "avg_houses_built",
            "avg_hotels_built"
        ]
        
        metric_labels = [
            "Win Rate", 
            "Draw Rate",
            "Survival Rate", 
            "Development Rate",
            "Avg Properties", 
            "Avg Monopolies",
            "Avg Houses",
            "Avg Hotels"
        ]
        
        # Normalize each metric to a 0-1 scale for comparison
        p1_values = []
        p2_values = []
        
        for metric in metrics:
            # Handle special metrics differently
            if metric in ["win_rate", "draw_rate", "survival_rate"]:
                # These are already between 0-1
                p1_values.append(p1_stats[metric])
                p2_values.append(p2_stats[metric])
            elif metric == "development_rate":
                # Normalize to max of 5
                p1_values.append(min(1.0, p1_stats[metric] / 5))
                p2_values.append(min(1.0, p2_stats[metric] / 5))
            elif metric == "avg_properties_owned":
                # Normalize to max of 28 properties
                p1_values.append(min(1.0, p1_stats[metric] / 28))
                p2_values.append(min(1.0, p2_stats[metric] / 28))
            elif metric == "avg_monopolies_owned":
                # Normalize to max of 8 monopolies
                p1_values.append(min(1.0, p1_stats[metric] / 8))
                p2_values.append(min(1.0, p2_stats[metric] / 8))
            elif metric == "avg_houses_built":
                # Normalize to max of 32 houses
                p1_values.append(min(1.0, p1_stats[metric] / 32))
                p2_values.append(min(1.0, p2_stats[metric] / 32))
            elif metric == "avg_hotels_built":
                # Normalize to max of 12 hotels
                p1_values.append(min(1.0, p1_stats[metric] / 12))
                p2_values.append(min(1.0, p2_stats[metric] / 12))
        
        # Plot comparison
        x = np.arange(len(metrics))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(12, 6))
        bars1 = ax.bar(x - width/2, p1_values, width, label=player1, color='#3498db')
        bars2 = ax.bar(x + width/2, p2_values, width, label=player2, color='#2ecc71')
        
        ax.set_title(f"Top Players Comparison: {player1} vs {player2}", fontsize=16)
        ax.set_ylabel("Normalized Score", fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(metric_labels, rotation=45, ha="right")
        ax.legend()
        
        # Add absolute value labels
        def get_original_value(player_stats, metric):
            if metric in ["win_rate", "draw_rate", "survival_rate"]:
                return f"{player_stats[metric]:.2%}"
            elif metric == "development_rate":
                return f"{player_stats[metric]:.2f}"
            else:
                return f"{player_stats[metric]:.1f}"
        
        for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
            metric = metrics[i]
            # Player 1 value
            ax.text(
                bar1.get_x() + bar1.get_width()/2, 
                bar1.get_height() + 0.05,
                get_original_value(p1_stats, metric),
                ha='center', va='bottom', fontsize=8
            )
            # Player 2 value
            ax.text(
                bar2.get_x() + bar2.get_width()/2, 
                bar2.get_height() + 0.05,
                get_original_value(p2_stats, metric),
                ha='center', va='bottom', fontsize=8
            )
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, f"{self.tournament_id}_top_players_comparison.png"))
        plt.close()
    
    def _plot_game_duration(self, tournament_results: Dict[str, Any]) -> None:
        """Plot distribution of game durations."""
        plt.figure(figsize=(10, 6))
        
        game_durations = [game.get("turn_count", 0) for game in tournament_results["games"] 
                        if "error" not in game]
        
        if not game_durations:  # Skip if no valid games
            return
            
        plt.hist(game_durations, bins=20, color='#3498db', alpha=0.7)
        
        avg_duration = tournament_results["overall_stats"]["avg_game_duration"]
        plt.axvline(x=avg_duration, color='#e74c3c', linestyle='--', 
                   label=f'Average: {avg_duration:.1f} turns')
        
        plt.title("Distribution of Game Durations", fontsize=16)
        plt.ylabel("Number of Games", fontsize=12)
        plt.xlabel("Number of Turns", fontsize=12)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", f"{self.tournament_id}_game_durations.png"))
        plt.close()
    
    def _plot_performance_radar(self, tournament_results: Dict[str, Any]) -> None:
        """Create radar charts for player performance metrics."""
        player_names = tournament_results["players"]
        
        # Define metrics for radar chart
        metrics = [
            "Win Rate", 
            "Survival Rate", 
            "Development Rate", 
            "Avg Properties", 
            "Avg Monopolies",
            "Net Worth"
        ]
        
        # Create radar chart for each player
        for player_name in player_names:
            stats = tournament_results["player_stats"][player_name]
            
            # Normalize metrics between 0 and 1 for radar chart
            win_rate = stats["win_rate"]
            survival_rate = stats["survival_rate"]
            development_rate = stats["development_rate"] / 5  # Normalize, assuming max is 5
            avg_properties = stats["avg_properties_owned"] / 28  # Normalize, assuming max is 28
            avg_monopolies = stats["avg_monopolies_owned"] / 8  # Normalize, assuming max is 8
            
            # Normalize net worth
            max_net_worth = max(tournament_results["player_stats"][p]["avg_final_net_worth"] 
                              for p in player_names)
            net_worth = stats["avg_final_net_worth"] / max_net_worth if max_net_worth > 0 else 0
            
            # Plot radar chart
            plt.figure(figsize=(8, 8))
            
            # Create the chart
            angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
            values = [win_rate, survival_rate, development_rate, avg_properties, avg_monopolies, net_worth]
            values += values[:1]  # Close the loop
            angles += angles[:1]  # Close the loop
            
            ax = plt.subplot(111, polar=True)
            plt.xticks(angles[:-1], metrics, fontsize=12)
            
            ax.plot(angles, values, 'o-', linewidth=2, color='#3498db')
            ax.fill(angles, values, alpha=0.25, color='#3498db')
            
            # Add value labels
            for angle, value, metric in zip(angles[:-1], values[:-1], metrics):
                if metric == "Win Rate" or metric == "Survival Rate":
                    label = f"{value:.2%}"
                elif metric == "Net Worth":
                    label = f"${int(value * max_net_worth)}" if max_net_worth > 0 else "$0"
                else:
                    label = f"{value:.2f}"
                
                plt.text(angle, value + 0.1, label, ha='center', va='center')
            
            # Configure radar chart
            ax.set_rlabel_position(0)
            plt.yticks([0.2, 0.4, 0.6, 0.8, 1.0], ["0.2", "0.4", "0.6", "0.8", "1.0"], 
                      color="grey", size=10)
            plt.ylim(0, 1)
            
            plt.title(f"Performance Metrics: {player_name}", fontsize=16, y=1.08)
            
            plt.tight_layout()
            
            # Save to player metrics folder
            plt.savefig(os.path.join(self.output_dir, "player_metrics", 
                                   f"{self.tournament_id}_{player_name}_radar.png"))
            plt.close()
    
    def _plot_performance_over_time(self, tournament_results: Dict[str, Any]) -> None:
        """Plot player performance metrics over time (turns)."""
        player_names = tournament_results["players"]
        
        # Collect time series data from turn_data
        # We'll use a sample of games for this analysis
        valid_games = [g for g in tournament_results["games"] if "error" not in g and "turn_data" in g]
        sample_size = min(10, len(valid_games))
        sample_games = valid_games[:sample_size]
        
        if not sample_games:  # Skip if no valid games
            return
            
        # Track metrics over time
        time_series_data = {
            player_name: {
                "cash": [],
                "net_worth": [],
                "properties": [],
                "houses": [],
                "hotels": [],
                "turns": []
            }
            for player_name in player_names
        }
        
        # Maximum turn count across sample games
        max_turns = max(len(game["turn_data"]) for game in sample_games)
        
        # For each turn, average the metrics across sample games
        for turn in range(max_turns):
            turn_values = {
                player_name: {
                    "cash": [],
                    "net_worth": [],
                    "properties": [],
                    "houses": [],
                    "hotels": []
                }
                for player_name in player_names
            }
            
            # Collect values for this turn from all sample games
            for game in sample_games:
                if turn < len(game["turn_data"]):
                    turn_data = game["turn_data"][turn]
                    for player_name in player_names:
                        if player_name in turn_data["player_data"]:
                            player_data = turn_data["player_data"][player_name]
                            turn_values[player_name]["cash"].append(player_data["cash"])
                            turn_values[player_name]["net_worth"].append(player_data["net_worth"])
                            turn_values[player_name]["properties"].append(player_data["properties_count"])
                            turn_values[player_name]["houses"].append(player_data["houses"])
                            turn_values[player_name]["hotels"].append(player_data["hotels"])
            
            # Calculate averages for this turn
            for player_name in player_names:
                if turn_values[player_name]["cash"]:  # Check if we have data
                    time_series_data[player_name]["cash"].append(np.mean(turn_values[player_name]["cash"]))
                    time_series_data[player_name]["net_worth"].append(np.mean(turn_values[player_name]["net_worth"]))
                    time_series_data[player_name]["properties"].append(np.mean(turn_values[player_name]["properties"]))
                    time_series_data[player_name]["houses"].append(np.mean(turn_values[player_name]["houses"]))
                    time_series_data[player_name]["hotels"].append(np.mean(turn_values[player_name]["hotels"]))
                    time_series_data[player_name]["turns"].append(turn)
        
        # Plot the data
        self._plot_metric_over_time(time_series_data, "cash", "Cash Balance Over Time")
        self._plot_metric_over_time(time_series_data, "net_worth", "Net Worth Over Time")
        self._plot_metric_over_time(time_series_data, "properties", "Properties Owned Over Time")
        self._plot_combined_development_over_time(time_series_data)
    
    def _plot_metric_over_time(self, time_series_data, metric, title):
        """Plot a specific metric over time for all players."""
        plt.figure(figsize=(12, 6))
        
        for player_name, data in time_series_data.items():
            if data["turns"] and data[metric]:  # Check if we have data
                plt.plot(data["turns"], data[metric], label=player_name, linewidth=2)
        
        plt.title(title, fontsize=16)
        plt.xlabel("Turn", fontsize=12)
        plt.ylabel(metric.capitalize(), fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", 
                               f"{self.tournament_id}_{metric}_over_time.png"))
        plt.close()
    
    def _plot_combined_development_over_time(self, time_series_data):
        """Plot combined development (houses + hotels) over time."""
        plt.figure(figsize=(12, 6))
        
        for player_name, data in time_series_data.items():
            if data["turns"] and data["houses"] and data["hotels"]:  # Check if we have data
                # Convert hotels to equivalent houses (1 hotel = 5 houses) for visualization
                combined_development = [h + 5*ht for h, ht in zip(data["houses"], data["hotels"])]
                plt.plot(data["turns"], combined_development, label=player_name, linewidth=2)
        
        plt.title("Property Development Over Time", fontsize=16)
        plt.xlabel("Turn", fontsize=12)
        plt.ylabel("Development Level (Houses + 5×Hotels)", fontsize=12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", 
                               f"{self.tournament_id}_development_over_time.png"))
        plt.close()
    
    def _plot_draw_error_rates(self, tournament_results: Dict[str, Any]) -> None:
        """Plot draw and error rates."""
        overall_stats = tournament_results["overall_stats"]
        draw_rate = overall_stats.get("draw_rate", 0)
        error_rate = overall_stats.get("error_rate", 0)
        win_rate = 1.0 - draw_rate - error_rate
        
        # Skip if no draws or errors
        if draw_rate == 0 and error_rate == 0:
            return
            
        plt.figure(figsize=(8, 6))
        
        # Create a pie chart
        labels = ['Games with Winner', 'Draws', 'Errors']
        sizes = [win_rate, draw_rate, error_rate]
        explode = (0, 0.1, 0.1)  # Explode the draw and error slices
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        
        # Remove empty categories
        valid_data = [(label, size, exp, color) 
                    for label, size, exp, color in zip(labels, sizes, explode, colors) 
                    if size > 0]
        
        if not valid_data:  # Skip if no valid data
            return
            
        labels, sizes, explode, colors = zip(*valid_data)
        
        plt.pie(sizes, explode=explode, labels=labels, colors=colors,
              autopct='%1.1f%%', shadow=True, startangle=140)
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        
        plt.title("Game Outcome Distribution", fontsize=16)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", 
                               f"{self.tournament_id}_draw_error_rates.png"))
        plt.close()
    
    def _plot_matchup_win_rates(self, tournament_results: Dict[str, Any]) -> None:
        """Plot win rates for each matchup in 2-player tournaments."""
        if "matchup_stats" not in tournament_results:
            return
            
        # Ensure graphs directory exists
        os.makedirs(os.path.join(self.output_dir, "graphs"), exist_ok=True)
        
        matchup_stats = tournament_results["matchup_stats"]
        
        # Process each matchup
        for matchup_key, stats in matchup_stats.items():
            # Parse player names from the string key
            player_names = matchup_key.split("_vs_")
            if len(player_names) != 2:
                continue
                
            player1, player2 = player_names
            
            # Skip if no valid games
            valid_games = stats["games_played"] - stats["errors"]
            if valid_games == 0:
                continue
                
            plt.figure(figsize=(8, 6))
            
            # Extract stats
            p1_win_rate = stats["by_player"][player1]["win_rate"]
            p2_win_rate = stats["by_player"][player2]["win_rate"]
            draw_rate = stats["draws"] / valid_games
            
            # Create a pie chart
            labels = [f'{player1} Wins', f'{player2} Wins', 'Draws']
            sizes = [p1_win_rate, p2_win_rate, draw_rate]
            explode = (0.1, 0.1, 0)  # Explode the win slices
            colors = ['#3498db', '#2ecc71', '#f39c12']
            
            # Remove empty categories
            valid_data = [(label, size, exp, color) 
                        for label, size, exp, color in zip(labels, sizes, explode, colors) 
                        if size > 0]
            
            if not valid_data:  # Skip if no valid data
                continue
                
            labels, sizes, explode, colors = zip(*valid_data)
            
            plt.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)
            plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            plt.title(f"Matchup: {player1} vs {player2}", fontsize=16)
            plt.suptitle(f"Total Games: {valid_games}", fontsize=12)
            
            plt.tight_layout()
            
            # Save to graphs directory
            plt.savefig(os.path.join(self.output_dir, "graphs", 
                                f"{self.tournament_id}_matchup_{player1}_vs_{player2}.png"))
            
            # Also save directly to player matchup folders
            os.makedirs(os.path.join(self.output_dir, "matchups", player1), exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, "matchups", player2), exist_ok=True)
            
            plt.savefig(os.path.join(self.output_dir, "matchups", player1, f"vs_{player2}.png"))
            plt.savefig(os.path.join(self.output_dir, "matchups", player2, f"vs_{player1}.png"))
            
            plt.close()
    
    def _plot_matchup_matrix(self, tournament_results: Dict[str, Any]) -> None:
        """Plot a matchup matrix showing head-to-head win rates."""
        if "matchup_stats" not in tournament_results:
            return
            
        player_names = tournament_results["players"]
        num_players = len(player_names)
        
        # Create a matrix of win rates
        win_matrix = np.zeros((num_players, num_players))
        
        # Fill the matrix with win rates
        for i, player1 in enumerate(player_names):
            for j, player2 in enumerate(player_names):
                if i == j:
                    win_matrix[i, j] = np.nan  # Diagonal elements are NaN
                    continue
                    
                # Find the matchup using string key
                matchup_key = f"{player1}_vs_{player2}" if player1 < player2 else f"{player2}_vs_{player1}"
                
                if matchup_key in tournament_results["matchup_stats"]:
                    stats = tournament_results["matchup_stats"][matchup_key]
                    
                    valid_games = stats["games_played"] - stats["errors"]
                    if valid_games > 0:
                        # Get win rate of player1 against player2
                        win_matrix[i, j] = stats["by_player"][player1]["win_rate"]
        
        # Create a mask for the diagonal
        mask = np.zeros_like(win_matrix, dtype=bool)
        np.fill_diagonal(mask, True)
        
        # Plot heatmap
        plt.figure(figsize=(12, 10))
        sns.heatmap(win_matrix, annot=True, fmt=".2f", linewidths=.5, mask=mask,
                  xticklabels=player_names, yticklabels=player_names, cmap="YlGnBu")
        
        plt.title("Head-to-Head Win Rates", fontsize=16)
        plt.xlabel("Opponent", fontsize=12)
        plt.ylabel("Player", fontsize=12)
        
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, "comparison_metrics", 
                               f"{self.tournament_id}_matchup_matrix.png"))
        plt.close()
    
    def _count_player_houses(self, game_state: GameState, player: Player) -> int:
        """Count total houses owned by a player."""
        houses_count = 0
        for group in PropertyGroup:
            if group in game_state.houses and game_state.houses[group][1] == player:
                houses_count += game_state.houses[group][0]
        return houses_count
    
    def _count_player_hotels(self, game_state: GameState, player: Player) -> int:
        """Count total hotels owned by a player."""
        hotels_count = 0
        for group in PropertyGroup:
            if group in game_state.hotels and game_state.hotels[group][1] == player:
                hotels_count += game_state.hotels[group][0]
        return hotels_count
    
    def _count_player_monopolies(self, game_state: GameState, player: Player) -> int:
        """Count how many complete property groups (monopolies) a player owns."""
        monopoly_count = 0
        for group in PropertyGroup:
            group_properties = game_state.board.get_properties_by_group(group)
            if all(prop in game_state.properties[player] for prop in group_properties):
                monopoly_count += 1
        return monopoly_count