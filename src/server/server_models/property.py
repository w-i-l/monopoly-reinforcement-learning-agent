from pydantic import BaseModel
from typing import List, Dict

class Property(BaseModel):
    id: int
    name: str