import os
import shutil
from pathlib import Path

def prepare_survey_dataset():
    # Configuration
    source_root = Path("Data/FFHQ/ffhq_sorted")
    dest_root = Path("Data/FFHQ/ffhq_for_survey")
    
    # Define groups and their corresponding list files
    groups = {
        "OK_4.0": "output/high_quality_images.txt",
        "not-OK_2.0": "output/low_quality_images.txt"
    }

    # Check source directory
    if not source_root.exists():
        print(f"Error: Source directory '{source_root}' not found.")
        return

    # Create destination directories and copy files
    for group_name, list_file in groups.items():
        dest_dir = dest_root / group_name
        
        if not os.path.exists(list_file):
            print(f"Warning: List file '{list_file}' not found. Skipping group '{group_name}'.")
            continue

        print(f"\nProcessing group: {group_name}")
        print(f"Creating directory: {dest_dir}")
        dest_dir.mkdir(parents=True, exist_ok=True)

        with open(list_file, 'r') as f:
            files = [line.strip() for line in f if line.strip()]

        count = 0
        for rel_path in files:
            # rel_path is like "female/20-29/asian/xxxx.png"
            # source path is Data/FFHQ/ffhq_sorted/female/20-29/asian/xxxx.png
            
            src_file = source_root / rel_path
            
            # Destination: Flatten the structure or keep it? 
            # Let's keep the filename only to avoid deep nesting in the dataset folder,
            # or we can keep structure. For a clean dataset folder, flattening is often easier
            # if filenames are unique. FFHQ filenames (integers) are unique across the whole dataset.
            # But just in case, let's check uniqueness or just copy the file.
            
            # To avoid potential name collisions (though unlikely in FFHQ original), 
            # we will copy to the root of the group folder.
            dest_file = dest_dir / src_file.name

            if src_file.exists():
                if dest_file.exists():
                    os.remove(dest_file) # Remove existing file/link to ensure update
                # Create symbolic link instead of copying
                os.symlink(src_file.resolve(), dest_file)
                count += 1
            else:
                print(f"  Warning: Source file not found: {src_file}")

        print(f"Successfully linked {count} images to {dest_dir}")

    print("\nDataset preparation complete.")

if __name__ == "__main__":
    prepare_survey_dataset()
