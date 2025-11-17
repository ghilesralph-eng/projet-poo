from inventory.inventory import Inventory

class Player:

    def __init__(self,x= 3,y= 1):
        self.x = x
        self.y = y
        self.inventory= Inventory()

    def move(self,dx,dy):
        self.x += dx
        self.y += dy

    def __str__(self):
        return f"Player at ({self.x}, {self.y})"
    
#forwarding use methods

    def use_step(self):
        return self.inventory.use_step()
    
    def use_coins(self,n):
        return self.inventory.use_coins(n)
    
    def use_gems(self,n):
        return self.inventory.use_gems(n)
    
    def use_keys(self,n=1):
        return self.inventory.use_keys(n)
    
    def use_dice(self):
        return self.inventory.use_dice()  
    
#forwarding use methods

    def use_step(self):
        return self.inventory.use_step()
    
    def use_coins(self,n):
        return self.inventory.use_coins(n)
    
    def use_gems(self,n):
        return self.inventory.use_gems(n)
    
    def use_keys(self,n=1):
        return self.inventory.use_keys
    
    def use_dice(self,n):
        return self.inventory.use_dice()    

#forwarding add methods

    def add_step(self,n):
        return self.inventory.add_step(n)
    
    def add_coins(self,n):
        return self.inventory.add_coins(n)
    
    def add_gems(self,n):
        return self.inventory.add_gems(n)
    
    def add_keys(self,n):
        return self.inventory.add_keys(n)
    
    def add_dice(self,n):
        return self.inventory.add_dice(n)
    
#forwarding permanants methods  

    def pickpermaloot(self,name):
        return self.inventory.pickpermaloot(name)       
    
    def has_permanent(self,name):
        return self.inventory.has_permanent(name) 