#!/usr/bin/env python
"""Fix ALL corrupted files with extended bytes in headers."""

import os
from pathlib import Path

# Define site-packages path
site_packages = Path(r"C:\Users\ND\AppData\Local\Programs\Python\Python312\Lib\site-packages")

fixed_count = 0
checked_count = 0
skipped_count = 0

# Find ALL files in dist-info directories
for item in site_packages.rglob("*"):
    # Only process files in dist-info directories
    if 'dist-info' not in str(item):
        skipped_count += 1
        continue

    if not item.is_file():
        skipped_count += 1
        continue

    checked_count += 1
    try:
        content = item.read_bytes()

        # Check for extended bytes (>= 0x80) in first 100 bytes (header area)
        # These are metadata files and shouldn't have extended bytes in the header
        has_extended_in_header = False
        for i in range(min(100, len(content))):
            if content[i] >= 0x80:
                has_extended_in_header = True
                break

        if has_extended_in_header:
            # Fix by replacing extended bytes in header with ASCII equivalent or removing
            # For metadata files, the corruption seems to be TSD-related
            # Let's try to fix by removing all extended bytes from the entire file
            new_content = bytearray()
            for byte in content:
                if byte < 0x80:
                    new_content.append(byte)

            item.write_bytes(new_content)
            print(f"Fixed: {item.name} in {item.parent.name}")
            fixed_count += 1
    except Exception as e:
        pass  # Skip files that can't be read

print(f"\nSummary:")
print(f"  Checked: {checked_count} dist-info files")
print(f"  Fixed: {fixed_count} files")
print(f"  Skipped: {skipped_count} files")
