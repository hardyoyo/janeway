#!/bin/bash

# Enable unofficial Bash strict mode
set -euo pipefail

# Define the path to the debian.sources file
debian_sources="/etc/apt/sources.list.d/debian.sources"

# Check if debian.sources file exists
if [ -f "$debian_sources" ]; then
  # Check if debian.sources already contains deb-src lines
  if grep -q 'Types: deb-src' "$debian_sources"; then
    echo "INFO: debian.sources already contains deb-src lines. No changes needed."
  else
    echo "INFO: adding deb-src lines to debian.sources..."

    # Create a temporary copy of debian.sources
    cp "$debian_sources" "${debian_sources}.copy"

    # Modify the lines in the copy using sed
    sed -i -e 's/Types: deb/Types: deb-src/' "${debian_sources}.copy"

    # Append the content of the modified copy back to the original file, merging the changes
    echo | cat "${debian_sources}.copy" >> "$debian_sources"

    # Remove the temporary copy of the file since it's no longer needed
    rm "${debian_sources}.copy"
  fi
else
  echo "INFO: debian.sources file not found. Skipping."
fi

# indicate success (0)
exit 0
