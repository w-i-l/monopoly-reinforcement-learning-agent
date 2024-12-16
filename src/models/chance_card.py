from typing import Callable, Tuple

class ChanceCard:
    def __init__(self, id: int, description: str, action: Callable, args: Tuple):
        self.id = id
        self.description = description
        self.action = action
        self.args = args

    def __repr__(self):
        return f"ChanceCard ({self.id} - {self.description})"
