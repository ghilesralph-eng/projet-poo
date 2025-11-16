import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from room_def import RoomDef, ROOM_CATALOGUE  

GRID_ROWS, GRID_COLS = 5, 9

@dataclass
class Room:
    definition: RoomDef
    placed_doors: Tuple[bool,bool,bool,bool]  # up,right,down,left

class Manor:
    def __init__(self):
        # None = vide; sinon Room
        self.grid: List[List[Optional[Room]]] = [[None for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self.deck: List[RoomDef] = []
        self.reset_deck()
        # Point de départ et arrivée
        self.start = (GRID_ROWS-1, GRID_COLS//2)   # bas-centre
        self.goal  = (0, GRID_COLS//2)             # haut-centre
        # Place Entrance Hall & Antechamber
        self.place_fixed()

    def reset_deck(self):
        # Construire la pioche : plusieurs exemplaires simples pour la démo
        base = []
        for rd in ROOM_CATALOGUE:
            if rd.name in ("Entrance Hall","Antechamber"): continue
            copies = 2 if rd.rarity == 0 else 1
            base += [rd]*copies
        self.deck = base.copy()

    def place_fixed(self):
        er, ec = self.start
        gr, gc = self.goal

    # Find the definitions from YOUR catalogue
        try:
            entrance_def = next(r for r in ROOM_CATALOGUE if r.name == "Entrance Hall")
            antechamber_def = next(r for r in ROOM_CATALOGUE if r.name == "Antechamber")
        except StopIteration:
            print("CRITICAL ERROR: 'Entrance Hall' or 'Antechamber' not in ROOM_CATALOGUE")
            return False
        self.grid[er][ec] = Room(entrance_def, entrance_def.doors)
        self.grid[gr][gc] = Room(antechamber_def, antechamber_def.doors)

    def neighbors_mask(self, r: int, c: int) -> Tuple[bool,bool,bool,bool]:
        # up,right,down,left exist & are empty/occupied
        up = inside(r-1,c)
        right = inside(r,c+1)
        down = inside(r+1,c)
        left = inside(r,c-1)
        return (up,right,down,left)

    def can_place(self, rd: RoomDef, r: int, c: int, from_dir: str) -> bool:
        # Vérifie conditions basiques: pas déjà occupé, conditions de bordure, compatibilité des portes
        if not inside(r,c): return False
        if self.grid[r][c] is not None: return False
        if rd.placement_condition == "border_only":
            if not (r in (0, GRID_ROWS-1) or c in (0, GRID_COLS-1)):
                return False
        # Compatibilité: la porte opposée doit exister
        idx_map = {"up":0,"right":1,"down":2,"left":3}
        opp = {"up":"down","down":"up","left":"right","right":"left"}
        need_open_here = rd.doors[idx_map[opp[from_dir]]]
        if not need_open_here:
            return False
        # Eviter portes sortant de la grille
        up,right,down,left = self.neighbors_mask(r,c)
        for flag, exists in zip(rd.doors,(up,right,down,left)):
            if flag and not exists:
                return False
        return True

    def lock_level_for_row(self, r: int) -> int:
        # 2.8: difficulté augmente vers le haut; bas (row 4) = 0, haut (row 0) = 2
        if r == GRID_ROWS-1:
            return 0
        if r == 0:
            return 2
        # intermédiaire: biais vers 1/2
        vals = [0,1,1,2]
        return random.choice(vals)

    def draw_candidates(self, r:int, c:int, from_dir:str, force_free_option=True) -> List[RoomDef]:
        # Tire 3 pièces admissibles avec pondération par rareté
        pool = [rd for rd in self.deck if self.can_place(rd, r, c, from_dir)]
        if not pool:
            return []
        # poids: 1 / 3^rarity
        weights = [1.0/(3**rd.rarity) for rd in pool]
        picks: List[RoomDef] = []
        temp_pool = pool[:]
        temp_w = weights[:]
        for _ in range(min(3, len(temp_pool))):
            wsum = sum(temp_w)
            rnum = random.random()*wsum
            acc = 0
            idx = 0
            for i, w in enumerate(temp_w):
                acc += w
                if rnum <= acc:
                    idx = i
                    break
            picks.append(temp_pool.pop(idx))
            temp_w.pop(idx)
        if force_free_option and picks and all(p.gem_cost>0 for p in picks):
            # insérer une option coût 0 si possible
            free_opts = [rd for rd in pool if rd.gem_cost==0 and rd not in picks]
            if free_opts:
                picks[-1] = random.choice(free_opts)
        return picks

    def place_room(self, rd: RoomDef, r: int, c: int, from_dir: str):
        # Détermine les portes placées (bloquer celles qui n'ont pas de voisin)
        up,right,down,left = self.neighbors_mask(r,c)
        base = list(rd.doors)
        # si pas de voisin -> fermera
        base[0] = base[0] and up
        base[1] = base[1] and right
        base[2] = base[2] and down
        base[3] = base[3] and left
        rm = Room(rd, tuple(base))
        self.grid[r][c] = rm
        # retirer de la pioche (single copy)
        if rd in self.deck:
            self.deck.remove(rd)
