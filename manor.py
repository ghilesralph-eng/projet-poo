import random
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict

from rooms.room_data import RoomDef, ROOM_CATALOGUE

# ------------------ CONSTANTES ------------------
GRID_ROWS = 9      # 9 lignes
GRID_COLS = 5      # 5 colonnes

# (r, c) = (ligne, colonne)
START_POS = (GRID_ROWS - 1, GRID_COLS // 2)  # bas milieu -> (8, 2)
GOAL_POS  = (0, GRID_COLS // 2)              # haut milieu -> (0, 2)

DIRECTIONS: Dict[str, Tuple[int, int]] = {
    "up":    (-1, 0),
    "down":  (1, 0),
    "left":  (0, -1),
    "right": (0, 1),
}

OPPOSITE_DIR: Dict[str, str] = {
    "up":    "down",
    "down":  "up",
    "left":  "right",
    "right": "left",
}

DOOR_INDEX: Dict[str, int] = {
    "up":    0,
    "right": 1,
    "down":  2,
    "left":  3,
}


def inside(r: int, c: int) -> bool:
    return 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS


@dataclass
class Room:
    """
    Wrapper autour de RoomDef pour coller à main_game :
    - definition : RoomDef
    - placed_doors : tuple(bool,bool,bool,bool)
    """
    definition: RoomDef
    placed_doors: Tuple[bool, bool, bool, bool]


class Manor:
    """
    Gère la grille 9x5, la pioche et les règles de placement.
    grid[r][c] contient soit None soit un Room.
    """

    def __init__(self):
        # grid[r][c]
        self.grid: List[List[Optional[Room]]] = [
            [None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)
        ]

        self.start: Tuple[int, int] = START_POS  # (row, col)
        self.goal: Tuple[int, int] = GOAL_POS

        self.deck: List[RoomDef] = []
        self._build_deck()
        self._place_fixed_rooms()

    # ------------------ INIT DECK + SALLES FIXES ------------------

    def _build_deck(self) -> None:
        """Pioche de toutes les salles sauf Entrance / Antechamber."""
        self.deck.clear()
        for rd in ROOM_CATALOGUE:
            if rd.name in ("Entrance Hall", "Antechamber"):
                continue
            self.deck.append(rd)
        random.shuffle(self.deck)

    def _place_fixed_rooms(self) -> None:
        """Place Entrance Hall en bas milieu et Antechamber en haut milieu."""
        entrance_hall = next((r for r in ROOM_CATALOGUE if r.name == "Entrance Hall"), None)
        antechamber   = next((r for r in ROOM_CATALOGUE if r.name == "Antechamber"), None)

        if entrance_hall is None:
            print("ERROR: 'Entrance Hall' not found in ROOM_CATALOGUE")
        else:
            r, c = START_POS
            self.grid[r][c] = Room(entrance_hall, entrance_hall.doors)

        if antechamber is None:
            print("ERROR: 'Antechamber' not found in ROOM_CATALOGUE")
        else:
            r, c = GOAL_POS
            self.grid[r][c] = Room(antechamber, antechamber.doors)

    # ------------------ ACCÈS SIMPLES ------------------

    def get_room(self, c: int, r: int) -> Optional[Room]:
        """Compat éventuelle avec ancien code (x = col, y = row)."""
        if inside(r, c):
            return self.grid[r][c]
        return None

    # ------------------ NIVEAU DE VERROU ------------------

    def lock_level_for_row(self, r: int) -> int:
        """Niveau de verrou en fonction de la ligne d’arrivée."""
        if r == START_POS[0]:
            return 0
        if r == GOAL_POS[0]:
            return 2
        return random.choice([0, 1, 1, 1, 2])

    # ------------------ AIDE RARETÉ / COÛT ------------------

    def _get_rarity_weight(self, room: RoomDef) -> float:
        rarity = room.rarity
        if isinstance(rarity, tuple):
            rarity = rarity[0]
        return 1.0 / (3 ** rarity)

    def _get_gem_cost(self, room: RoomDef) -> int:
        cost = room.gem_cost
        if isinstance(cost, tuple):
            cost = cost[0]
        return cost

    # ------------------ CONTRÔLE DE PLACEMENT ------------------

    def _is_valid_placement(self, room: RoomDef, r: int, c: int, from_dir: str) -> bool:
        # 1) porte de connexion obligatoire
        idx_back = DOOR_INDEX[OPPOSITE_DIR[from_dir]]
        if not room.doors[idx_back]:
            return False

        # 2) contraintes de bordure
        cond = getattr(room, "placement_condition", None)
        if cond == "border_only":
            if not (r == 0 or r == GRID_ROWS - 1 or c == 0 or c == GRID_COLS - 1):
                return False
        if cond == "not_edges":
            if r == 0 or r == GRID_ROWS - 1 or c == 0 or c == GRID_COLS - 1:
                return False

        # 3) aucune porte vers l’extérieur du manoir
        for dname, (dr, dc) in DIRECTIONS.items():
            if not room.doors[DOOR_INDEX[dname]]:
                continue
            nr, nc = r + dr, c + dc
            if not inside(nr, nc):
                return False

        return True

    # ------------------ TIRAGE DES CANDIDATS ------------------

    def draw_candidates(self, r: int, c: int, from_dir: str) -> List[RoomDef]:
        """Renvoie 3 RoomDef possibles pour (r, c) en venant de from_dir."""
        valid = [
            rd for rd in self.deck
            if self._is_valid_placement(rd, r, c, from_dir)
        ]
        if not valid:
            return []

        weights = [self._get_rarity_weight(rd) for rd in valid]

        if len(valid) <= 3:
            candidates = valid[:]
        else:
            candidates = random.choices(valid, weights=weights, k=3)

        # garantir au moins 1 salle coût 0
        if all(self._get_gem_cost(x) > 0 for x in candidates):
            free = [rd for rd in valid if self._get_gem_cost(rd) == 0]
            if free:
                import random as _r
                candidates[_r.randint(0, len(candidates) - 1)] = _r.choice(free)

        return candidates

    # ------------------ PLACEMENT EFFECTIF ------------------

    def place_room(self, room_def: RoomDef, r: int, c: int, from_dir: str) -> None:
        if not inside(r, c):
            return
        self.grid[r][c] = Room(room_def, room_def.doors)
        if room_def in self.deck:
            self.deck.remove(room_def)
