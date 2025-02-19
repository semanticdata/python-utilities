# This script is used to create a zip archive of the vault location and save it to the backup location.
# The zip file will be named with the current timestamp.
# The script will also print the size of the zip file in a human readable format.

import os
import zipfile
from datetime import datetime
import shutil
import sys
import fnmatch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get configuration from environment variables
VAULT_LOCATION = os.getenv('VAULT_LOCATION')
BACKUP_LOCATION = os.getenv('BACKUP_LOCATION')
IGNORE_PATTERNS = os.getenv('IGNORE_PATTERNS', '').split(',')

# Validate required environment variables
if not VAULT_LOCATION or not BACKUP_LOCATION:
    print("Error: VAULT_LOCATION and BACKUP_LOCATION must be set in .env file", file=sys.stderr)
    sys.exit(1)

def should_ignore(path, patterns=IGNORE_PATTERNS):
    """
    Check if the path matches any of the ignore patterns.

    Args:
        path (str): The path to check
        patterns (list): List of patterns to ignore

    Returns:
        bool: True if the path should be ignored, False otherwise
    """
    # Convert Windows path separators to forward slashes for consistent pattern matching
    path = path.replace(os.sep, "/")
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def create_backup():
    """
    Creates a zip archive of the vault location and saves it to the backup location.
    The zip file will be named with the current timestamp.
    """
    try:
        # Ensure both directories exist
        if not os.path.exists(VAULT_LOCATION):
            raise FileNotFoundError(f"Vault location does not exist: {VAULT_LOCATION}")

        if not os.path.exists(BACKUP_LOCATION):
            os.makedirs(BACKUP_LOCATION)
            print(f"Created backup directory: {BACKUP_LOCATION}")

        # Create timestamp for unique backup name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_{timestamp}.zip"
        zip_path = os.path.join(BACKUP_LOCATION, zip_filename)

        # Create zip file
        print(f"Creating backup archive: {zip_filename}")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the directory
            for root, dirs, files in os.walk(VAULT_LOCATION):
                # Remove ignored directories from dirs list to prevent walking into them
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(
                        os.path.relpath(os.path.join(root, d), VAULT_LOCATION)
                    )
                ]

                for file in files:
                    # Get the full path of the file
                    file_path = os.path.join(root, file)
                    # Calculate path relative to VAULT_LOCATION for the archive
                    arcname = os.path.relpath(file_path, VAULT_LOCATION)

                    # Skip if file matches ignore patterns
                    if should_ignore(arcname):
                        print(f"Ignoring: {arcname}")
                        continue

                    print(f"Adding: {arcname}")
                    zipf.write(file_path, arcname)

        print(f"\nBackup completed successfully!")
        print(f"Archive saved to: {zip_path}")
        print(f"Total size: {format_size(os.path.getsize(zip_path))}")

    except Exception as e:
        print(f"Error creating backup: {str(e)}", file=sys.stderr)
        sys.exit(1)


def format_size(size):
    """Convert size in bytes to human readable format"""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0


if __name__ == "__main__":
    create_backup()
