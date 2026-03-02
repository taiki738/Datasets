import pandas as pd
import os

def analyze_dataset():
    # File paths
    # Note: Assuming the script is run from the project root
    label_csv_path = 'DB/2026-0107/_label__202601071130.csv'
    image_csv_path = 'DB/2026-0107/image_202601071129.csv'

    # Check if files exist
    if not os.path.exists(label_csv_path) or not os.path.exists(image_csv_path):
        print(f"Error: CSV files not found in the current directory.")
        print(f"Expected: {label_csv_path} and {image_csv_path}")
        return

    # Load data
    print("Loading CSV files...")
    try:
        labels_df = pd.read_csv(label_csv_path)
        images_df = pd.read_csv(image_csv_path)
    except Exception as e:
        print(f"Error reading CSV files: {e}")
        return

    # Calculate average rating for each image
    print("Calculating average ratings...")
    # Group by image_id and calculate mean rating
    image_ratings = labels_df.groupby('image_id')['rating'].agg(['mean', 'count']).reset_index()
    image_ratings.columns = ['id', 'average_rating', 'rating_count']

    # Merge with image details to get filenames
    # Use 'id' from images_df and 'id' from image_ratings
    merged_df = pd.merge(images_df, image_ratings, on='id', how='inner')

    # Filter into groups
    high_quality = merged_df[merged_df['average_rating'] >= 4.0]
    low_quality = merged_df[merged_df['average_rating'] <= 2.0]
    middle_quality = merged_df[(merged_df['average_rating'] > 2.0) & (merged_df['average_rating'] < 4.0)]

    # Print statistics
    print("\n--- Analysis Results ---")
    print(f"Total images evaluated: {len(merged_df)}")
    print(f"High Quality (Score >= 4.0): {len(high_quality)} images")
    print(f"Low Quality  (Score <= 2.0): {len(low_quality)} images")
    print(f"Middle Quality (2.0 < Score < 4.0): {len(middle_quality)} images")

    # Export file lists
    print("\nExporting file lists...")
    
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    high_quality_path = os.path.join(output_dir, 'high_quality_images.txt')
    low_quality_path = os.path.join(output_dir, 'low_quality_images.txt')
    
    with open(high_quality_path, 'w') as f:
        f.write('\n'.join(high_quality['filename'].tolist()))
    
    with open(low_quality_path, 'w') as f:
        f.write('\n'.join(low_quality['filename'].tolist()))

    print(f"Created '{high_quality_path}' with {len(high_quality)} entries.")
    print(f"Created '{low_quality_path}' with {len(low_quality)} entries.")

if __name__ == "__main__":
    analyze_dataset()
