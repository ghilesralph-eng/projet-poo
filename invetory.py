
# defining inventory 

class Consumables ():

    def __init__(self):
        self.steps = 70
        self.coins = 0
        self.gems = 2
        self.keys = 0
        self.dices = 0
    
    def use(self,name,n):

        try: 
            value = getattr(self,name)
        except AttributeError:
            print(f"the consumable {name} isnt defined in the game")
            return False
    
        if n > value :
            print(f'Not enough {name}')
            return False
     
        new_val = value - n
        setattr(self, name, new_val )
        print(f'-{n} {name}')
        return True
    
    def use_steps(self,n):
        return self.use("steps",1)
    
    def use_coins(self,n):
        return self.use("coins",n)
    
    def use_gems(self,n):
        return self.use("gems", n)
    
    def use_keys(self,n=1):
        if n > 2:
            print(f"there is no door with more than 2 locks")
            return False
        
        return self.use("keys", n)
    
    def use_dices(self,n):
        return self.use("dices", n)
        
    
    def add_loot (self , name , n):

        try:
            value = getattr(self, name)
        except AttributeError:
            print(f"the consumable {name} isnt defined in the game")
            return False
        
        if n < 0: 
            print(f"loot {name} can't be negative")
            return False
        
        new_val = n + value
        setattr(self,name, new_val)
        print(f"+{n} {name}")
        return True
        
    def add_steps(self, n):
        return self.add_loot("steps",n)  
          
    def add_coins(self, n):
        return self.add_loot("coins",n) 
          
    def add_gems(self, n):
        return self.add_loot("gems",n) 
          
    def add_keys(self, n):
        return self.add_loot("keys",n)
     
          
    def add_dices(self, n):
        return self.add_loot("dices",n)
    
    
    

class Permanants():

    def __init__(self):
        self.shovel = False
        self.hammer = False
        self.lockpick = False
        self.metaldetector = False
        self.paw = False

    def pickpermaloot(self,name):

        try:
            state = getattr(self,name)
        except AttributeError:
            print(f"{name} isnt defined in the game")
            return False

        if type(state) is not bool:
            print(f"{name} has to be of boolean type")
            return False
             
        if state is True:
            print(f"{name} already aquired.")
            return True
        
        setattr(self,name,True)
        return True

    def has_item(self,name):

        try:
            return getattr(self, name)
        except AttributeError:
            print(f"item {name} isnt defined in the game, check for spelling mistake")
            return False
      
class Inventory():

    def __init__(self):
        self.permanants= Permanants()
        self.consumables = Consumables()

        


        


