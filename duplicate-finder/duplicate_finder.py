# This script is used to find duplicate files in a directory.
# It uses the MD5 hash of the file to determine if it is a duplicate.
# It then prints the duplicate files and the total size of the duplicate files.
# It also prints the potential space savings if the duplicate files are removed.
# pip install humanize

import os
import hashlib
from collections import defaultdict
from pathlib import Path
import argparse
import sys
from typing import Dict, List, Set
import humanize


def calculate_file_hash(filepath: str, block_size: int = 65536) -> str:
    """Calculate MD5 hash of a file."""
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def find_duplicates(directory: str) -> Dict[str, List[str]]:
    """Find duplicate files in the given directory."""
    hash_map: Dict[str, List[str]] = defaultdict(list)
    total_size = 0
    duplicate_size = 0

    # Walk through the directory
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                file_hash = calculate_file_hash(filepath)
                file_size = os.path.getsize(filepath)
                total_size += file_size
                hash_map[file_hash].append(filepath)
            except (IOError, OSError) as e:
                print(f"Error processing {filepath}: {e}", file=sys.stderr)

    # Filter out unique files and calculate duplicate size
    duplicate_files = {h: files for h, files in hash_map.items() if len(files) > 1}
    for _, files in duplicate_files.items():
        if files:
            duplicate_size += os.path.getsize(files[0]) * (len(files) - 1)

    return duplicate_files, total_size, duplicate_size


def main() -> None:
    parser = argparse.ArgumentParser(description="Find duplicate files in a directory")
    parser.add_argument("directory", help="Directory to scan for duplicates")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)

    print(f"\nScanning directory: {args.directory}")
    print("This might take a while depending on the number and size of files...\n")

    duplicates, total_size, duplicate_size = find_duplicates(args.directory)

    if not duplicates:
        print("No duplicate files found.")
        return

    # Print results with improved formatting
    print(
        f"Found {sum(len(files) for files in duplicates.values()) - len(duplicates)} duplicate files"
    )
    print(f"Total space used: {humanize.naturalsize(total_size)}")
    print(f"Space taken by duplicates: {humanize.naturalsize(duplicate_size)}")
    print(f"Potential space savings: {humanize.naturalsize(duplicate_size)}\n")

    print("Duplicate files:")
    for hash_value, file_list in duplicates.items():
        print(
            f"\nDuplicate set (size: {humanize.naturalsize(os.path.getsize(file_list[0]))})"
        )
        for filepath in file_list:
            print(f"  {filepath}")


if __name__ == "__main__":
    main()
