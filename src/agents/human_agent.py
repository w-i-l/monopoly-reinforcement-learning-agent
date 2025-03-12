from game.game_state import GameState
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import queue
import threading
import subprocess
import sys
import os
import signal
import time
from pathlib import Path
from utils.logger import ErrorLogger
from fastapi import HTTPException
from server.server_models.property import Property as ServerProperty
from game.player import Player
from models.tile import Tile
from models.property_group import PropertyGroup
from models.property import Property
from models.railway import Railway
from models.utility import Utility
from copy import deepcopy
from models.trade_offer import TradeOffer
from typing import Optional
from datetime import datetime as Date

class HumanAgent(Player):
    def __init__(self, name, port=6060, frontend_port=5173):
        super().__init__(name)
        self.port = port
        self.game_state = None
        self.frontend_port = frontend_port

        self.decision_queue = queue.Queue()
        self.response_queue = queue.Queue()

        self.ui_event_queue = queue.Queue(maxsize=100)  # Cap at 100 events

        self.server = self._setup_server()

        self._start_server()
        self._start_frontend()


    def _setup_server(self):
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
            try:
                self.response_queue.put(decision['choice'])
                return {"status": "success"}
            except Exception as e:
                ErrorLogger.log_error(e)
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/pending-decision")
        async def get_pending_decision():
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

        return app
    

    def _start_server(self):
        def run_server():
            import uvicorn
            config = uvicorn.Config(self.server, host="127.0.0.1", port=self.port, log_level="error")
            server = uvicorn.Server(config)
            server.run()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        self.server_thread.join(timeout=1) # Wait for server to start
        print(f"Server started - http://127.0.0.1:{self.port}")


    def _get_project_root(self) -> Path:
        current_path = Path(__file__).resolve()  # Get the human_agent.py location
        # Go up until we find the src directory
        while current_path.name != "src" and current_path.parent != current_path:
            current_path = current_path.parent
        if current_path.name != "src":
            raise FileNotFoundError("Could not find src directory")
        return current_path.parent
    

    def _create_human_interface(self, components_dir: Path):
        human_player_dir = components_dir / "HumanPlayer"
        human_player_dir.mkdir(exist_ok=True)

        interface_path = human_player_dir / "HumanPlayerInterface.jsx"
        if not interface_path.exists():
            component_code = """
    import React, { useState, useEffect } from 'react';
    import MonopolyBoard from '../Board/MonopolyBoard';
    import Alert from "../UI/Alert";
    import { AlertDescription } from "../UI/Alert";
    import Button from "../UI/Button";
    import useGameState from '../../hooks/useGameState';

    const HumanPlayerInterface = ({ playerPort = 6060 }) => {  // Added default value
        const [pendingDecision, setPendingDecision] = useState(null);
        const [error, setError] = useState(null);
        const gameState = useGameState();

        useEffect(() => {
            if (!playerPort) return;  // Added guard
            
            const checkDecisions = async () => {
                try {
                    const response = await fetch(`http://localhost:${playerPort}/api/pending-decision`);
                    if (!response.ok) throw new Error('Failed to fetch decisions');
                    const data = await response.json();
                    if (data.type !== 'none') {
                        setPendingDecision(data);
                    }
                } catch (err) {
                    setError(err.message);
                }
            };

            const interval = setInterval(checkDecisions, 1000);
            return () => clearInterval(interval);
        }, [playerPort]);

        const handleDecision = async (choice) => {
            if (!playerPort) return;  // Added guard
            
            try {
                const response = await fetch(`http://localhost:${playerPort}/api/decision`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ choice }),
                });
                if (!response.ok) throw new Error('Failed to send decision');
                setPendingDecision(null);
            } catch (err) {
                setError(err.message);
            }
        };

        // Rest of the component remains the same
    """
            interface_path.write_text(component_code)
                
            # Update main.jsx to properly pass the port
            main_content = f"""
            import {{ StrictMode }} from 'react';
            import {{ createRoot }} from 'react-dom/client';
            import './index.css';
            import './style.css'
            import HumanPlayerInterface from './components/HumanPlayer/HumanPlayerInterface';

            const root = createRoot(document.getElementById('root'));
            root.render(
                <StrictMode>
                    <HumanPlayerInterface playerPort={{{self.port}}} />
                </StrictMode>
            );
            """

            project_root = self._get_project_root()
            frontend_dir = project_root / "frontend"
            main_dir = frontend_dir / "src" / "main.jsx"
            with open(main_dir, "w+") as f:
                f.write(main_content)

        return "HumanPlayerInterface"


    def _start_frontend(self):
        try:
            project_root = self._get_project_root()
            frontend_dir = project_root / "frontend"
            components_dir = frontend_dir / "src" / "components"

            print(f"Starting frontend from directory: {frontend_dir}")

            # Verify frontend directory exists
            if not frontend_dir.exists():
                raise RuntimeError(f"Frontend directory not found at {frontend_dir}")

            # Verify package.json exists
            if not (frontend_dir / "package.json").exists():
                raise RuntimeError(f"package.json not found in {frontend_dir}")

            # Create the human player interface component
            component_name = self._create_human_interface(components_dir)

            # Update the main.jsx content
            main_content = f"""
    import {{ StrictMode }} from 'react'
    import {{ createRoot }} from 'react-dom/client'
    import './index.css'
    import './style.css'
    import HumanPlayerInterface from './components/HumanPlayer/HumanPlayerInterface'

    const root = createRoot(document.getElementById('root'))
    root.render(
        <StrictMode>
            <HumanPlayerInterface playerPort={{{self.port}}} />
        </StrictMode>
    )
    """
            with open(frontend_dir / "src" / "main.jsx", "w") as f:
                f.write(main_content)

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
        self.decision_queue.put({
            "type": decision_type,
            "data": data
        })
        return self.response_queue.get()


    # Rest of the agent methods remain the same as in the previous version
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
                if len(grouped_properties[group]) != len(game_state.board.get_properties_by_group(group)):
                    grouped_properties.pop(group)

            if not grouped_properties:
                return []

            data = {
                "grouped_properties": {
                    str(group): [str(p) for p in props]
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
        Handle events by storing them and forwarding to the UI.
        
        Args:
            event: The Event object
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