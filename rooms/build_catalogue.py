import sys
import os
# Import the new types we need from the 'typing' toolkit
from room_data import RoomDef # Import our 'blueprint'
from typing import List, Tuple, Optional, Union, Dict

# --- Helper functions to get clean input ---

def get_color_for_room(room_number: int) -> str:
    """Applies the user's bulk-entry rules for colors."""
    if 1 <= room_number <= 45:
        return "blue"
    elif 46 <= room_number <= 53:
        return "purple"
    elif 54 <= room_number <= 61:
        return "brown" # Using "brown" as requested
    elif 62 <= room_number <= 69:
        return "green"
    elif 70 <= room_number <= 77:
        return "yellow"
    elif 78 <= room_number <= 85:
        return "red"
    return "blue" # Fallback (shouldn't be hit)

def get_row_range_for_blue_room(room_number: int) -> Optional[Tuple[int, int]]:
    """Applies the user's logic for blue room row ranges."""
    if 1 <= room_number <= 12:
        return (1, 12)
    elif 13 <= room_number <= 24:
        return (13, 24)
    elif 25 <= room_number <= 36:
        return (25, 36)
    elif 37 <= room_number <= 45:
        return (37, 45)
    return None

def get_mandatory_string(prompt: str) -> str:
    """Gets a non-empty string from the user. 'exit' quits."""
    while True:
        val = input(f"  {prompt}: ").strip()
        if val.lower() == 'exit':
            sys.exit(0)
        if val:
            return val
        print("    ERROR: This value cannot be empty.")

def get_optional_string(prompt: str) -> Optional[str]:
    """Gets a string, or None if the user types 'none' or hits Enter."""
    val = input(f"  {prompt} (press Enter or type 'none' to skip): ").strip()
    if val == '' or val.lower() == 'none':
        return None
    return val

# NEW: Handles single int OR ranged int (min, max)
def get_ranged_int(prompt: str, default: int = 0) -> Union[int, Tuple[int, int]]:
    """Gets an integer OR an inclusive (min, max) tuple."""
    while True:
        val = input(f"  {prompt} (e.g., '5' or '3,7', default: {default}): ").strip()
        if val == '':
            return default
        if val.lower() == 'exit':
            sys.exit(0)
        
        try:
            if ',' in val:
                # This is a range
                parts = val.replace(' ', ',').split(',')
                if len(parts) != 2: raise ValueError
                min_val = int(parts[0].strip())
                max_val = int(parts[1].strip())
                # Return the auto-sorted (min, max) tuple
                return (min(min_val, max_val), max(min_val, max_val))
            else:
                # This is a single number
                return int(val)
        except (ValueError, TypeError):
            print(f"    ERROR: Invalid. Must be a single number '5' or a range '3,7'.")

def get_doors() -> Tuple[bool, bool, bool, bool]:
    """Gets the four door values from the user."""
    print("  Enter doors (U, R, D, L). Example: 'U,R,L' for Up, Right, Left")
    while True:
        val = input("    Doors (U,R,D,L): ").strip().upper().replace(',', '')
        
        up = 'U' in val
        right = 'R' in val
        down = 'D' in val
        left = 'L' in val
        
        print(f"    > Got: Up={up}, Right={right}, Down={down}, Left={left}. Is this correct? (Y/n)")
        confirm = input("    ").strip().lower()
        if confirm == '' or confirm == 'y':
            return (up, right, down, left)

# NEW: Helper function to get objects and their counts/ranges
def get_objects() -> Dict[str, Tuple[int, int]]:
    """Loops and asks for objects and their (min, max) counts."""
    objects_dict = {}
    print("  --- Add Objects ---")
    while True:
        # 1. Get object name
        obj_name = input("    Object Name (e.g., 'chest', or 'none' to finish): ").strip()
        if obj_name == '' or obj_name.lower() == 'none':
            break # Finished adding objects
        if obj_name.lower() == 'exit':
            sys.exit(0)
        
        # 2. Get count/range for this object (mandatory)
        while True: 
            count_val = input(f"      Count/Range for '{obj_name}' (e.g., '1' or '1,3'): ").strip()
            if count_val == '' or count_val.lower() == 'none':
                print("      ERROR: You must provide a count or range.")
                continue
            if count_val.lower() == 'exit':
                sys.exit(0)
            
            try:
                if ',' in count_val:
                    # This is a range
                    parts = count_val.replace(' ', ',').split(',')
                    if len(parts) != 2: raise ValueError
                    min_val = int(parts[0].strip())
                    max_val = int(parts[1].strip())
                    objects_dict[obj_name] = (min(min_val, max_val), max(min_val, max_val))
                    break # Success, break inner loop
                else:
                    # This is a single number, store as (count, count)
                    count = int(count_val)
                    objects_dict[obj_name] = (count, count) 
                    break # Success, break inner loop
            except (ValueError, TypeError):
                print(f"      ERROR: Invalid. Must be a single number '1' or a range '1,3'.")
    
    print("  ---------------------")
    return objects_dict

# ---------------------------------------------------
# --- MAIN SCRIPT (UPDATED)
# ---------------------------------------------------

def build_catalogue():
    print("--- Room Catalogue Builder ---")
    print("Enter 'exit' at any time to quit.")
    print("Press Enter or type 'none' for optional fields.\n")

    all_rooms: List[RoomDef] = []

    for i in range(1, 86): 
        print(f"\n--- Adding Room {i} of 85 ---")
        
        try:
            # --- Mandatory fields ---
            new_name = get_mandatory_string("Name (e.g., 'Vault')")
            
            new_color = get_color_for_room(i)
            print(f"  > Auto-set Color: {new_color}")

            filename_base = new_name.lower().replace(' ', '_')
            new_image_path = f"images/{filename_base}.png"
            print(f"  > Auto-generated Image Path: {new_image_path}")
            
            # UPDATED: Use get_ranged_int
            new_rarity = get_ranged_int("Rarity (0-3)", default=0)
            new_gem_cost = get_ranged_int("Gem Cost", default=0)
            
            new_doors = get_doors()

            # --- Optional fields ---
            new_allowed_rows = None
            if new_color == "blue":
                new_allowed_rows = get_row_range_for_blue_room(i)
                print(f"  > Auto-set Allowed Rows: {new_allowed_rows}")
            else:
                print(f"  > Auto-set Allowed Rows: None (not a blue room)")

            new_placement = get_optional_string("Placement Condition (e.g., 'border_only')")
            
            # --- Effect ---
            new_effect_id = get_optional_string("Effect ID (e.g., 'ADD_COINS')")
            new_effect_val = None
            if new_effect_id: 
                # UPDATED: Use get_ranged_int
                new_effect_val = get_ranged_int(f"Value for '{new_effect_id}'", default=0)
            
            # --- Objects ---
            # UPDATED: Use get_objects
            new_objects = get_objects()

            # 2. CREATE THE OBJECT
            new_room = RoomDef(
                name=new_name,
                color=new_color,
                image_path=new_image_path,
                rarity=new_rarity,
                gem_cost=new_gem_cost,
                doors=new_doors,
                placement_condition=new_placement,
                allowed_rows=new_allowed_rows,
                effect_id=new_effect_id,
                effect_value=new_effect_val,
                objects_in_room=new_objects
            )

            # 3. APPEND THE OBJECT
            all_rooms.append(new_room)
            print(f"\nSuccessfully added '{new_name}' to the catalogue.")

        except SystemExit:
            print("\nExiting builder...")
            break 
        except Exception as e:
            print(f"\nAn error occurred: {e}. Let's try that room again.")
            continue 

    # 4. PRINT THE FINAL, FORMATTED CODE
    print("\n\n" + "="*50)
    print("--- GENERATED PYTHON CODE ---")
    print("Copy the text below and paste it into 'ROOM_CATALOGUE' in room_data.py")
    print("="*50 + "\n")
    print("ROOM_CATALOGUE: List[RoomDef] = [")
    
    for room in all_rooms:
        print("    RoomDef(")
        print(f"        name=\"{room.name}\",")
        print(f"        color=\"{room.color}\",")
        print(f"        image_path=\"{room.image_path}\",")
        # These will print '5' or '(3, 7)' correctly
        print(f"        rarity={room.rarity},")
        print(f"        gem_cost={room.gem_cost},")
        print(f"        doors={room.doors},")
        
        if room.placement_condition:
            print(f"        placement_condition=\"{room.placement_condition}\",")
        if room.allowed_rows:
            print(f"        allowed_rows={room.allowed_rows},")
        if room.effect_id:
            print(f"        effect_id=\"{room.effect_id}\",")
        # Check for 'is not None' because 0 is a valid value
        if room.effect_value is not None:
            print(f"        effect_value={room.effect_value},")
        # Check if the dictionary is not empty
        if room.objects_in_room:
            print(f"        objects_in_room={room.objects_in_room},")
            
        print("    ),")
        
    print("]")
    print("\n" + "="*50)
    print("--- END OF CODE ---")
    print("="*50)

if __name__ == "__main__":
    build_catalogue()