
import os
import shutil
import argparse
import pandas as pd
from tqdm import tqdm

def reorganize_by_ethnicity(csv_path, source_dir, target_ethnicity, action='move'):
    """
    Reorganizes images within the source directory into subdirectories based on ethnicity.

    For each {gender}/{age_group} folder, it creates subdirectories for the
    target ethnicity (e.g., 'asian') and 'other', then moves the images
    from the parent folder into the appropriate new subdirectory.

    Args:
        csv_path (str): Path to the FFHQ_Demographics.csv file.
        source_dir (str): Path to the directory containing images to be reorganized.
        target_ethnicity (str): The primary ethnicity to create a folder for (e.g., 'Asian').
        action (str): 'copy' or 'move'. Defaults to 'move' for reorganization.
    """
    try:
        print(f"Reading demographics from {csv_path}...")
        df = pd.read_csv(csv_path)
        # Create a dictionary for fast lookup: filename -> ethnicity
        ethnicity_map = df.set_index('File')['Ethnic'].to_dict()
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        return
    except KeyError:
        print(f"Error: CSV file must contain 'File' and 'Ethnic' columns.")
        return

    print(f"Reorganizing directory '{source_dir}' for ethnicity '{target_ethnicity}' (action: {action})...")

    # This regex is to find directories like 'male/15-19' but not 'male/15-19/asian'
    # We walk the directory and collect paths to process.
    image_paths_to_process = []
    for root, dirs, files in os.walk(source_dir):
        # We only want to process files in the {gender}/{age_group} directories,
        # not in the new ethnicity subdirs we are about to create.
        if target_ethnicity.lower() in root.lower() or 'other' in root.lower():
            continue

        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_paths_to_process.append(os.path.join(root, file))

    if not image_paths_to_process:
        print(f"No images found to reorganize in the source directory: {source_dir}")
        return

    processed_count = 0
    skipped_count = 0
    for image_path in tqdm(image_paths_to_process, desc="Reorganizing by ethnicity"):
        filename = os.path.basename(image_path)
        
        image_ethnicity = ethnicity_map.get(filename)
        
        dest_subdir_name = 'other' # Default to 'other'
        if image_ethnicity and image_ethnicity.lower() == target_ethnicity.lower():
            dest_subdir_name = target_ethnicity.lower()
            
        parent_dir = os.path.dirname(image_path)
        dest_dir = os.path.join(parent_dir, dest_subdir_name)
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, filename)

        if image_path == dest_path: # Should not happen, but a safeguard
            continue

        if os.path.exists(dest_path):
            skipped_count += 1
            # If destination exists, we might want to remove the source if action is 'move'
            if action == 'move' and os.path.exists(image_path):
                os.remove(image_path)
            continue

        try:
            if action == 'copy':
                shutil.copyfile(image_path, dest_path)
            elif action == 'move':
                shutil.move(image_path, dest_path)
            processed_count += 1
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            skipped_count += 1

    print("\n-------------------------------------------------")
    print("Demographic reorganization complete!")
    print(f"Reorganized images within: {source_dir}")
    print(f"Successfully {action}ed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} images (e.g., not in CSV, or already reorganized).")
    print("-------------------------------------------------")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Reorganize FFHQ dataset by demographics.")
    parser.add_argument(
        '--csv_path',
        type=str,
        required=True,
        help="Path to the demographics CSV file (e.g., Data/FFHQ/FFHQ_Demographics.csv)."
    )
    parser.add_argument(
        '--source_dir',
        type=str,
        required=True,
        help="Directory containing the images to reorganize (e.g., Data/FFHQ/ffhq_sorted)."
    )
    parser.add_argument(
        '--target_ethnicity',
        type=str,
        required=True,
        help="The target ethnicity to create a specific folder for (e.g., 'Asian')."
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['copy', 'move'],
        default='move',
        help="Action to perform on files: 'move' (default) or 'copy'."
    )

    args = parser.parse_args()
    
    reorganize_by_ethnicity(args.csv_path, args.source_dir, args.target_ethnicity, args.action)
