from pydantic import BaseModel
from typing import List, Dict

class MortagingRequest(BaseModel):
    property_name: str