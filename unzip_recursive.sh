#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <source_directory> <destination_directory>"
  exit 1
fi

source_dir="$1"
dest_dir="$2"

# Check if the source directory exists
if [ ! -d "$source_dir" ]; then
  echo "Error: Source directory '$source_dir' not found."
  exit 1
fi

# Check if the destination directory exists. If not, create it.
if [ ! -d "$dest_dir" ]; then
    echo "Destination directory '$dest_dir' not found. Creating it."
    mkdir -p "$dest_dir" || { echo "Failed to create destination directory"; exit 1; }
fi

# Function to recursively unzip files while preserving directory structure
unzip_recursive() {
  local src="$1"
  local dst="$2"

  find "$src" -type f \( -name "*.zip" -o -name "*.rar" -o -name "*.tar.gz" -o -name "*.tgz" -o -name "*.tar.bz2" -o -name "*.tbz2" -o -name "*.tar" -o -name "*.7z" \) -print0 | while IFS= read -r -d $'\0' file; do
    # Get the relative path of the file from the source directory
    relative_path="${file#"$src/"}"

    # Construct the destination path
    dest_file="${dst}/${relative_path%.*}" #Remove the extension

    # Create the necessary destination directories
    mkdir -p "$(dirname "$dest_file")"

    # Extract the filename without the extension for directory name
    filename=$(basename "$file")
    extension="${filename##*.}"
    filename="${filename%.*}"
    output_dir="$dest_file"

    # Determine the correct command based on the file extension
    case "$extension" in
      zip)
        echo "Unzipping: $file to $output_dir"
        unzip -q "$file" -d "$output_dir" || echo "Error unzipping $file"
        ;;
      rar)
        echo "Unraring: $file to $output_dir"
        unrar x "$file" "$output_dir" || echo "Error unraring $file"
        ;;
      tar.gz|tgz)
        echo "Extracting: $file to $output_dir"
        tar -xzf "$file" -C "$output_dir" || echo "Error extracting $file"
        ;;
      tar.bz2|tbz2)
        echo "Extracting: $file to $output_dir"
        tar -xjf "$file" -C "$output_dir" || echo "Error extracting $file"
        ;;
      tar)
        echo "Extracting: $file to $output_dir"
        tar -xf "$file" -C "$output_dir" || echo "Error extracting $file"
        ;;
        7z)
          echo "Extracting: $file to $output_dir"
          7z x "$file" -o"$output_dir" || echo "Error extracting $file"
          ;;
      *)
        echo "Unknown archive type: $file"
        ;;
    esac
  done
}

unzip_recursive "$source_dir" "$dest_dir"

echo "Finished."

exit 0