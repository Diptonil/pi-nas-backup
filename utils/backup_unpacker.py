from abc import ABC, abstractmethod
import csv
import sys
import os
import shutil
import tarfile
import gzip

import cloudinary
import requests

from utils.misc import logger, generate_key_from_password, Credentials


SUMMARY_FILENAME = "reports/summary.csv"


class BackupRetriever(ABC):
    """To unpack the backups."""

    def __init__(self) -> None:
        self.summary = []
        self.credentials = Credentials()
        logger.info("Initiating Bat Backup v1.0.0.")
        logger.info("Retrieval mode selected.")
        logger.info("Starting the 3-step process now.")

    @abstractmethod
    def download(self) -> None:
        """Extraction logic that would vary based on the providers used."""
        
    def decrypt(self) -> None:
        """Decrypts files that are encrypted. Also removes all .enc binaries."""
        password = self.credentials.password.encode('utf-8')
        try:
            with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    filename = 'backups/' + row['public_id']
                    if filename[-4:] != '.enc':
                        continue
                    with open(filename, 'rb') as file:
                        content = file.read()
                    salt = content[:16]
                    encrypted = content[16:]
                    fernet = generate_key_from_password(password, salt)
                    decrypted_data = fernet.decrypt(encrypted)
                    with open(filename[:-4], 'wb') as file:
                        file.write(decrypted_data)
                    os.remove(filename)
        except Exception as e:
            print(f"Error processing: {e}")
            sys.exit()
        logger.info("Step 2 (Decryption): Complete!")
        print("Step 2 (Decryption): Complete!")
        
    def decompress(self) -> None:
        """Unzips the files and folders."""
        try:
            with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    original_filename = 'backups/' + (row['public_id'][:-4] if row['public_id'][-4:] == ".enc" else row['public_id'])
                    folder = os.path.dirname(original_filename)
                    filename = os.path.basename(original_filename)
                    logger.info(f"Unzipping file at {filename}.")
                    if filename.endswith('.tgz'):
                        with tarfile.open(original_filename, 'r:gz') as tar:
                            tar.extractall(path=folder)
                    elif filename.endswith('.gz'):
                        output_path = os.path.join(folder, filename[:-3])
                        with gzip.open(original_filename, 'rb') as f_in, open(output_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    os.remove(original_filename)
        except Exception as e:
            print(f"Error processing: {e}")
            sys.exit()
        logger.info("Step 3 (Decompression): Complete!")
        print("Step 3 (Decompression): Complete!")

    def retrieve(self) -> None:
        """To kick-off the entire process."""
        self.download()
        self.decrypt()
        self.decompress()


class CloudinaryBackupRetriever(BackupRetriever):
    """To extract Cloudinary backups."""

    def __init__(self):
        super().__init__()

    def download(self):
        """Fetches files from Cloudinary."""
        cloudinary.config(cloud_name=self.credentials.cloud_name, api_key=self.credentials.api_key, api_secret=self.credentials.api_secret)
        try:
            with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    filename = row['public_id']
                    url = cloudinary.utils.cloudinary_url(filename, resource_type = "raw")[0]
                    logger.info(f"Downloading file from URL: {url}.")
                    with requests.get(url, stream=True) as r, open(f"backups/{filename}", 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192): 
                            f.write(chunk)
        except Exception as e:
            print(f"Error reading summary.csv: {e}")
            sys.exit()
        logger.info("Step 1 (Download): Complete!")
        print("Step 1 (Download): Complete!")
