#!/bin/bash

# Script to merge CSV files in a specified folder
# Usage: ./csv_merger.sh <folder_path> [output_file]

# Check if the folder path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <folder_path> [output_file]"
    exit 1
fi

# Variables
FOLDER="$1"
OUTPUT_FILE="${2:-merged.csv}" # Default output file name is "merged.csv"

# Check if the folder exists
if [ ! -d "$FOLDER" ]; then
    echo "Error: Directory '$FOLDER' does not exist."
    exit 1
fi

# Change to the target folder
cd "$FOLDER" || exit

# Check for CSV files in the folder
CSV_FILES=(*.csv)
if [ ${#CSV_FILES[@]} -eq 0 ]; then
    echo "Error: No CSV files found in the directory '$FOLDER'."
    exit 1
fi

# Merge the CSV files
{
    head -n 1 "${CSV_FILES[0]}" # Add the header from the first file
    for FILE in "${CSV_FILES[@]}"; do
        tail -n +2 "$FILE" # Append all data excluding headers
    done
} > "$OUTPUT_FILE"

# Print success message
echo "Merged ${#CSV_FILES[@]} CSV files into '$FOLDER/$OUTPUT_FILE'"
