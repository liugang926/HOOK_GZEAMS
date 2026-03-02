#!/usr/bin/env python
"""Fix all corrupted entry_points.txt files in Python site-packages."""

import os
from pathlib import Path

# Define site-packages path
site_packages = Path(r"C:\Users\ND\AppData\Local\Programs\Python\Python312\Lib\site-packages")

# All non-UTF-8 bytes that might appear in corrupted files (0x80-0xFF range)
# We'll remove any byte >= 0x80 that's not a valid UTF-8 continuation
bad_bytes_found = set()

fixed_count = 0
checked_count = 0

# Find all entry_points.txt files
for entry_point_file in site_packages.rglob("entry_points.txt"):
    checked_count += 1
    try:
        # Try to read as UTF-8
        content = entry_point_file.read_bytes()
        has_bad_bytes = False

        # Check for any problematic bytes (non-ASCII in header)
        # TSD header corruption typically has bytes > 0x7F in unexpected places
        for i, byte in enumerate(content[:100]):  # Check first 100 bytes (header area)
            if byte >= 0x80:
                # Check if this is a valid UTF-8 sequence start
                # UTF-8: 0xC0-0xDF = 2-byte, 0xE0-0xEF = 3-byte, 0xF0-0xF7 = 4-byte
                # If it's in 0x80-0xBF range without a lead byte, it's invalid
                if byte < 0xC0:
                    has_bad_bytes = True
                    bad_bytes_found.add(byte)
                    break

        if has_bad_bytes:
            # Remove problematic bytes by zeroing them or replacing with valid bytes
            # For TSD headers, we need to preserve structure
            # Let's try a different approach - remove the bad bytes entirely from content
            new_content = bytearray()
            i = 0
            while i < len(content):
                byte = content[i]
                if byte < 0x80:
                    new_content.append(byte)
                    i += 1
                elif 0xC0 <= byte <= 0xDF:
                    # Valid 2-byte sequence
                    if i + 1 < len(content):
                        new_content.extend(content[i:i+2])
                        i += 2
                    else:
                        i += 1
                elif 0xE0 <= byte <= 0xEF:
                    # Valid 3-byte sequence
                    if i + 2 < len(content):
                        new_content.extend(content[i:i+3])
                        i += 3
                    else:
                        i += 1
                elif 0xF0 <= byte <= 0xF7:
                    # Valid 4-byte sequence
                    if i + 3 < len(content):
                        new_content.extend(content[i:i+4])
                        i += 4
                    else:
                        i += 1
                else:
                    # Invalid UTF-8 continuation byte without lead - skip it
                    bad_bytes_found.add(byte)
                    i += 1

            entry_point_file.write_bytes(new_content)
            print(f"Fixed: {entry_point_file}")
            fixed_count += 1
    except Exception as e:
        print(f"Error checking {entry_point_file}: {e}")

print(f"\nChecked {checked_count} files")
print(f"Fixed {fixed_count} files")
print(f"Bad bytes found: {sorted(bad_bytes_found)}")
