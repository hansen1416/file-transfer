#!/bin/bash

# Check if a directory is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Set the target directory. Defaults to the current directory if not provided.
target_dir="${1:-.}"

# Function to recursively unzip files
unzip_recursive() {
  local dir="$1"

  # Find all .zip, .rar, .tar.gz, .tar.bz2, .tar, .7z files in the current directory
  find "$dir" -type f \( -name "*.zip" -o -name "*.rar" -o -name "*.tar.gz" -o -name "*.tgz" -o -name "*.tar.bz2" -o -name "*.tbz2" -o -name "*.tar" -o -name "*.7z" \) -print0 | while IFS= read -r -d $'\0' file; do
    # Extract the filename without the extension
    filename=$(basename "$file")
    extension="${filename##*.}"
    filename="${filename%.*}"

    # Create a directory with the same name as the zip file (if it doesn't exist)
    output_dir="$dir/$filename"
    mkdir -p "$output_dir"

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

# Check if the target directory exists
if [ ! -d "$target_dir" ]; then
  echo "Error: Directory '$target_dir' not found."
  exit 1
fi

# Call the recursive function
unzip_recursive "$target_dir"

echo "Finished."

exit 0