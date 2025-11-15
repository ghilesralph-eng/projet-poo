class Consumables ():

    def __init__(self):
        self.data = {
            
            "step": 70,
            "coins": 0,
            "gems": 2,
            "keys": 0,
            "dices": 0
        }
    
    def use(self,name,n):

        if name not in self.data:
            print(f"the consumable {name} isnt defined in the game")
            return False
        
        value= self.data[name]
        if n > value:
            print(f'Not enough {name}')
            return False
        
        self.data[name] = value - n
        print(f'-{n} {name}')
        return True
    
    def use_step(self):
        return self.use("step",1)
    
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

        if name not in self.data:
            print(f"the consumable {name} isnt defined in the game, check for spelling mistake")
            return False
        
        if n < 0: 
            print(f"loot {name} can't be negative")
            return False
        
        self.data[name] += n      
        print(f"+{n} {name}")
        return True
        
    def add_step(self, n):
        return self.add_loot("step",n)  
          
    def add_coins(self, n):
        return self.add_loot("coins",n) 
          
    def add_gems(self, n):
        return self.add_loot("gems",n) 
          
    def add_keys(self, n):
        return self.add_loot("keys",n)
          
    def add_dices(self, n):
        return self.add_loot("dices",n)
    
    def __str__(self):
        parts = [f"{key.capitalize()}: {val}" for key, val in self.data.items()]
        return ", ".join(parts)


