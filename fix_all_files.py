#!/usr/bin/env python
"""Fix ALL corrupted files in Python site-packages dist-info directories."""

import os
from pathlib import Path

# Define site-packages path
site_packages = Path(r"C:\Users\ND\AppData\Local\Programs\Python\Python312\Lib\site-packages")

fixed_count = 0
checked_count = 0
skipped_count = 0
error_count = 0

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
        # Read as binary
        content = item.read_bytes()
        has_bad_bytes = False

        # Check for any invalid UTF-8 bytes in entire file
        # A valid UTF-8 sequence starts with 0x00-0x7F (ASCII) or 0xC0-0xDF (2-byte), 0xE0-0xEF (3-byte), 0xF0-0xF7 (4-byte)
        # Bytes 0x80-0xBF are only valid as continuation bytes
        for i, byte in enumerate(content):
            if 0x80 <= byte < 0xC0:
                # This is a continuation byte without a lead byte - invalid UTF-8
                has_bad_bytes = True
                break

        if has_bad_bytes:
            # Fix by removing bad bytes
            new_content = bytearray()
            i = 0
            while i < len(content):
                byte = content[i]
                if byte < 0x80:
                    # ASCII - keep as is
                    new_content.append(byte)
                    i += 1
                elif 0xC0 <= byte <= 0xDF:
                    # 2-byte UTF-8 sequence
                    if i + 1 < len(content):
                        new_content.extend(content[i:i+2])
                        i += 2
                    else:
                        i += 1
                elif 0xE0 <= byte <= 0xEF:
                    # 3-byte UTF-8 sequence
                    if i + 2 < len(content):
                        new_content.extend(content[i:i+3])
                        i += 3
                    else:
                        i += 1
                elif 0xF0 <= byte <= 0xF7:
                    # 4-byte UTF-8 sequence
                    if i + 3 < len(content):
                        new_content.extend(content[i:i+4])
                        i += 4
                    else:
                        i += 1
                else:
                    # Invalid continuation byte - skip it
                    i += 1

            item.write_bytes(new_content)
            print(f"Fixed: {item.name} in {item.parent.name}")
            fixed_count += 1
    except Exception as e:
        error_count += 1
        # Don't print errors for files that can't be read

print(f"\nSummary:")
print(f"  Checked: {checked_count} dist-info files")
print(f"  Fixed: {fixed_count} files")
print(f"  Errors: {error_count} files")
print(f"  Skipped (non-dist-info): {skipped_count} files")
