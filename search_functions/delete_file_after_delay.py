import os
import time

# File expiration time in seconds (300 minutes)
FILE_EXPIRATION_TIME = 300 * 60 # Adjust file expiration time as you wish.

def delete_file_after_delay(file_path):
    """Deletes the file after a specified delay."""
    time.sleep(FILE_EXPIRATION_TIME)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted file: {file_path}")
        except OSError as e:
            print(f"Error deleting file {file_path}: {e}")