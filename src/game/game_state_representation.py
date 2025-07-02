from game.game_state import GameState
from game.player import Player


class GameStateRepresentation:
    """
    Class to handle the JSON representation of the game state.
    """

    def __init__(self, game_state: GameState, additional_data: dict = None):
        """
        Initialize the GameStateRepresentation with a GameState object and optional additional data.
        
        :param game_state: The GameState object to represent.
        :param additional_data: Optional additional data to include in the representation.
        """
        self.game_state = game_state
        self.additional_data = additional_data


    def to_json(self) -> dict:
        """
        Convert the game state to a JSON-serializable dictionary.
        """
        json_representation = {}
        json_representation['game_state'] = self.game_state.json_representation()
        if self.additional_data:
            json_representation.update(self.additional_data)
        return json_representation
    

    @staticmethod
    def load_from_json(json_data: dict, players: list[Player]) -> 'GameStateRepresentation':
        """
        Load a GameStateRepresentation from a JSON-serializable dictionary.
        
        :param json_data: The JSON data to load from.
        :return: An instance of GameStateRepresentation.
        """
        game_state = GameState.from_json(json_data, players=players)
        additional_data = json_data.get('additional_data', {})
        return GameStateRepresentation(game_state, additional_data)