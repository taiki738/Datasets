#!/bin/bash

# This script restores the 'filtered_dataset' from the 'demo_preferred' directory.
# It gathers all images from the 'kept' and 'discarded' subdirectories and
# copies them into a new, clean 'filtered_dataset' structure.

# --- Configuration ---
SOURCE_BASE="UTK-FACE/demo_preferred"
DEST_BASE="UTK-FACE/filtered_dataset"

# --- Main Logic ---

echo "Creating new 'filtered_dataset' directories..."
mkdir -p "$DEST_BASE/male"
mkdir -p "$DEST_BASE/female"

# Process for both genders
for gender in "male" "female"; do
    DEST_DIR="$DEST_BASE/$gender"
    
    # Process both 'kept' and 'discarded' subfolders
    for status in "kept" "discarded"; do
        SOURCE_DIR="$SOURCE_BASE/$gender/$status"
        
        if [ -d "$SOURCE_DIR" ]; then
            echo "Copying files from $SOURCE_DIR to $DEST_DIR..."
            # Use 'cp -n' to avoid overwriting if run multiple times
            # Use 'shopt -s nullglob' to handle empty directories gracefully
            shopt -s nullglob
            files=("$SOURCE_DIR"/*.jpg)
            if [ ${#files[@]} -gt 0 ]; then
                cp -n "${files[@]}" "$DEST_DIR/"
            else
                echo "No .jpg files found in $SOURCE_DIR."
            fi
            shopt -u nullglob
        else
            echo "Warning: Source directory $SOURCE_DIR not found. Skipping."
        fi
    done
done

echo
echo "Restoration complete."
echo "Total files in $DEST_BASE/male: $(ls -1 "$DEST_BASE/male" | wc -l)"
echo "Total files in $DEST_BASE/female: $(ls -1 "$DEST_BASE/female" | wc -l)"
