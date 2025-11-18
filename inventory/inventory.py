# inventory/inventory.py

class Inventory:
    def __init__(self):
        # ressources consommables
        self.steps = 1
        self.coins = 999
        self.gems = 999
        self.keys = 999
        self.dice = 999

        # objets permanents
        self.lockpick = True
        self.rabbit_foot = True
        self.metal_detector = True
        self.shovel = True

    # ============================================
    # CONSOMMATION
    # ============================================
    def use_step(self, n=1):
        self.steps -= n
        return self.steps

    def use_coins(self, n):
        if self.coins >= n:
            self.coins -= n
            return True
        return False

    def use_gems(self, n):
        if self.gems >= n:
            self.gems -= n
            return True
        return False

    def use_keys(self, n=1):
        if self.keys >= n:
            self.keys -= n
            return True
        return False

    def use_dice(self, n=1):
        if self.dice >= n:
            self.dice -= n
            return True
        return False

    # ============================================
    # AJOUT
    # ============================================
    def add_steps(self, n):
        self.steps += n

    def add_coins(self, n):
        self.coins += n

    def add_gems(self, n):
        self.gems += n

    def add_keys(self, n):
        self.keys += n

    def add_dice(self, n):
        self.dice += n

    # ============================================
    # PERMANENTS
    # ============================================
    def add_permanent(self, name):
        if name == "lockpick":
            self.lockpick = True
        elif name == "rabbit_foot":
            self.rabbit_foot = True
        elif name == "metal_detector":
            self.metal_detector = True

    def has_permanent(self, name):
        if name == "lockpick":
            return self.lockpick
        if name == "rabbit_foot":
            return self.rabbit_foot
        if name == "metal_detector":
            return self.metal_detector
        return False

    # ============================================
    # PORTES (simplifié)
    # ============================================
    def can_open(self, lock_level: int) -> bool:
        if lock_level == 0:
            return True
        if lock_level == 1:
            # 1 clé OU lockpick
            return self.keys >= 1 or self.lockpick
        if lock_level == 2:
            # 2 clés nécessaires
            return self.keys >= 2
        return False

    def spend_for_lock(self, lock_level: int):
        # Ne rien faire pour 0
        if lock_level <= 0:
            return

        if lock_level == 1:
            # on privilégie la clé si dispo
            if self.keys >= 1:
                self.keys -= 1
            # sinon lockpick utilisé "gratuitement"
            # (si tu veux que lockpick soit consommé, ajoute un flag ici)
        elif lock_level == 2:
            # consomme 2 clés (en supposant que can_open a été vérifié avant)
            if self.keys >= 2:
                self.keys -= 2
