import json
import os

from game.game_state import GameState
from models.property_group import PropertyGroup
from game.game_state_representation import GameStateRepresentation
from models.board import Board
from agents.random_agent import RandomAgent


def create_advanced_strategic_scenario():
    
    human_agent = RandomAgent("DQN player")
    dqn_agent = RandomAgent("Human Player")
    
    game_state = GameState([human_agent, dqn_agent])

    game_state.player_balances[dqn_agent] = 40_000
    game_state.player_balances[human_agent] = 40_000

    rahova = game_state.board.get_tile_by_name("Rahova") 
    giulesti = game_state.board.get_tile_by_name("Giulesti")
    game_state.buy_property(dqn_agent, rahova)
    game_state.buy_property(dqn_agent, giulesti)
    
    vitan = game_state.board.get_tile_by_name("Vitan")
    pantelimon = game_state.board.get_tile_by_name("Pantelimon")  
    game_state.buy_property(dqn_agent, vitan)
    game_state.buy_property(dqn_agent, pantelimon)
    

    timisoara = game_state.board.get_tile_by_name("B-dul Timisoara") 
    game_state.buy_property(dqn_agent, timisoara)
    
    carol = game_state.board.get_tile_by_name("B-dul Carol")       
    game_state.buy_property(dqn_agent, carol)

    titulescu = game_state.board.get_tile_by_name("B-dul Titulescu")
    bd_1_mai = game_state.board.get_tile_by_name("B-dul 1 Mai")
    game_state.buy_property(dqn_agent, titulescu)
    game_state.buy_property(dqn_agent, bd_1_mai)

    magheru = game_state.board.get_tile_by_name("B-dul Magheru")
    primaverii = game_state.board.get_tile_by_name("B-dul Primaverii")
    game_state.buy_property(dqn_agent, magheru)
    game_state.buy_property(dqn_agent, primaverii)

    gara_progresul = game_state.board.get_tile_by_name("Gara Progresul")
    gara_obor = game_state.board.get_tile_by_name("Gara Obor")
    game_state.buy_property(dqn_agent, gara_progresul)
    game_state.buy_property(dqn_agent, gara_obor)
    
    berceni = game_state.board.get_tile_by_name("Berceni") 
    game_state.buy_property(human_agent, berceni)
    
    titan = game_state.board.get_tile_by_name("Titan")          
    colentina = game_state.board.get_tile_by_name("Colentina")   
    tei = game_state.board.get_tile_by_name("Tei")                
    game_state.buy_property(human_agent, titan)
    game_state.buy_property(human_agent, colentina)
    game_state.buy_property(human_agent, tei)

    brasov = game_state.board.get_tile_by_name("B-dul Brasov")   
    drumul_taberei = game_state.board.get_tile_by_name("Drumul Taberei") 
    game_state.buy_property(human_agent, brasov)
    game_state.buy_property(human_agent, drumul_taberei)
    
    piata_unirii = game_state.board.get_tile_by_name("Piata Unirii")  
    cotroceni = game_state.board.get_tile_by_name("Cotroceni")
    game_state.buy_property(human_agent, piata_unirii)
    game_state.buy_property(human_agent, cotroceni)

    eroilor = game_state.board.get_tile_by_name("B-dul Eroilor")
    game_state.buy_property(human_agent, eroilor)

    uzina_electrica = game_state.board.get_tile_by_name("Uzina Electrica")
    game_state.buy_property(human_agent, uzina_electrica)

    gara_de_nord = game_state.board.get_tile_by_name("Gara de Nord")
    game_state.buy_property(human_agent, gara_de_nord)


    game_state.place_house(dqn_agent, PropertyGroup.BROWN)

    game_state.player_balances[dqn_agent] = 1000
    game_state.player_balances[human_agent] = 1200
    
    game_state.player_positions[dqn_agent] = 12
    
    game_state.player_positions[human_agent] = 38
    
    game_state.current_player_index = 1
    game_state.receive_get_out_of_jail_card(dqn_agent)
    
    return game_state, {
        "scenario_name": "advanced_multi_decision_strategic_test",
        "description": "Complex scenario testing DQN's advanced strategic reasoning across multiple dimensions",
        "seed": "7379100"
    }


def create_end_game_pressure_scenario():
    """
    Creates a late-game scenario with high-stakes decisions and cash flow management.
    Tests DQN's ability to handle complex end-game dynamics.
    """
    
    human_agent = RandomAgent("Human Player")
    dqn_agent = RandomAgent("DQN player")
    
    game_state = GameState([human_agent, dqn_agent])

    game_state.player_balances[dqn_agent] = 40_000
    game_state.player_balances[human_agent] = 40_000

    rahova = game_state.board.get_tile_by_name("Rahova")
    giulesti = game_state.board.get_tile_by_name("Giulesti")
    game_state.buy_property(dqn_agent, rahova)
    game_state.buy_property(dqn_agent, giulesti)
    game_state.place_house(dqn_agent, PropertyGroup.BROWN)
    game_state.place_house(dqn_agent, PropertyGroup.BROWN)
    
    titulescu = game_state.board.get_tile_by_name("B-dul Titulescu")
    mai = game_state.board.get_tile_by_name("B-dul 1 Mai")
    dorobantilor = game_state.board.get_tile_by_name("Calea Dorobantilor")
    game_state.buy_property(dqn_agent, titulescu)
    game_state.buy_property(dqn_agent, mai)
    game_state.buy_property(dqn_agent, dorobantilor)
    
    magheru = game_state.board.get_tile_by_name("B-dul Magheru")
    primaverii = game_state.board.get_tile_by_name("B-dul Primaverii")
    game_state.buy_property(dqn_agent, magheru)
    game_state.buy_property(dqn_agent, primaverii)
    
    gara_nord = game_state.board.get_tile_by_name("Gara de Nord")
    gara_basarab = game_state.board.get_tile_by_name("Gara Basarab")
    gara_obor = game_state.board.get_tile_by_name("Gara Obor")
    game_state.buy_property(dqn_agent, gara_nord)
    game_state.buy_property(dqn_agent, gara_basarab)
    game_state.buy_property(dqn_agent, gara_obor)
    
    gara_progresul = game_state.board.get_tile_by_name("Gara Progresul")
    game_state.buy_property(dqn_agent, gara_progresul)
    game_state.mortgage_property(dqn_agent, gara_progresul)
    
    carol = game_state.board.get_tile_by_name("B-dul Carol")
    eroilor = game_state.board.get_tile_by_name("B-dul Eroilor")
    game_state.buy_property(dqn_agent, carol)
    game_state.buy_property(dqn_agent, eroilor)

    titan = game_state.board.get_tile_by_name("Titan")
    colentina = game_state.board.get_tile_by_name("Colentina")
    tei = game_state.board.get_tile_by_name("Tei")
    game_state.buy_property(dqn_agent, titan)
    game_state.buy_property(dqn_agent, colentina)
    game_state.buy_property(dqn_agent, tei)
    game_state.place_house(dqn_agent, PropertyGroup.PINK)
    game_state.place_house(dqn_agent, PropertyGroup.PINK)
    
    timisoara = game_state.board.get_tile_by_name("B-dul Timisoara")
    brasov = game_state.board.get_tile_by_name("B-dul Brasov")
    drumul_taberei = game_state.board.get_tile_by_name("Drumul Taberei")
    game_state.buy_property(human_agent, timisoara)
    game_state.buy_property(human_agent, brasov)
    game_state.buy_property(human_agent, drumul_taberei)
    game_state.place_house(human_agent, PropertyGroup.ORANGE)
    game_state.place_house(human_agent, PropertyGroup.ORANGE)
    
    piata_unirii = game_state.board.get_tile_by_name("Piata Unirii")
    cotroceni = game_state.board.get_tile_by_name("Cotroceni")
    calea_victoriei = game_state.board.get_tile_by_name("Calea Victoriei")
    game_state.buy_property(human_agent, piata_unirii)
    game_state.buy_property(human_agent, cotroceni)
    game_state.buy_property(human_agent, calea_victoriei)
    game_state.place_house(human_agent, PropertyGroup.GREEN)
    game_state.place_house(human_agent, PropertyGroup.GREEN)
    game_state.place_house(human_agent, PropertyGroup.GREEN)
    
    
    berceni = game_state.board.get_tile_by_name("Berceni")
    kogalniceanu = game_state.board.get_tile_by_name("B-dul Kogalniceanu")
    game_state.buy_property(human_agent, berceni)
    game_state.buy_property(human_agent, kogalniceanu)
    
    uzina_electrica = game_state.board.get_tile_by_name("Uzina Electrica")
    uzina_apa = game_state.board.get_tile_by_name("Uzina de Apa")
    game_state.buy_property(human_agent, uzina_electrica)
    game_state.buy_property(human_agent, uzina_apa)
    
    game_state.player_balances[dqn_agent] = 2500
    
    game_state.player_balances[human_agent] = 2600
    
    game_state.player_positions[dqn_agent] = 29
    
    game_state.player_positions[human_agent] = 39
    
    game_state.send_player_to_jail(dqn_agent)
    game_state.count_turn_in_jail(dqn_agent)
    
    game_state.receive_get_out_of_jail_card(dqn_agent)
    
    game_state.current_player_index = 1 
    
    return game_state, {
        "scenario_name": "end_game_high_stakes_cash_management",
        "description": "Late-game scenario with developed monopolies and cash flow pressure",
        "seed": "8431292"
    }

def save_scenario_to_json(game_state, metadata, filename):
    """
    Save the game state scenario to JSON file with metadata.
    """
    
    game_state.configure_debug_mode(True)
    
    json_data = GameStateRepresentation(
        game_state, 
        additional_data=metadata
    ).to_json()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)
    
    print(f"Saved complex scenario: {filename}")
    
    return json_data

if __name__ == "__main__":

    root_folder = "../misc/game_configurations"
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)
    
    game_state1, metadata1 = create_advanced_strategic_scenario()
    json_data1 = save_scenario_to_json(
        game_state1, 
        metadata1, 
        f"{root_folder}/advanced_game_configuration.json"
    )
    
    game_state2, metadata2 = create_end_game_pressure_scenario()
    json_data2 = save_scenario_to_json(
        game_state2, 
        metadata2, 
        f"{root_folder}/endgame_game_configuration.json"
    )