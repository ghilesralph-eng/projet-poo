import sys
from pathlib import Path
from PIL import Image, UnidentifiedImageError

# --- Configuration ---

# 1. Set the folder with your images
INPUT_FOLDER = Path("images")

# 2. Set a folder for the converted images
#    It's safer to save to a new folder!
OUTPUT_FOLDER = Path("pngs") 
# ---------------------

def convert_images_to_png(input_dir, output_dir):
    """
    Converts all valid images in input_dir to lowercase-named PNGs in output_dir.
    """
    
    # 1. Create the output folder if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning folder: {input_dir.resolve()}")
    print(f"Saving converted files to: {output_dir.resolve()}\n")
    
    converted_count = 0
    skipped_count = 0
    
    # 2. Loop through all files in the input folder
    for file_path in input_dir.iterdir():
        
        # 3. Process only files (skip sub-folders)
        if file_path.is_file():
            try:
                # 4. Open the file as an image
                with Image.open(file_path) as img:
                    
                    # 5. Create the new lowercase filename
                    # .stem gets the filename without the extension
                    new_filename = f"{file_path.stem.lower()}.png"
                    
                    # 6. Create the full new path
                    output_path = output_dir / new_filename
                    
                    # 7. Save the image in PNG format
                    # We use save() here, not convert().
                    # 'PNG' format is specified.
                    img.save(output_path, 'PNG')
                    
                    print(f"✅ Converted: {file_path.name}  ->  {output_path.name}")
                    converted_count += 1
                    
            except UnidentifiedImageError:
                # 8. Handle files that aren't images
                print(f"❌ Skipped:   {file_path.name} (not a recognized image)")
                skipped_count += 1
            except Exception as e:
                # 9. Handle other potential errors
                print(f"⚠️ Error:     {file_path.name} ({e})")
                skipped_count += 1
                
    print(f"\n--- Summary ---")
    print(f"Total images converted: {converted_count}")
    print(f"Total files skipped:    {skipped_count}")

# --- Main execution ---
if __name__ == "__main__":
    if not INPUT_FOLDER.is_dir():
        print(f"Error: Input folder not found at {INPUT_FOLDER.resolve()}")
        print("Please edit the INPUT_FOLDER variable in the script.")
        sys.exit(1)
        
    convert_images_to_png(INPUT_FOLDER, OUTPUT_FOLDER)