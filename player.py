# player.py
from inventory.inventory import Inventory

class Player:
    def __init__(self, r=3, c=1, inventory: Inventory | None = None):
        # position sur la grille (ligne, colonne)
        self.r = r
        self.c = c
        self.dir = "up"

        # on ne crée pas un nouvel inventaire si on nous en fournit un
        self.inventory = inventory if inventory is not None else Inventory()

    def move(self, dr, dc):
        self.r += dr
        self.c += dc

    def set_dir(self, d: str):
        self.dir = d

    def __str__(self):
        return f"Player at ({self.r}, {self.c})"

    # ========= Consommables =========
    def use_step(self, n=1):
        return self.inventory.use_step(n)

    def use_coins(self, n):
        return self.inventory.use_coins(n)

    def use_gems(self, n):
        return self.inventory.use_gems(n)

    def use_keys(self, n=1):
        return self.inventory.use_keys(n)

    def use_dice(self, n=1):
        return self.inventory.use_dice(n)

    # ========= Ajout =========
    def add_steps(self, n):
        return self.inventory.add_steps(n)

    def add_coins(self, n):
        return self.inventory.add_coins(n)

    def add_gems(self, n):
        return self.inventory.add_gems(n)

    def add_keys(self, n):
        return self.inventory.add_keys(n)

    def add_dice(self, n):
        return self.inventory.add_dice(n)

    # ========= Permanents =========
    def add_permanent(self, name):
        return self.inventory.add_permanent(name)

    def has_permanent(self, name):
        return self.inventory.has_permanent(name)
