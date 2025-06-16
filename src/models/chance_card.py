from typing import Callable, Tuple


class ChanceCard:
    """
    Represents a Chance card with its description and executable action.
    
    Chance cards in Monopoly contain instructions that modify game state when drawn.
    Each card has a unique identifier, descriptive text for display, and an
    executable action function with parameters for game state modifications.
    
    Attributes
    ----------
    id : int
        Unique identifier for this chance card
    description : str
        Text description of the card's effect for display to players
    action : Callable
        Function to execute when this card is drawn
    args : Tuple
        Arguments to pass to the action function when executed
    """

    def __init__(self, id: int, description: str, action: Callable, args: Tuple):
        """
        Initialize a chance card with its action and parameters.
        
        Parameters
        ----------
        id : int
            Unique identifier for this card
        description : str
            Player-visible description of the card's effect
        action : Callable
            Function to execute when card is drawn
        args : Tuple
            Arguments for the action function
        """
        self.id = id
        self.description = description
        self.action = action
        self.args = args


    def __repr__(self):
        return f"ChanceCard ({self.id} - {self.description})"