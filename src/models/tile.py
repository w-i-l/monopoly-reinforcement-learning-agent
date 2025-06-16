class Tile:
    """
    Base class for all Monopoly board tiles.
    
    Provides the fundamental structure shared by all tiles on the Monopoly board,
    including board position and display name. Serves as the parent class for
    all specific tile types (properties, railways, utilities, special tiles).
    
    Attributes
    ----------
    id : int
        Board position (0-39) of this tile
    name : str
        Display name of the tile for UI and game messages
    """


    def __init__(self, id: int, name: str):
        """
        Initialize a board tile with position and name.
        
        Parameters
        ----------
        id : int
            Board position of this tile (0-39)
        name : str
            Display name of the tile
        """
        self.id = id
        self.name = name
