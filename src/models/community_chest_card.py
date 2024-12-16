from typing import Callable, Tuple

class CommunityChestCard:
    def __init__(self, id: int, description: str, action: Callable, args: Tuple):
        self.id = id
        self.description = description
        self.action = action
        self.args = args

    def __repr__(self):
        return f"CommunityChestCard ({self.id} - {self.description})"