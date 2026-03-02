#!/usr/bin/env python
"""Fix ALL corrupted files in site-packages - remove null bytes and extended bytes."""

import os
from pathlib import Path

# Define site-packages path
site_packages = Path(r"C:\Users\ND\AppData\Local\Programs\Python\Python312\Lib\site-packages")

fixed_count = 0
checked_count = 0
skipped_count = 0
error_count = 0

# File extensions to check (Python source and metadata)
check_extensions = {'.py', '.txt', '.md', '.rst', '.cfg', '.ini', '.toml', '.json', '.yaml', '.yml'}

print("Scanning site-packages for corrupted files...")
print("=" * 60)

for item in site_packages.rglob("*"):
    # Skip directories
    if not item.is_file():
        skipped_count += 1
        continue

    # Only check relevant file types
    if item.suffix.lower() not in check_extensions:
        skipped_count += 1
        continue

    checked_count += 1
    try:
        content = item.read_bytes()

        # Check for null bytes or extended bytes
        null_count = content.count(b'\x00')
        extended_count = sum(1 for b in content if b >= 0x80)

        # Fix if corrupted
        if null_count > 0 or extended_count > 0:
            # Remove null bytes and extended bytes
            new_content = bytearray()
            for byte in content:
                if byte != 0 and byte < 0x80:
                    new_content.append(byte)

            if len(new_content) > 0:
                item.write_bytes(bytes(new_content))
                rel_path = item.relative_to(site_packages)
                print(f"Fixed: {rel_path} (nulls: {null_count}, extended: {extended_count})")
                fixed_count += 1
            else:
                # File would be empty - skip
                print(f"WARNING: Would make file empty, skipping: {item.name}")
    except Exception as e:
        error_count += 1
        if error_count <= 10:  # Only show first 10 errors
            print(f"Error checking {item.name}: {e}")

print("\n" + "=" * 60)
print(f"Summary:")
print(f"  Checked: {checked_count} files")
print(f"  Fixed: {fixed_count} files")
print(f"  Skipped: {skipped_count} items")
print(f"  Errors: {error_count} files")
print("=" * 60)
