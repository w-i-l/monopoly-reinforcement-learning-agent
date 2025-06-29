import queue
import threading
import subprocess
import os
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from copy import deepcopy
from datetime import datetime as Date
from pathlib import Path
from pydantic import BaseModel

from game.game_state import GameState
from game.player import Player
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from models.trade_offer import TradeOffer
from utils.logger import ErrorLogger


class ServerProperty(BaseModel):
    id: int
    name: str


class HumanAgent(Player):
    """
    Human player agent that provides a web-based interface for Monopoly gameplay.
    
    This agent creates a FastAPI server to handle game decisions and optionally manages
    a React frontend for user interaction. It bridges the gap between the game engine
    and human players by providing RESTful API endpoints for all game decisions.
    
    The agent uses a queue-based system for decision handling, where the game engine
    waits for human input through the web interface. All standard Player methods are
    implemented to request decisions from the human player via HTTP requests.
    
    Key features:
    - RESTful API server for game state and decision handling
    - Queue-based decision system with blocking waits
    - Real-time event streaming to the frontend
    - Optional frontend process management
    - CORS-enabled for web interface integration
    - Comprehensive error handling and logging

    Attributes
    ----------
    port : int
        Port number for the FastAPI server
    frontend_port : int
        Port number for the React frontend development server
    auto_start_frontend : bool
        Whether to automatically start and manage the frontend process
    game_state : Optional[GameState]
        Current game state reference for API endpoints
    decision_queue : queue.Queue
        Queue for sending decision requests to the frontend
    response_queue : queue.Queue
        Queue for receiving decision responses from the frontend
    ui_event_queue : queue.Queue
        Queue for game events to be displayed in the UI
    server : FastAPI
        The FastAPI application instance
    server_thread : threading.Thread
        Thread running the FastAPI server
    frontend_process : Optional[subprocess.Popen]
        Process handle for the frontend development server
    """


    def __init__(self, name: str, port: int = 6060, frontend_port: int = 5173):
        """
        Initialize the human agent with web interface capabilities.
        
        Parameters
        ----------
        name : str
            Display name for this human player
        port : int, default 6060
            Port number for the FastAPI server hosting the game API
        frontend_port : int, default 5173
            Port number for the React frontend development server
        """

        super().__init__(name)
        self.port = port
        self.game_state = None
        self.frontend_port = frontend_port

        self.decision_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.ui_event_queue = queue.Queue(maxsize=100)
        
        self.game_result = {
            "game_ended": False,
            "winner": None,
            "bankrupt_players": [],
            "turn_count": 0,
            "is_draw": False,
            "max_turns_reached": False,
            "player_stats": {},
            "error": None
        }

        self.server = self._setup_server()
        self._start_server()
        self._start_frontend()


    def _setup_server(self) -> FastAPI:
        """
        Create and configure the FastAPI server with game endpoints.
        
        Sets up CORS middleware and defines API routes for game state access,
        decision handling, and event streaming.
        
        Returns
        -------
        FastAPI
            Configured FastAPI application instance
        """

        app = FastAPI()
        
        # Updated CORS middleware configuration
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],  # Explicitly allow Vite dev server
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"]
        )

        @app.get("/api/game-state")
        async def get_game_state():
            """Get current game state formatted for frontend display."""
            try:
                players = [{
                    "name": str(player),
                    "properties": [ServerProperty(id=p.id, name=p.name) for p in self.game_state.properties[player]],
                    "houses": self.game_state.get_houses_for_player(player),
                    "hotels": self.game_state.get_hotels_for_player(player),
                    "escape_jail_cards": self.game_state.escape_jail_cards[player],
                    "in_jail": self.game_state.in_jail[player],
                    "position": self.game_state.player_positions[player],
                    "balance": self.game_state.player_balances[player]
                } for player in self.game_state.players]
                
                owned_properties = [prop.id for prop in self.game_state.is_owned]
                mortgaged_properties = [prop.id for prop in self.game_state.mortgaged_properties]

                return {
                    'players': players,
                    'currentPlayer': self.game_state.current_player_index,
                    'ownedProperties': owned_properties,
                    'mortgagedProperties': mortgaged_properties
                }
            except Exception as e:
                ErrorLogger.log_error(e)
                raise HTTPException(status_code=500, detail=str(e))
            
        @app.post("/api/decision")
        async def make_decision(decision: dict):
            """Receive decision from frontend and forward to game engine."""
            try:
                self.response_queue.put(decision['choice'])
                return {"status": "success"}
            except Exception as e:
                ErrorLogger.log_error(e)
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/pending-decision")
        async def get_pending_decision():
            """Check for pending decisions that need human input."""
            try:
                decision_data = self.decision_queue.get_nowait()
                return decision_data
            except queue.Empty:
                return {"type": "none"}
            except Exception as e:
                ErrorLogger.log_error(e)
                raise HTTPException(status_code=500, detail=str(e))
            
        @app.get("/api/events")
        async def get_events():
            """Get all queued game events for display in the UI."""
            events = []
            try:
                # Get all events from queue without blocking
                while not self.ui_event_queue.empty():
                    events.append(self.ui_event_queue.get_nowait())
                return {"events": events}
            except Exception as e:
                from utils.logger import ErrorLogger
                ErrorLogger.log_error(e)
                return {"events": []}
            
        @app.get("/api/game-result")
        async def get_game_result():
            """API endpoint to get current game result status"""
            try:
                return self.game_result
            except Exception as e:
                ErrorLogger.log_error(e)
                raise HTTPException(status_code=500, detail=str(e))

        return app
    

    def set_game_ended(self, winner=None, bankrupt_players=None, turn_count=0, is_draw=False, max_turns_reached=False, error=None):
        """Update game result when game ends"""
        
        # Calculate final stats first
        final_stats = self._calculate_final_stats() if self.game_state else {}
        
        # Update winner status in player stats
        if winner and final_stats:
            for player_name in final_stats:
                final_stats[player_name]["is_winner"] = (player_name == winner)
        
        self.game_result.update({
            "game_ended": True,
            "winner": winner,
            "bankrupt_players": bankrupt_players or [],
            "turn_count": turn_count,
            "is_draw": is_draw,
            "max_turns_reached": max_turns_reached,
            "error": error,
            "player_stats": final_stats
        })


    def _calculate_final_stats(self):
        """Calculate final player statistics"""
        if not self.game_state:
            return {}
            
        stats = {}
        for player in self.game_state.players:
            player_name = player.name
            
            try:
                # Count monopolies
                monopolies = self._count_player_monopolies(player)
                
                # Count buildings
                houses, hotels = self._count_player_buildings(player)
                
                # Count mortgaged properties
                player_properties = self.game_state.properties.get(player, [])
                mortgaged = sum(1 for prop in player_properties 
                               if prop in self.game_state.mortgaged_properties)
                
                stats[player_name] = {
                    "final_cash": self.game_state.player_balances.get(player, 0),
                    "final_net_worth": self.game_state.get_player_net_worth(player),
                    "properties_owned": len(player_properties),
                    "monopolies_owned": monopolies,
                    "houses_built": houses,
                    "hotels_built": hotels,
                    "properties_mortgaged": mortgaged,
                    "is_winner": self.game_result.get("winner") == player_name,
                    "went_bankrupt": player_name in self.game_result.get("bankrupt_players", [])
                }
            except Exception as e:
                ErrorLogger.log_error(e)
                # Fallback stats if calculation fails
                stats[player_name] = {
                    "final_cash": self.game_state.player_balances.get(player, 0),
                    "final_net_worth": self.game_state.player_balances.get(player, 0),
                    "properties_owned": 0,
                    "monopolies_owned": 0,
                    "houses_built": 0,
                    "hotels_built": 0,
                    "properties_mortgaged": 0,
                    "is_winner": self.game_result.get("winner") == player_name,
                    "went_bankrupt": player_name in self.game_result.get("bankrupt_players", [])
                }
        
        return stats


    def _count_player_monopolies(self, player):
        """Count complete monopolies owned by player"""
        monopolies = 0
        player_properties = self.game_state.properties.get(player, [])
        property_groups = {}
        
        # Group properties by color
        for prop in player_properties:
            if hasattr(prop, 'group'):
                if prop.group not in property_groups:
                    property_groups[prop.group] = 0
                property_groups[prop.group] += 1
        
        # Check for complete groups
        for group, count in property_groups.items():
            try:
                group_properties = self.game_state.board.get_properties_by_group(group)
                if count == len(group_properties):
                    monopolies += 1
            except:
                pass  # Handle any errors in group checking
        
        return monopolies


    def _count_player_buildings(self, player):
        """Count houses and hotels owned by player"""
        houses = 0
        hotels = 0
        
        try:
            # Count houses
            for group, house_data in self.game_state.houses.items():
                if len(house_data) >= 2 and house_data[1] == player:
                    houses += house_data[0]
            
            # Count hotels
            for group, hotel_data in self.game_state.hotels.items():
                if len(hotel_data) >= 2 and hotel_data[1] == player:
                    hotels += hotel_data[0]
        except Exception as e:
            ErrorLogger.log_error(e)
        
        return houses, hotels


    def _start_server(self):
        """Start the FastAPI server in a separate thread."""
        def run_server():
            import uvicorn
            config = uvicorn.Config(self.server, host="127.0.0.1", port=self.port, log_level="error")
            server = uvicorn.Server(config)
            server.run()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_thread.join(timeout=1) # Wait for server to start
        print(f"\nServer started - http://127.0.0.1:{self.port}")


    def _get_project_root(self) -> Path:
        current_path = Path(__file__).resolve()  # Get the human_agent.py location
        # Go up until we find the src directory
        while current_path.name != "src" and current_path.parent != current_path:
            current_path = current_path.parent
        if current_path.name != "src":
            raise FileNotFoundError("Could not find src directory")
        return current_path.parent


    def _start_frontend(self):
        """
        Start the React frontend development server.
        
        Launches the frontend using npm run dev and waits for it to become available.
        
        Raises
        ------
        RuntimeError
            If the frontend fails to start or become available
        """
        try:
            project_root = self._get_project_root()
            frontend_dir = project_root / "frontend"
            components_dir = frontend_dir / "src" / "components"

            print(f"\nStarting frontend from directory: {frontend_dir}")

            # Verify frontend directory exists
            if not frontend_dir.exists():
                raise RuntimeError(f"Frontend directory not found at {frontend_dir}")

            # Verify package.json exists
            if not (frontend_dir / "package.json").exists():
                raise RuntimeError(f"package.json not found in {frontend_dir}")

            # Start npm process with output logging
            def log_output(process):
                while True:
                    output = process.stdout.readline()
                    if output:
                        print(f"Frontend output: {output.strip()}")
                    error = process.stderr.readline()
                    if error:
                        print(f"Frontend error: {error.strip()}")
                    if output == '' and error == '' and process.poll() is not None:
                        break

            print("Starting npm process...")
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev", "--", "--port", str(self.frontend_port)],
                cwd=str(frontend_dir),
                env={**os.environ, "VITE_PLAYER_PORT": str(self.port)},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )

            # Start output logging in a separate thread
            log_thread = threading.Thread(
                target=log_output,
                args=(self.frontend_process,),
                daemon=True
            )
            log_thread.start()

            # Wait for frontend to start
            print(f"Waiting for frontend to be available on port {self.frontend_port}...")
            for attempt in range(20):  # Increased timeout to 20 seconds
                if self.frontend_process.poll() is not None:
                    stdout, stderr = self.frontend_process.communicate()
                    raise RuntimeError(
                        f"Frontend process exited prematurely.\nStdout: {stdout}\nStderr: {stderr}"
                    )
                
                import requests
                try:
                    response = requests.get(f"http://localhost:{self.frontend_port}")
                    if response.status_code == 200:
                        print(f"Frontend successfully started on port {self.frontend_port}")
                        print(f"Frontend URL: http://localhost:{self.frontend_port}")
                        return
                    else:
                        print(f"Attempt {attempt + 1}: Got status code {response.status_code}")
                except requests.exceptions.ConnectionError:
                    print(f"Attempt {attempt + 1}: Connection refused")
                except Exception as e:
                    print(f"Attempt {attempt + 1}: Error checking frontend: {str(e)}")
                
                time.sleep(1)

            raise RuntimeError("Frontend server did not become available after 20 seconds")

        except Exception as e:
            ErrorLogger.log_error(e)
            # Cleanup if needed
            if hasattr(self, 'frontend_process') and self.frontend_process:
                self.frontend_process.kill()
                self.frontend_process.wait()
            raise RuntimeError(f"Frontend failed to start: {str(e)}")


    def __del__(self):
        if hasattr(self, 'frontend_process'):
            self.frontend_process.kill()  # Force kill instead of terminate
            self.frontend_process.wait()


    def _wait_for_decision(self, decision_type: str, data: dict = None) -> any:
        """
        Queue a decision request and wait for human response.
        
        Parameters
        ----------
        decision_type : str
            Type of decision being requested
        data : dict, optional
            Additional data context for the decision
            
        Returns
        -------
        any
            The decision response from the human player
        """

        self.decision_queue.put({
            "type": decision_type,
            "data": data
        })
        return self.response_queue.get()


    def should_buy_property(self, game_state: GameState, property: Tile) -> bool:
        if not (isinstance(property, Property) or isinstance(property, Railway) or isinstance(property, Utility)):
            return False
        
        if property in game_state.is_owned:
            return False

        try:
            data = {
                "property": str(property),
                "price": property.price if hasattr(property, 'price') else None,
                "balance": game_state.player_balances[self],
                "owned_properties": [str(p) for p in game_state.properties[self]]
            }
            return self._wait_for_decision("buy_property", data)
        except Exception as e:
            ErrorLogger.log_error(e)
            return False


    def get_upgrading_suggestions(self, game_state: GameState) -> List[PropertyGroup]:
        try:
            properties = game_state.properties[self]
            grouped_properties = {
                property.group: [] for property in properties 
                if isinstance(property, Property)
            }
            
            for property in properties:
               if isinstance(property, Property):   
                    grouped_properties[property.group].append(property)


            grouped_properties_copy = deepcopy(grouped_properties)
            for group in grouped_properties_copy:
                if len(grouped_properties[group]) != len(game_state.board.get_properties_by_group(group)) or\
                     game_state.hotels[group][0] > 0:
                    grouped_properties.pop(group)

            if not grouped_properties:
                return []

            data = {
                "grouped_properties": {
                    str(group): ([str(p) for p in props], len(props) * group.house_cost() if game_state.houses[group][0] < 4 else len(props) * group.hotel_cost())
                    for group, props in grouped_properties.items()
                },
                "balance": game_state.player_balances[self],
            }

            suggestions = self._wait_for_decision("upgrade_properties", data)
            return [PropertyGroup.init_from(group) for group in suggestions]
        except Exception as e:
            ErrorLogger.log_error(e)
            return []


    def get_mortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        try:
            properties = [p for p in game_state.properties[self] 
                        if p not in game_state.mortgaged_properties]
            
            properties = [p for p in properties 
                          if (isinstance(p, Property) and game_state.hotels[p.group][0] == 0 and game_state.houses[p.group][0] == 0)
                          or not isinstance(p, Property)]

            
            if not properties:
                return []
            
            data = {
                "properties": [str(p) for p in properties],
                "balance": game_state.player_balances[self],
                "mortgaged_properties": [
                    str(p) for p in game_state.mortgaged_properties
                ]
            }
            
            suggestions = self._wait_for_decision("mortgage_properties", data)
            return [
                next(p for p in properties if str(p) == prop_str)
                for prop_str in suggestions
            ]
        except Exception as e:
            ErrorLogger.log_error(e)
            return []
        

    def get_unmortgaging_suggestions(self, game_state: GameState) -> List[Tile]:
        try:
            properties = [p for p in game_state.properties[self] 
                        if p in game_state.mortgaged_properties]
            
            if not properties:
                return []
            
            data = {
                "properties": [str(p) for p in properties],
                "balance": game_state.player_balances[self]
            }
            
            suggestions = self._wait_for_decision("unmortgage_properties", data)
            if not suggestions:
                return []
            return [
                next(p for p in properties if str(p) == prop_str)
                for prop_str in suggestions
            ]
        except Exception as e:
            ErrorLogger.log_error(e)
            return []


    def should_pay_get_out_of_jail_fine(self, game_state: GameState) -> bool:
        try:
            data = {
                "balance": game_state.player_balances[self],
                "jail_fine": game_state.board.get_jail_fine()
            }
            return self._wait_for_decision("pay_jail_fine", data)
        except Exception as e:
            ErrorLogger.log_error(e)
            return False


    def should_use_escape_jail_card(self, game_state: GameState) -> bool:
        if game_state.escape_jail_cards[self] == 0:
            return False
        
        try:
            data = {
                "has_card": game_state.escape_jail_cards[self] > 0
            }
            return self._wait_for_decision("use_jail_card", data)
        except Exception as e:
            ErrorLogger.log_error(e)
            return False
        

    def should_accept_trade_offer(self, game_state: GameState, trade_offer: TradeOffer) -> bool:
        try:
            data = {
                "source_player": str(trade_offer.source_player),
                "properties_offered": [str(p) for p in trade_offer.properties_offered] if trade_offer.properties_offered else [],
                "money_offered": trade_offer.money_offered,
                "jail_cards_offered": trade_offer.jail_cards_offered,
                "properties_requested": [str(p) for p in trade_offer.properties_requested] if trade_offer.properties_requested else [],
                "money_requested": trade_offer.money_requested,
                "jail_cards_requested": trade_offer.jail_cards_requested,
                "my_balance": game_state.player_balances[self],
                "their_balance": game_state.player_balances[trade_offer.source_player]
            }
            return self._wait_for_decision("accept_trade", data)
        except Exception as e:
            print(f"Error in should_accept_trade_offer: {e}")
            return False


    def get_trade_offers(self, game_state: GameState) -> Optional[List[TradeOffer]]:
        try:
            players_data = []
            for player in game_state.players:
                if player != self:
                    players_data.append({
                        "name": str(player),
                        "properties": [str(p) for p in game_state.properties[player]],
                        "balance": game_state.player_balances[player],
                        "jail_cards": game_state.escape_jail_cards[player]
                    })

            my_data = {
                "properties": [str(p) for p in game_state.properties[self]],
                "balance": game_state.player_balances[self],
                "jail_cards": game_state.escape_jail_cards[self]
            }

            data = {
                "my_data": my_data,
                "players": players_data
            }

            trade_data = self._wait_for_decision("create_trade", data)

            if not trade_data:
                return None
                
            # Convert the trade data into TradeOffer objects
            offers = []
            for trade in trade_data:
                target_player = next(p for p in game_state.players if str(p) == trade["target_player"])


                # Convert property strings back to Property objects
                properties_offered = []
                if "properties_offered" in trade and trade["properties_offered"]:
                    for prop_str in trade["properties_offered"]:
                        prop = game_state.board.get_tile_by_name(prop_str)
                        if prop:
                            properties_offered.append(prop)

                properties_requested = []
                if "properties_requested" in trade and trade["properties_requested"]:
                    for prop_str in trade["properties_requested"]:
                        prop = game_state.board.get_tile_by_name(prop_str)
                        if prop:
                            properties_requested.append(prop)

                money_offered = None
                if "money_offered" in trade:
                    money_offered = trade["money_offered"]

                money_requested = None
                if "money_requested" in trade:
                    money_requested = trade["money_requested"]

                jail_cards_offered = None
                if "jail_cards_offered" in trade:
                    jail_cards_offered = trade["jail_cards_offered"]

                jail_cards_requested = None
                if "jail_cards_requested" in trade:
                    jail_cards_requested = trade["jail_cards_requested"]

                offer = TradeOffer(
                    source_player=self,
                    target_player=target_player,
                    properties_offered=properties_offered,
                    money_offered=money_offered,
                    jail_cards_offered=jail_cards_offered,
                    properties_requested=properties_requested,
                    money_requested=money_requested,
                    jail_cards_requested=jail_cards_requested
                )
                offers.append(offer)
            
            return offers
            
        except Exception as e:
            ErrorLogger.log_error(e)
            return None
        

    def on_event_received(self, event):
        """
        Process game events and forward them to the UI for display.
        
        Converts game events into a UI-friendly format and queues them
        for consumption by the frontend. Events are timestamped and
        marked with opponent flags for proper display.
        
        Parameters
        ----------
        event : Event
            The game event to process and display
        """

        # Call the parent implementation to log and store in history
        super().on_event_received(event)
        
        # Convert event to a UI-friendly format, regardless of which player triggered it
        ui_event = {
            "type": event.type.name,
            "description": event.description,
            "player": str(event.player),
            "target_player": str(event.target_player) if event.target_player else None,
            "tile": str(event.tile) if event.tile else None,
            "amount": event.amount,
            "timestamp": Date.now().isoformat(),  # Add a timestamp for sorting in ISO format
            "is_opponent": event.player != self  # Flag to indicate if it's an opponent's event
        }
        
        # Queue the event to be sent to the UI
        try:
            self.ui_event_queue.put_nowait(ui_event)
        except queue.Full:
            # Queue is full, remove oldest event and add new one
            try:
                self.ui_event_queue.get_nowait()
                self.ui_event_queue.put_nowait(ui_event)
            except:
                pass