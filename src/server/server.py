from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from game.game_state import GameState
from game.player import Player
from server_models.game_state_response import GameStateResponse
from server_models.player_state import PlayerState
from models.property_group import PropertyGroup
from server_models.property import Property
from server_models.mortage_request import MortagingRequest
import random
from server_utils.logger import ErrorLogger

# Initialize FastAPI app
app = FastAPI(title="Monopoly Game API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize game state
players = [Player("Player 1"), Player("Player 2")]
game_state = GameState(players)

# brown_properties = game_state.board.get_properties_by_group(PropertyGroup.BROWN)
# game_state.properties[players[0]] = list(brown_properties)
# game_state.is_owned.update(brown_properties)
# game_state.houses[PropertyGroup.BROWN] = (3, 0)

for group in PropertyGroup:
    # Skip non-property groups like RAILROAD and UTILITY
        # Get properties for this group
    group_properties = game_state.board.get_properties_by_group(group)
    # Assign properties to player 0
    game_state.properties[players[0]].extend(list(group_properties))
    # Mark properties as owned
    game_state.is_owned.update(group_properties)
    # Set 3 houses for each group
    game_state.houses[group] = (3, 0)  # (player0_houses, player1_houses)
    game_state.hotels[group] = (1, 0)  # (player0_hotels, player1_hotels)
game_state.doubles_rolled = 2


@app.get("/api/game-state", response_model=GameStateResponse)
async def get_game_state():
    try:
        players = [{
            "name": str(player),
            "properties": [Property(id=p.id, name=p.name) for p in game_state.properties[player]],
            "houses": game_state.get_houses_for_player(player),
            "hotels": game_state.get_hotels_for_player(player),
            "escape_jail_cards": game_state.escape_jail_cards[player],
            "in_jail": game_state.in_jail[player],
            "position": game_state.player_positions[player],
            "balance": game_state.player_balances[player]
        } for player in game_state.players]
        
        owned_properties = [prop.id for prop in game_state.is_owned]
        mortaged_properties = [prop.id for prop in game_state.mortgaged_properties]

        return {
            'players': players,
            'currentPlayer': game_state.current_player_index,
            'ownedProperties': owned_properties,
            'mortagedProperties': mortaged_properties
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/roll-dice")
async def roll_dice():
    try:
        dice = (random.randint(1, 6), random.randint(1, 6))
        current_player = game_state.players[game_state.current_player_index]
        
        game_state.move_player(current_player, dice)
        current_position = game_state.player_positions[current_player]
        current_tile = game_state.board.tiles[current_position]
        
        return {
            'dice': dice,
            'player': str(current_player),
            'position': current_position,
            'tile': str(current_tile),
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/buy-property")
async def buy_property():
    try:
        current_player = game_state.players[game_state.current_player_index]
        current_position = game_state.player_positions[current_player]
        property = game_state.board.tiles[current_position]
        
        game_state.buy_property(current_player, property)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/end-turn")
async def end_turn():
    game_state.change_turn()
    return {
        'nextPlayer': str(game_state.players[game_state.current_player_index])
    }

@app.post("/api/pay-rent")
async def pay_rent():
    try:
        current_player = game_state.players[game_state.current_player_index]
        current_position = game_state.player_positions[current_player]
        property = game_state.board.tiles[current_position]
        
        game_state.pay_rent(current_player, property)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/mortgage-property")
async def mortage_property(request: MortagingRequest):
    try:
        current_player = game_state.players[game_state.current_player_index]
        property_name = request.property_name
        property_name = property_name.split(' ')[0]
        property = game_state.board.get_property_by_name(property_name)
        game_state.mortage_property(current_player, property)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

class HouseRequest(MortagingRequest):
    property_name: str

@app.post("/api/place-house")
async def place_house(request: MortagingRequest):
    try:
        property_name = request.property_name
        property_name = property_name.split(' ')[0]

        current_player = game_state.players[game_state.current_player_index]

        property = game_state.board.get_property_by_name(property_name)

        property_group = property.group
        game_state.place_house(current_player, property_group)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))
    
class HotelRequest(MortagingRequest):
    property_name: str

@app.post("/api/place-hotel")
async def place_hotel(request: MortagingRequest):
    try:
        property_name = request.property_name
        property_name = property_name.split(' ')[0]

        current_player = game_state.players[game_state.current_player_index]

        property = game_state.board.get_property_by_name(property_name)

        property_group = property.group
        game_state.place_hotel(current_player, property_group)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sell-house")
async def sell_house(request: HouseRequest):
    try:
        property_name = request.property_name
        property_name = property_name.split(' ')[0]

        current_player = game_state.players[game_state.current_player_index]

        property = game_state.board.get_property_by_name(property_name)

        property_group = property.group
        game_state.sell_house(current_player, property_group)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))
    
@app.post("/api/sell-hotel")
async def sell_hotel(request: HotelRequest):
    try:
        property_name = request.property_name
        property_name = property_name.split(' ')[0]

        current_player = game_state.players[game_state.current_player_index]

        property = game_state.board.get_property_by_name(property_name)

        property_group = property.group
        game_state.sell_hotel(current_player, property_group)
        return {
            'success': True,
            'balance': game_state.player_balances[current_player],
            'properties': [str(p) for p in game_state.properties[current_player]]
        }
    except Exception as e:
        ErrorLogger.log_error(e)
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server on port 5000...")
    uvicorn.run("server:app", host="127.0.0.1", port=5000, reload=True)