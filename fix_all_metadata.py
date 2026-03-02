#!/usr/bin/env python
"""Fix ALL corrupted .txt files in Python site-packages dist-info directories."""

import os
from pathlib import Path

# Define site-packages path
site_packages = Path(r"C:\Users\ND\AppData\Local\Programs\Python\Python312\Lib\site-packages")

fixed_count = 0
checked_count = 0
skipped_count = 0

# Find ALL .txt files in dist-info directories
for txt_file in site_packages.rglob("*.txt"):
    # Only process files in dist-info directories
    if 'dist-info' not in str(txt_file):
        skipped_count += 1
        continue

    checked_count += 1
    try:
        # Read as binary
        content = txt_file.read_bytes()
        has_bad_bytes = False

        # Check for any invalid UTF-8 bytes in first 100 bytes
        # A valid UTF-8 sequence starts with 0x00-0x7F (ASCII) or 0xC0-0xDF (2-byte), 0xE0-0xEF (3-byte), 0xF0-0xF7 (4-byte)
        # Bytes 0x80-0xBF are only valid as continuation bytes
        for i, byte in enumerate(content[:100]):
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

            txt_file.write_bytes(new_content)
            print(f"Fixed: {txt_file.name} in {txt_file.parent.name}")
            fixed_count += 1
    except Exception as e:
        print(f"Error checking {txt_file}: {e}")

print(f"\nSummary:")
print(f"  Checked: {checked_count} dist-info .txt files")
print(f"  Fixed: {fixed_count} files")
print(f"  Skipped (non-dist-info): {skipped_count} files")
