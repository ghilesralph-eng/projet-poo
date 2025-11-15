class Permanants():

    def __init__(self):
        self.data = set()

        self.valid_items = {"shovel", "hammer", "lockpick", "metaldetector", "paw"}


    def pickpermaloot(self,name):

        if name not in self.valid_items:
            print(f"{name} isnt defined in the game")
            return False
        

        if name in self.data:
            print(f"{name} already acquired.")
            return True
             
        self.data.add(name)
        print(f"Acquired {name}!")
        return True


    def has_item(self, name):
        return name in self.data

      
    def __str__(self):
        if not self.data:
            return "None"
        # Sorts the set for a clean, consistent print
        return ", ".join(sorted(self.data))
    