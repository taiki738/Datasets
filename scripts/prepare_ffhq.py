
import os
import shutil
import argparse
import pandas as pd
from tqdm import tqdm

"""
This script prepares the FFHQ dataset for the labeling survey by sorting
pre-existing FFHQ images into 'male' and 'female' directories based on
the labels from the FFHQ-Aging-Dataset.

This script does NOT perform resizing. It assumes the source images are
already the desired size.

Prerequisites:
1. You must have downloaded an FFHQ dataset containing images.
2. You must have downloaded the FFHQ-Aging-Dataset, specifically the `ffhq_aging_labels.csv` file.
3. Required Python libraries must be installed. You can install them using pip:
   pip install pandas tqdm

How to run the script:
1. Make sure the FFHQ images are in a single directory.
2. Run the script from the root directory of the project, providing the necessary paths.

Example:
# Process the first 1000 images, copying them (default action)
python scripts/prepare_ffhq.py \\
    --csv_path "/path/to/your/ffhq_aging_labels.csv" \\
    --source_dir "/path/to/your/ffhq-images-source/" \\
    --output_dir "./Data/FFHQ_sorted" \\
    --limit 1000

# Process the entire dataset, moving files instead of copying (use with caution!)
python scripts/prepare_ffhq.py \\
    --csv_path "/path/to/your/ffhq_aging_labels.csv" \\
    --source_dir "/path/to/your/ffhq-images-source/" \\
    --output_dir "./Data/FFHQ_sorted" \\
    --action move
"""

def sort_ffhq_dataset(csv_path, source_dir, output_dir, action='copy', limit=None):
    """
    Sorts pre-resized FFHQ images based on gender labels from a CSV file.

    Args:
        csv_path (str): Path to the ffhq_aging_labels.csv file.
        source_dir (str): Path to the directory containing FFHQ .png images.
        output_dir (str): Path to the directory where sorted images will be saved.
        action (str): 'copy' to copy files, 'move' to move files. Defaults to 'copy'.
        limit (int, optional): Maximum number of images to process. Defaults to None (process all).
    """
    # Create output directories
    male_dir = os.path.join(output_dir, 'male')
    female_dir = os.path.join(output_dir, 'female')
    os.makedirs(male_dir, exist_ok=True)
    os.makedirs(female_dir, exist_ok=True)

    # Load the labels
    try:
        print(f"Reading labels from {csv_path}...")
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        return
        
    # The 'gender' column in FFHQ-Aging is 'male' or 'female'.
    # The 'image_id' column contains the base filename without extension.
    required_columns = {'image_number', 'gender'}
    if not required_columns.issubset(df.columns):
        print(f"Error: CSV file must contain the following columns: {required_columns}")
        return

    if limit is not None:
        print(f"Limiting processing to the first {limit} images from the CSV.")
        df = df.head(limit)

    print(f"Found {len(df)} labels. Starting image sorting (action: {action})...")

    # Process each image
    processed_count = 0
    skipped_count = 0
    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Sorting images"):
        image_id = str(row['image_number']).strip().zfill(5)
        gender_label = row['gender']
        
        source_filename = f"{image_id}.png"
        # Accommodate for the nested directory structure, e.g., images1024x1024/01000/01234.png
        # For image_id '01234', the folder_name will be '01000'.
        folder_name = str(int(image_id) // 1000 * 1000).zfill(5)
        source_path = os.path.join(source_dir, folder_name, source_filename)
        
        if gender_label == 'male': # Male
            dest_path = os.path.join(male_dir, source_filename)
        elif gender_label == 'female': # Female
            dest_path = os.path.join(female_dir, source_filename)
        else:
            continue # Skip if gender label is not 'male' or 'female'

        # Skip if the destination file already exists
        if os.path.exists(dest_path):
            skipped_count += 1
            continue

        if not os.path.exists(source_path):
            skipped_count += 1
            continue

        try:
            if action == 'copy':
                shutil.copyfile(source_path, dest_path)
            elif action == 'move':
                shutil.move(source_path, dest_path)
            processed_count += 1
        except Exception as e:
            print(f"Error processing {source_path} with action '{action}': {e}")
            skipped_count += 1

    print("\n-------------------------------------------------")
    print("Dataset sorting complete!")
    print(f"Sorted images are saved in: {output_dir}")
    print(f"Successfully processed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} images due to errors or not found or already existing in destination.")
    print("-------------------------------------------------")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Sort FFHQ dataset for labeling survey.")
    parser.add_argument(
        '--csv_path',
        type=str,
        required=True,
        help="Path to the ffhq_aging_labels.csv file."
    )
    parser.add_argument(
        '--source_dir',
        type=str,
        required=True,
        help="Directory containing the FFHQ .png images (e.g., images1024x1024)."
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help="Directory where the sorted images will be saved (e.g., ./Data/FFHQ_sorted)."
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['copy', 'move'],
        default='copy',
        help="Action to perform on files: 'copy' (default) or 'move'. Use 'move' with caution."
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help="Maximum number of images to process from the CSV. Defaults to all images."
    )

    args = parser.parse_args()
    sort_ffhq_dataset(args.csv_path, args.source_dir, args.output_dir, args.action, args.limit)
