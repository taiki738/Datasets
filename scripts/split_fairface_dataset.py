import os
import glob
import random
import shutil
from tqdm import tqdm

def split_dataset(input_dir, output_dir, split_ratio=0.8):
    """
    Splits a dataset of images into training and validation sets.

    The input directory should have subdirectories for each class,
    and this function will create a similar structure in the output directory.

    Args:
        input_dir (str): Path to the input directory.
        output_dir (str): Path to the output directory.
        split_ratio (float): The ratio of training data.
    """
    random.seed(42)  # for reproducibility

    # Create output directories
    train_dir = os.path.join(output_dir, 'train')
    val_dir = os.path.join(output_dir, 'val')

    if os.path.exists(output_dir):
        print(f"Output directory {output_dir} already exists. Removing it.")
        shutil.rmtree(output_dir)

    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(val_dir, exist_ok=True)

    classes = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]

    for cls in classes:
        print(f"Processing class: {cls}")
        os.makedirs(os.path.join(train_dir, cls), exist_ok=True)
        os.makedirs(os.path.join(val_dir, cls), exist_ok=True)

        class_dir = os.path.join(input_dir, cls)
        images = glob.glob(os.path.join(class_dir, '*.jpg')) # Assuming .jpg, adjust if needed
        random.shuffle(images)

        split_point = int(len(images) * split_ratio)
        train_images = images[:split_point]
        val_images = images[split_point:]

        print(f"  - Train images: {len(train_images)}")
        print(f"  - Validation images: {len(val_images)}")

        # Copy training images
        for img_path in tqdm(train_images, desc=f"Copying train {cls}"):
            shutil.copy(img_path, os.path.join(train_dir, cls))

        # Copy validation images
        for img_path in tqdm(val_images, desc=f"Copying val {cls}"):
            shutil.copy(img_path, os.path.join(val_dir, cls))

if __name__ == '__main__':
    # Note: Adjust these paths as needed
    input_dataset_dir = '../Data/FairFace/fairface_for_survey'
    output_dataset_dir = '../Data/FairFace/fairface_split'
    
    # Check if the input directory exists
    if not os.path.isdir(input_dataset_dir):
        print(f"Error: Input directory not found at '{input_dataset_dir}'")
        print("Please make sure the FairFace data is correctly placed.")
    else:
        split_dataset(input_dataset_dir, output_dataset_dir)
        print("\nDataset splitting complete.")
        print(f"Train and validation sets are in '{output_dataset_dir}'")
