from typing import Callable, Tuple


class CommunityChestCard:
    """
    Represents a Community Chest card with its description and executable action.
    
    Community Chest cards function identically to Chance cards but are drawn from
    a separate deck. They contain instructions that modify game state when drawn,
    typically involving money transfers or positional changes.
    
    Attributes
    ----------
    id : int
        Unique identifier for this community chest card
    description : str
        Text description of the card's effect for display to players
    action : Callable
        Function to execute when this card is drawn
    args : Tuple
        Arguments to pass to the action function when executed
    """


    def __init__(self, id: int, description: str, action: Callable, args: Tuple):
        """
        Initialize a community chest card with its action and parameters.
        
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
        return f"CommunityChestCard ({self.id} - {self.description})"

