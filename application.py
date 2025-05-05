
import csv
from datetime import datetime
import os
import logging
import gzip
import shutil
import subprocess
import sys
import tarfile

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


LOCATION_SPECIFIER_FILENAME = "locations.txt"
SUMMARY_FILENAME = "summary.txt"
LOG_FILENAME = datetime.now().strftime("%Y%m%d") + ".log"

logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
log_handler = logging.FileHandler(f'logs/{LOG_FILENAME}')
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)


def get_size_gb(path: str) -> str:
    return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')
        

class Credentials:
    """Stores credentials derived from environment variables."""

    def __init__(self) -> None:
        pass
    

class BackupGenerator:
    """The core functionality of creating backups is handled here."""

    def __init__(self, credentials: dict, is_encrypted: bool = False) -> None:
        self.credentials = credentials
        self.is_encrypted = is_encrypted
        self.file_validity_check()
        self.location_data = self.location_data

    def file_validity_check(self) -> None:
        """Checks if the file exists and is valid."""
        if not os.path.exists(LOCATION_SPECIFIER_FILENAME):
            print("ERROR: Path specified for 'location.txt' does not exist.")
            sys.exit()
        if not os.path.exists(SUMMARY_FILENAME):
            print("ERROR: Path specified does not exist.")
            sys.exit()

    def get_location_data(self) -> list:
        """Returns the contents of the entire file (the locations of taking backups)."""
        with open(LOCATION_SPECIFIER_FILENAME, "r") as file:
            data = [line.strip() for line in file]
        return data

    def create_gzip_files(self) -> None:
        """Applies GZIP compression on TAR balls (or regular files)."""
        for location in self.location_data:
            try:
                if os.path.isfile(location):
                    with open(location, 'rb') as input_file, gzip.open(location + '.gz', 'wb') as output_file:
                        shutil.copyfileobj(input_file, output_file)
                else:
                    with tarfile.open(location + ".tgz", "w:gz") as tar:
                        tar.add(name)
            except Exception:
                print("ERROR: GZIP operation failed on file:", location)
            
    def remove_gzip_files(self) -> None:
        """Removes all generated GZIPs post cloud backup."""
        for location in self.location_data:
            try:
                os.remove(location + '.gz' if os.path.isfile(location) else location + '.tgz')
            except Exception:
                print("ERROR: Deletion failed for tarball of file:", location)
    
    def encrypt(self) -> None:
        """Perform encryption on the collected data."""
        password = self.credentials["password"].encode('utf-8')
        for location in self.location_data:
            try:
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000, backend=default_backend())
                key = Fernet(kdf.derive(password))

                with open(location, 'rb') as infile, open(location + '.enc', 'wb') as outfile:
                    outfile.write(salt)
                    while True:
                        chunk = infile.read(4096)
                        if not chunk:
                            break
                        encrypted_chunk = key.encrypt(chunk)
                        outfile.write(encrypted_chunk)
            except Exception:
                print("ERROR: Encryption issues on file:", location)

    def backup(self) -> None:
        """Backs up to Cloudinary."""

    def generate_summary(self) -> None:
        """Populates the summary file by altering or appending entries."""
        summary_data = {}
        with open(summary_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            if header == ['location', 'size', 'timestamp']:
                for row in reader:
                    location, size_gb_str, timestamp_str = row
                    try:
                        size_gb = float(size_gb_str)
                        timestamp = datetime.fromisoformat(timestamp_str)
                        summary_data[location] = {'size': size_gb, 'timestamp': timestamp}
                    except ValueError:
                        print(f"Warning: Skipping invalid entry in summary.csv: {row}")
            else:
                print("Warning: summary.csv header is missing or incorrect. Starting with an empty tracker.")
                sys.exit()
        updated_summary_data = summary_data.copy()
        for location in location_data:
            try:
                if location in updated_summary_data:
                    updated_summary_data[location]['size'] = get_size_gb(location)
                    updated_summary_data[location]['timestamp'] = datetime.now()
                    print(f"Updated backup status for: {location} (Size: {size} GB, Timestamp: {timestamp.isoformat()})")
                else:
                    updated_summary_data[location] = {'size_gb': size_gb, 'timestamp': timestamp}
                    print(f"Added backup status for: {location} (Size: {size} GB, Timestamp: {timestamp.isoformat()})")
            except FileNotFoundError:
                print(f"Warning: Location not found: {location}. Cannot update backup status.")
            except Exception as e:
                print(f"Error processing location {location}: {e}")
        try:
            with open(summary_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['location', 'size_gb', 'timestamp'])
                for location, data in updated_summary_data.items():
                    writer.writerow([location, data['size_gb'], data['timestamp'].isoformat()])
        except Exception as e:
            print(f"Error saving summary.csv: {e}")

    def start(self) -> None:
        """To kick-off the entire process."""
        self.create_gzip_files()
        if self.is_encrypted:
            self.encrypt()
        self.backup()
        self.generate_summary()
        self.remove_gzip_files()
        logger.info("Backup Complete!")
        print("SUCCESS: Backup Complete!")
        

class BackupRetriever:
    pass
