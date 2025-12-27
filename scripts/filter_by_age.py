
import os
import shutil
import argparse
import pandas as pd
from tqdm import tqdm

def filter_ffhq_by_age(csv_path, source_dir, output_dir, age_groups, action='copy'):
    """
    Filters FFHQ images based on specified age groups and copies/moves them to an output directory.

    Args:
        csv_path (str): Path to the ffhq_aging_labels.csv file.
        source_dir (str): Path to the directory containing gender-sorted FFHQ images (e.g., Data/FFHQ/ffhq_sorted).
                          This directory should contain 'male' and 'female' subdirectories.
        output_dir (str): Path to the base directory where age-filtered images will be saved,
                          creating nested gender/age_group subdirectories (e.g., Data/FFHQ/ffhq_sorted).
        age_groups (list): A list of age group strings to filter by (e.g., ['15-19', '20-29']).
        action (str): 'copy' to copy files, 'move' to move files. Defaults to 'copy'.
    """
    # The output_dir should be the base where gender/age subdirs will be created
    # No need to os.makedirs(output_dir, exist_ok=True) here directly, as nested ones will be made.

    try:
        print(f"Reading labels from {csv_path}...")
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: The file '{csv_path}' was not found.")
        return

    required_columns = {'image_number', 'gender', 'age_group'}
    if not required_columns.issubset(df.columns):
        print(f"Error: CSV file must contain the following columns: {required_columns}")
        return

    # Filter by age groups
    filtered_df = df[df['age_group'].isin(age_groups)]
    
    if filtered_df.empty:
        print(f"No images found for the specified age groups: {age_groups}")
        return

    print(f"Found {len(filtered_df)} images matching age groups {age_groups}. Starting filtering (action: {action})...")

    processed_count = 0
    skipped_count = 0
    for _, row in tqdm(filtered_df.iterrows(), total=filtered_df.shape[0], desc="Filtering images by age"):
        image_id = str(row['image_number']).strip().zfill(5)
        gender_label = row['gender']
        age_group_label = str(row['age_group']).strip() # Get the age group from the row
        
        source_filename = f"{image_id}.png"
        
        # Determine the source gender subdirectory
        gender_subdir = ''
        if gender_label == 'male':
            gender_subdir = 'male'
        elif gender_label == 'female':
            gender_subdir = 'female'
        else:
            skipped_count += 1
            continue # Skip if gender label is not 'male' or 'female'

        # Construct the full destination path with nested gender/age_group subdirectories
        age_group_dest_dir = os.path.join(output_dir, gender_subdir, age_group_label)
        os.makedirs(age_group_dest_dir, exist_ok=True) # Ensure this new age group dir exists

        source_path = os.path.join(source_dir, gender_subdir, source_filename)
        dest_path = os.path.join(age_group_dest_dir, source_filename)

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
            print(f"Error processing {source_path}: {e}")
            skipped_count += 1

    print("\n-------------------------------------------------")
    print("Age-based filtering complete!")
    print(f"Filtered images are saved in: {output_dir}")
    print(f"Successfully processed {processed_count} images.")
    if skipped_count > 0:
        print(f"Skipped {skipped_count} images due to errors, not found, or already existing in destination.")
    print("-------------------------------------------------")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Filter FFHQ dataset by age groups.")
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
        help="Directory containing gender-sorted FFHQ images (e.g., Data/FFHQ/ffhq_sorted)."
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        required=True,
        help="Base directory where the age-filtered images will be saved, creating nested gender/age_group subdirectories (e.g., Data/FFHQ/ffhq_sorted)."
    )
    parser.add_argument(
        '--age_groups',
        type=str,
        required=True,
        help="Comma-separated list of age groups to filter by (e.g., '15-19,20-29')."
    )
    parser.add_argument(
        '--action',
        type=str,
        choices=['copy', 'move'],
        default='copy',
        help="Action to perform on files: 'copy' (default) or 'move'. Use 'move' with caution."
    )

    args = parser.parse_args()
    
    # Split the comma-separated string into a list of age groups
    age_groups_list = [ag.strip() for ag in args.age_groups.split(',')]
    
    filter_ffhq_by_age(args.csv_path, args.source_dir, args.output_dir, age_groups_list, args.action)
