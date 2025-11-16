
import random
from typing import List, Optional, Tuple, Dict, Union

# Import your existing backend classes
from player import Player
from rooms.room_data import RoomDef, ROOM_CATALOGUE

# --- Constants based on the PDF ---
GRID_ROWS = 5
GRID_COLS = 9

# [PDF 2.5] Player starts at Entrance Hall (bottom-center)
# We map (x, y) to (col, row)
# (x=4, y=4) is the 5th column, 5th row (bottom-center of 5x9)
START_POS = (GRID_COLS // 2, GRID_ROWS - 1) # (4, 4)
# [PDF 2.5] Goal is Antechamber (top-center)
GOAL_POS = (GRID_COLS // 2, 0)             # (4, 0)

# Helper dictionary to map directions to (dx, dy) changes
DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0)
}
# Helper to get the opposite direction
OPPOSITE_DIR: Dict[str, str] = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left"
}
# Helper to map direction string to RoomDef.doors tuple index
DOOR_INDEX: Dict[str, int] = {
    "up": 0,
    "right": 1,
    "down": 2,
    "left": 3
}


class Manor:
    """
    Manages the game state, including the grid, the player, and the room deck.
    """

    def __init__(self):
        # Create the 5x9 grid (List of Lists)
        # self.grid[y][x]
        self.grid: List[List[Optional[RoomDef]]] = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        
        # Create the player at the starting position
        self.player = Player(x=START_POS[0], y=START_POS[1])
        
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
            if room_def.name in ("Entrance Hall", "Antechamber"):
                continue
            
            # [PDF 2.3] Allows for multiple copies of rooms in the deck
            # We'll just add one for now.
            self.deck.append(room_def)
        
        random.shuffle(self.deck)
        print(f"Deck built with {len(self.deck)} rooms.")

    def _place_fixed_rooms(self):
        """
        Finds and places the 'Entrance Hall' and 'Antechamber' on the grid.
        """
        entrance_hall = next((r for r in ROOM_CATALOGUE if r.name == "Entrance Hall"), None)
        antechamber = next((r for r in ROOM_CATALOGUE if r.name == "Antechamber"), None)
        
        if entrance_hall:
            # self.grid[y][x]
            self.grid[START_POS[1]][START_POS[0]] = entrance_hall
        else:
            print("ERROR: 'Entrance Hall' not found in ROOM_CATALOGUE")
            
        if antechamber:
            # self.grid[y][x]
            self.grid[GOAL_POS[1]][GOAL_POS[0]] = antechamber
        else:
            print("ERROR: 'Antechamber' not found in ROOM_CATALOGUE")

    def get_room(self, x: int, y: int) -> Optional[RoomDef]:
        """Safely get the room definition at a given (x, y)."""
        if 0 <= x < GRID_COLS and 0 <= y < GRID_ROWS:
            return self.grid[y][x]
        return None

    def get_lock_level(self, dest_y: int) -> int:
        """
        Calculates the lock level for a door based on the row (y) it leads to.
        Implements logic from section 2.8 of the PDF. [cite: 465, 466, 467]
        """
        if dest_y == START_POS[1]: # y=4 (bottom row)
            return 0 # [PDF 2.8] Unlocked
        if dest_y == GOAL_POS[1]: # y=0 (top row)
            return 2 # [PDF 2.8] Double-locked
        
        # Intermediate rows (1, 2, 3)
        # We can make this more likely to be 1
        return random.choice([0, 1, 1, 2])

    def _get_rarity_weight(self, room: RoomDef) -> float:
        """
        Calculates draw weight based on rarity. [PDF 2.3]
        Handles both int and (min, max) tuple from your room_data.py.
        """
        rarity = room.rarity
        if isinstance(rarity, tuple):
            rarity = rarity[0] # Use the min rarity for calculation
        
        # [PDF 2.3] "Chaque incrément ... doit diviser par trois la probabilité"
        return 1.0 / (3**rarity)

    def _get_gem_cost(self, room: RoomDef) -> int:
        """
        Gets the gem cost.
        Handles both int and (min, max) tuple from your room_data.py.
        """
        cost = room.gem_cost
        if isinstance(cost, tuple):
            cost = cost[0] # Use the min cost
        return cost

    def _is_valid_placement(self, room: RoomDef, x: int, y: int, from_dir: str) -> bool:
        """
        Checks if a room can be legally placed at (x, y) coming from `from_dir`.
        Implements rules from PDF 2.7.
        """
        # --- Rule 1: Must have a door connecting back
        # The room we are placing must have a door on the side we came from.
        connecting_door_index = DOOR_INDEX[OPPOSITE_DIR[from_dir]]
        if not room.doors[connecting_door_index]:
            return False

        # --- Rule 2: Check placement conditions
        if room.placement_condition == 'border_only':
            if not (x == 0 or x == GRID_COLS - 1 or y == 0 or y == GRID_ROWS - 1):
                return False
        if room.placement_condition == 'not edges':
             if (x == 0 or x == GRID_COLS - 1 or y == 0 or y == GRID_ROWS - 1):
                return False
        
        # --- Rule 3: Check allowed rows (from room_data.py)
        if room.allowed_rows:
            min_row, max_row = room.allowed_rows
            # Your room_data.py has rows 1-45, let's map to 0-4
            # This is tricky. Let's assume for now 1-12 means row 0-1, etc.
            # A simpler rule: if y is in the allowed range (e.g., (1,12))
            # Let's ignore this for now as it's complex, but here's where it would go.

        # --- Rule 4: [PDF 2.7] No doors leading outside the manor
        for direction, (dx, dy) in DIRECTIONS.items():
            door_exists = room.doors[DOOR_INDEX[direction]]
            if not door_exists:
                continue
            
            # Check if this door leads to a valid *grid cell*
            neighbor_x, neighbor_y = x + dx, y + dy
            if not (0 <= neighbor_x < GRID_COLS and 0 <= neighbor_y < GRID_ROWS):
                # This room has a door pointing off the map
                return False

        return True

    def draw_candidates(self, x: int, y: int, from_dir: str) -> List[RoomDef]:
        """
        Draws 3 valid room candidates from the deck for a new position.
        Implements PDF 2.7 and 2.8.
        """
        # 1. Filter deck for all valid placements
        valid_rooms = [
            room for room in self.deck
            if self._is_valid_placement(room, x, y, from_dir)
        ]

        if not valid_rooms:
            return [] # No rooms can be placed here!

        # 2. Get weights for each valid room [cite: 417, 418]
        weights = [self._get_rarity_weight(room) for room in valid_rooms]

        # 3. Draw 3 candidates using weighted choice
        #    `k=3` will pick 3 rooms. `random.choices` can pick the same room
        #    multiple times, which is fine as per PDF 2.3.
        #    If you want 3 *unique* rooms, this is harder.
        #    Let's assume `k=3` is fine for now.
        if len(valid_rooms) <= 3:
            candidates = valid_rooms # Not enough rooms to draw, just return all
        else:
            candidates = random.choices(valid_rooms, weights=weights, k=3)
        
        # 4. [PDF 2.7] Ensure at least one room costs 0 gems 
        # Check if we need to fix this
        if all(self._get_gem_cost(room) > 0 for room in candidates):
            # Try to find a free room from the valid list
            free_rooms = [room for room in valid_rooms if self._get_gem_cost(room) == 0]
            if free_rooms:
                # Replace one of the drawn rooms with a random free one
                candidates[random.randint(0, 2)] = random.choice(free_rooms)
            # If no free rooms exist, the game continues (per PDF, this
            # rule is to *prevent* a block, but if no free rooms are
            # placeable, we can't do anything)

        print(f"Drawing candidates for ({x}, {y}): {[r.name for r in candidates]}")
        return candidates

    def place_room(self, room_def: RoomDef, x: int, y: int):
        """
        Places a chosen room onto the grid and removes it from the deck.
        """
        print(f"Placing {room_def.name} at ({x}, {y})")
        self.grid[y][x] = room_def
        
        # [PDF 2.3] Remove the placed room from the deck
        if room_def in self.deck:
            self.deck.remove(room_def)