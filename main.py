from player import Player
from manor import Manor

# --- Create your core game objects ---
player = Player(4, 4) # Your Player class
manor = Manor()       # Your NEW Manor class

# --- Run your tests ---
print("--- TESTING ---")
print(f"Player's steps: {player.inventory.consumables.data['step']}")
player.use_step()
print(f"Player's steps now: {player.inventory.consumables.data['step']}")

# Test the manor logic
candidates = manor.draw_candidates(r=4, c=3, from_dir='up')
print("\nDrew 3 candidate rooms:")
for room in candidates:
    print(f"- {room.name} (Cost: {room.gem_cost})")