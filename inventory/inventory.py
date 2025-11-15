from permanants import Permanants
from consumables import Consumables

class Inventory():

    def __init__(self):
        self.permanants= Permanants()
        self.consumables = Consumables()

    # method forwarding 


    # Consumables methods forwarding
    # use methods forwarding
    def use_step(self):
        return self.consumables.use_step()
    
    def use_coins(self,n):
        return self.consumables.use_coins(n)
    
    def use_gems(self,n):
        return self.consumables.use_gems(n)
    
    def use_keys(self,n=1):
        return self.consumables.use_keys(n)
    
    def use_dice(self):
        return self.consumables.use_dice()
    

    # add methods forwarding
    def add_step(self, n):
        return self.consumables.add_step(n)

    def add_coins(self, n):
        return self.consumables.add_coins(n)
    
    def add_gems(self, n):
        return self.consumables.add_gems(n)
    
    def add_keys(self, n):
        return self.consumables.add_keys(n)
    
    def add_dice(self, n):
        return self.consumables.add_dice(n)
    
    # Permanants methods forwarding
    
    def pickpermaloot(self,name):
        return self.permanants.pickpermaloot(name)
    
    def has_permanent(self, name):
        return self.permanants.has_item(name)

        


        


