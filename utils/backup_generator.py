import base64
import csv
from datetime import datetime
import os
import gzip
import shutil
import sys
import tarfile

import cloudinary
import cloudinary.uploader
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from utils.misc import get_size_gb, logger, Credentials


LOCATION_SPECIFIER_FILENAME = "reports/locations.txt"
SUMMARY_FILENAME = "reports/summary.csv"


class BackupGenerator:
    """To create backups."""

    def __init__(self, is_encrypted: bool = False) -> None:
        self.file_validity_check()
        self.summary = []
        self.credentials = Credentials()
        self.is_encrypted = is_encrypted
        self.location_data = self.get_location_data()
        logger.info("Initiating Bat Backup v1.0.0.\nBackup mode selected.")
        logger.info("Starting the 5-step process now." if is_encrypted else "Starting the 4-step process now.")

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

    def get_location_data(self) -> list[str]:
        """Returns the contents of the entire file (the locations of taking backups)."""
        with open(LOCATION_SPECIFIER_FILENAME, "r") as file:
            data = [line.strip() for line in file]
        return data

    def create_gzip_files(self) -> None:
        """Applies GZIP compression on TAR balls (or regular files)."""
        for location in self.location_data:
            path = os.path.abspath(location)
            try:
                if os.path.isfile(path):
                    with open(path, 'rb') as input_file, gzip.open(path + '.gz', 'wb') as output_file:
                        shutil.copyfileobj(input_file, output_file)
                else:
                    with tarfile.open(location + ".tgz", "w:gz") as tar:
                        tar.add(location)
            except Exception:
                print("ERROR: GZIP operation failed on file:", location)
                logger.error(f"GZIP operation failed on location: {location}.")
                sys.exit()
        logger.info("Step 1 (Compression): Complete!")
        print("Step 1 (Compression): Complete!")
        

    def remove_gzip_files(self) -> None:
        """Removes all generated GZIPs post cloud backup."""
        for location in self.location_data:
            try:
                os.remove(location + '.gz' if os.path.isfile(location) else location + '.tgz')
            except Exception:
                print("ERROR: Deletion failed for tarball of file:", location)
                logger.error(f"Archive deletion failed on location: {location}.")
                sys.exit()
        logger.info("Step 4 (Archive Removal): Complete!" if self.is_encrypted else "Step 3 (Archive Removal): Complete!")
        print("Step 4 (Archive Removal): Complete!" if self.is_encrypted else "Step 3 (Archive Removal): Complete!")
    
    def encrypt(self) -> None:
        """Perform encryption on the collected data."""
        password = self.credentials.password.encode('utf-8')
        for location in self.location_data:
            try:
                salt = os.urandom(16)
                kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000, backend=default_backend())
                key = Fernet(base64.urlsafe_b64encode(kdf.derive(password)))
                location = location + '.gz' if os.path.isfile(location) else location + '.tgz'
                with open(location, 'rb') as infile, open(location + '.enc', 'wb') as outfile:
                    outfile.write(salt)
                    while True:
                        chunk = infile.read(4096)
                        if not chunk:
                            break
                        encrypted_chunk = key.encrypt(chunk)
                        outfile.write(encrypted_chunk)
            except Exception as e:
                print("ERROR: Encryption issues on file:", location)
                logger.error(f"Encryption failed on location: {location}.")
                self.remove_gzip_files()
                print(e)
                sys.exit()
        logger.info("Step 2 (Encryption): Complete!")
        print("Step 2 (Encryption): Complete!")

    def backup(self) -> None:
        """Backs up to Cloudinary."""
        cloudinary.config(cloud_name=self.credentials.cloud_name, api_key=self.credentials.api_key, api_secret=self.credentials.api_secret)
        try:
            for location in self.location_data:
                original_size = get_size_gb(location)
                if self.is_encrypted:
                    backup_filename = location + ".gz.enc" if os.path.isfile(location) else location + '.tgz.enc'
                    backup_size = get_size_gb(backup_filename)
                    cloudinary.uploader.upload_large(backup_filename, public_id=backup_filename.split('/')[-1], overwrite=True, type="private")
                else:
                    backup_filename = location + ".gz" if os.path.isfile(location) else location + '.tgz'
                    backup_size = get_size_gb(backup_filename)
                    cloudinary.uploader.upload_large(backup_filename, public_id=backup_filename.split('/')[-1], overwrite=True, type="private")
                self.summary.append({"location": location, "size": backup_size, "timestamp": datetime.now()})
                logger.info(f"Backed up '{location}' to Cloud. Original size: {original_size}. Backed-up size: {backup_size}.")
        except Exception as e:
            print("ERROR: Backup failed.", e)
            self.remove_gzip_files()
            sys.exit()
        logger.info("Step 3 (Backup): Complete!" if self.is_encrypted else "Step 2 (Backup): Complete!")
        print("Step 3 (Backup): Complete!" if self.is_encrypted else "Step 2 (Backup): Complete!")
        
    def generate_summary(self) -> None:
        """Populates the summary file by altering or appending entries."""
        updated_summary = []
        try:
            with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    if row["location"] not in self.location_data:
                        updated_summary.append(row)
            with open(SUMMARY_FILENAME, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["location", "size", "timestamp"])
                writer.writeheader()
                writer.writerows(updated_summary)
            with open(SUMMARY_FILENAME, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["location", "size", "timestamp"])
                writer.writerows(self.summary)
        except Exception as e:
            print(f"Error saving summary.csv: {e}")
            sys.exit()
        logger.info("Step 5 (Summary Generation): Complete!" if self.is_encrypted else "Step 4 (Summary Generation): Complete!")
        print("Step 5 (Summary Generation): Complete!" if self.is_encrypted else "Step 4 (Summary Generation): Complete!")
        
    def back_up(self) -> None:
        """To kick-off the entire process."""
        self.create_gzip_files()
        if self.is_encrypted:
            self.encrypt()
        self.backup()
        self.remove_gzip_files()
        self.generate_summary()
        logger.info("Backup successfully complete!")
        print("SUCCESS: Backup Complete!")
