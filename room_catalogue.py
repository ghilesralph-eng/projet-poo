# in a new file, e.g., rooms/room_data.py
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class RoomDef:
    name: str
    color: str
    rarity: int
    gem_cost: int
    doors: Tuple[bool, bool, bool, bool] # (up, right, down, left)
    effect_id: Optional[str] = None
    effect_value: Optional[int] = None # Or other param
    border_only: bool = False
    # ... any other special flags