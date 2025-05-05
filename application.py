
import csv
from datetime import datetime
import os
import logging
import gzip
import shutil
import subprocess
import sys
import tarfile

import cloudinary.uploader
import cloudinary
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


LOCATION_SPECIFIER_FILENAME = "locations.txt"
SUMMARY_FILENAME = "summary.csv"
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
        

def load_env(dotenv_path=".env"):
    """Loads environment variables from a .env file. No external dependencies."""
    with open(dotenv_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value


class Credentials:
    """Stores credentials derived from environment variables."""

    def __init__(self) -> None:
        try:
            load_env()
            self.cloud_name = os.getenv("CLOUD_NAME")
            self.api_key = os.getenv("API_KEY")
            self.api_secret = os.getenv("API_SECRET")
            self.validate_existence()
        except Exception:
            print("ERROR: Failed to access environment variables.")
            logger.error("Failed to access environment variables.")
            sys.exit()
    
    def validate_existence(self) -> None:
        if not self.cloud_name or not self.api_key or not self.api_secret:
            raise Exception


class BackupGenerator:
    """To create backups."""

    def __init__(self, credentials: dict, is_encrypted: bool = False) -> None:
        self.credentials = credentials
        self.is_encrypted = is_encrypted
        self.file_validity_check()
        self.location_data = self.location_data
        logger.info("Starting the 4-step process now." if is_encrypted else "Starting the 3-step process now.")

    def file_validity_check(self) -> None:
        """Checks if the file exists and is valid."""
        if not os.path.exists(LOCATION_SPECIFIER_FILENAME):
            print("ERROR: Path specified for 'location.txt' does not exist.")
            logger.error("Location file improperly configured.")
            sys.exit()
        if not os.path.exists(SUMMARY_FILENAME):
            print("ERROR: Path specified for 'summary.csv' does not exist.")
            logger.error("Summary file improperly configured.")
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
                        tar.add(location)
            except Exception:
                print("ERROR: GZIP operation failed on file:", location)
                logger.error(f"GZIP operation failed on location: {location}.")
                sys.exit()
        logger.info("Step 1 (Compression): Complete!")
        

    def remove_gzip_files(self) -> None:
        """Removes all generated GZIPs post cloud backup."""
        for location in self.location_data:
            try:
                os.remove(location + '.gz' if os.path.isfile(location) else location + '.tgz')
            except Exception:
                print("ERROR: Deletion failed for tarball of file:", location)
                logger.error(f"Archive deletion failed on location: {location}.")
                sys.exit()
        logger.info("Step 4 (Backup): Complete!" if self.is_encrypted else "Step 3 (Backup): Complete!")
        
    
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
                logger.error(f"Encryption failed on location: {location}.")
                sys.exit()
        logger.info("Step 2 (Encryption): Complete!")

    def backup(self) -> None:
        """Backs up to Cloudinary."""
        credentials = Credentials()
        cloudinary.config(cloud_name=credentials.cloud_name, api_key=credentials.api_key, api_secret=credentials.api_secret)
        try:
            for location in self.location_data:
                original_size = get_size_gb(location)
                if self.is_encrypted:
                    backup_filename = location + ".gz.enc" if os.path.isfile(location) else location + '.tgz.enc'
                    backup_size = get_size_gb(backup_filename)
                    cloudinary.uploader.upload_large(backup_filename)
                else:
                    backup_filename = location + ".gz" if os.path.isfile(location) else location + '.tgz'
                    backup_size = get_size_gb(backup_filename)
                    cloudinary.uploader.upload_large(backup_filename)
                logger.info(f"Backed up '{location}' to Cloud. Original size: {original_size} GB. Backed-up size: {backup_size} GB.")
        except Exception:
            print("ERROR: Backup failed.")
            sys.exit()
        logger.info("Step 3 (Backup): Complete!" if self.is_encrypted else "Step 2 (Backup): Complete!")
        
    def generate_summary(self) -> None:
        """Populates the summary file by altering or appending entries."""
        summary_data = {}
        with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
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
                        sys.exit()
            else:
                print("Warning: summary.csv header is missing or incorrect. Starting with an empty tracker.")
                sys.exit()
        updated_summary_data = summary_data.copy()
        for location in self.location_data:
            try:
                if location in updated_summary_data:
                    updated_summary_data[location]['size'] = get_size_gb(location)
                    updated_summary_data[location]['timestamp'] = datetime.now()
                    print(f"Updated backup status for: {location} (Size: {size_gb} GB, Timestamp: {timestamp.isoformat()})")
                else:
                    updated_summary_data[location] = {'_gb_gb': size_gb, 'timestamp': timestamp}
                    print(f"Added backup status for: {location} (Size: {size_gb} GB, Timestamp: {timestamp.isoformat()})")
            except FileNotFoundError:
                print(f"Warning: Location not found: {location}. Cannot update backup status.")
                sys.exit()
            except Exception as e:
                print(f"Error processing location {location}: {e}")
                sys.exit()
        try:
            with open(SUMMARY_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['location', 'size_gb', 'timestamp'])
                for location, data in updated_summary_data.items():
                    writer.writerow([location, data['size_gb'], data['timestamp'].isoformat()])
        except Exception as e:
            print(f"Error saving summary.csv: {e}")
            sys.exit()
        logger.info("Step 5 (Backup): Complete!" if self.is_encrypted else "Step 4 (Backup): Complete!")
        
    def start(self) -> None:
        """To kick-off the entire process."""
        self.create_gzip_files()
        if self.is_encrypted:
            self.encrypt()
        self.backup()
        self.generate_summary()
        self.remove_gzip_files()
        logger.info("Backup successfully complete!")
        print("SUCCESS: Backup Complete!")
        

class BackupRetriever:
    """To unpack the backups."""
