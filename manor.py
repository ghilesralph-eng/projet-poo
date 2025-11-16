# manor.py

import random
from typing import List, Optional, Tuple, Dict

# Import your existing backend classes
from player import Player
from inventory.inventory import Inventory
from inventory.consumables import Consumables
from inventory.permanents import Permanents
from rooms.room_data import RoomDef, ROOM_CATALOGUE 

# --- Constants based on the PDF ---
GRID_ROWS = 5
GRID_COLS = 9
START_POS = (GRID_ROWS - 1, GRID_COLS // 2) # (4, 4) - Bottom-center
GOAL_POS = (0, GRID_COLS // 2)             # (0, 4) - Top-center

# Helper dictionary to map directions to (dr, dc) changes
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1)
}

class Manor:
    """
    Manages the game state, including the grid, the player, and the room deck.
    """

    def __init__(self):
        # Create the 5x9 grid, initially empty
        self.grid: List[List[Optional[RoomDef]]] = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        # Create the player at the starting position
        self.player = Player(start_row=START_POS[0], start_col=START_POS[1])
        
        # Create the "pioche" (deck) of available rooms
        self.deck: List[RoomDef] = []
        self._build_deck()
        
        # Place the fixed start and end rooms
        self._place_fixed_rooms()

    def _build_deck(self):
        """
        Populates the deck with all rooms from the catalogue,
        except for the pre-placed rooms.
        """
        for room_def in ROOM_CATALOGUE:
            # Don't add the fixed rooms to the deck
            if room_def.name in ("Entrance Hall", "Antechamber"):
                continue
            
            # Add multiple copies if specified (as per PDF example)
            # For now, we'll just add one copy.
            self.deck.append(room_def)
        
        # Shuffle the deck
        random.shuffle(self.deck)
        print(f"Deck built with {len(self.deck)} rooms.")

    def _place_fixed_rooms(self):
        """
        Finds and places the 'Entrance Hall' and 'Antechamber' on the grid.
        """
        entrance_hall = next((r for r in ROOM_CATALOGUE if r.name == "Entrance Hall"), None)
        antechamber = next((r for r in ROOM_CATALOGUE if r.name == "Antechamber"), None)
        
        if entrance_hall:
            self.grid[START_POS[0]][START_POS[1]] = entrance_hall
        else:
            print("ERROR: 'Entrance Hall' not found in ROOM_CATALOGUE")
            
        if antechamber:
            self.grid[GOAL_POS[0]][GOAL_POS[1]] = antechamber
        else:
            print("ERROR: 'Antechamber' not found in ROOM_CATALOGUE")

    def get_room(self, r: int, c: int) -> Optional[RoomDef]:
        """Safely get the room definition at a given (row, col)."""
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            return self.grid[r][c]
        return None

    def get_lock_level(self, dest_row: int) -> int:
        """
        Calculates the lock level for a door based on the row it leads to.
        Implements logic from section 2.8 of the PDF.
        """
        if dest_row == START_POS[0]:
            # Starting row always has unlocked doors
            return 0
        if dest_row == GOAL_POS[0]:
            # Goal row always has double-locked doors
            return 2
        
        # For intermediate rows, return a random level (e.g., 0, 1, or 1)
        # This can be adjusted for difficulty.
        return random.choice([0, 1, 1])

    def draw_candidates(self, r: int, c: int, from_dir: str) -> List[RoomDef]:
        """
        Draws 3 valid room candidates from the deck for a new position.
        """
        candidates = []
        
        # --- TODO ---
        # 1. Filter self.deck for rooms that can be placed at (r, c)
        #    [cite_start]- Check placement_condition (e.g., 'border_only') [cite: 419]
        #    - Check if the room has a door matching 'from_dir'
        
        # [cite_start]2. Draw 3 rooms based on rarity (Section 2.7) [cite: 137, 418]
        #    - Rarity 0: weight 1.0
        #    - Rarity 1: weight 1/3
        #    - Rarity 2: weight 1/9
        #    - Rarity 3: weight 1/27
        
        # [cite_start]3. Ensure at least one room costs 0 gems [cite: 138, 458]
        
        # For now, just return the first 3 rooms from the deck as a placeholder
        candidates = self.deck[:3] 
        
        print(f"Drawing candidates for ({r}, {c})")
        return candidates

    def place_room(self, room_def: RoomDef, r: int, c: int):
        """
        Places a chosen room onto the grid and removes it from the deck.
        """
        print(f"Placing {room_def.name} at ({r}, {c})")
        self.grid[r][c] = room_def
        
        # [cite_start]Remove the placed room from the deck so it can't be drawn again [cite: 101, 421]
        if room_def in self.deck:
            self.deck.remove(room_def)