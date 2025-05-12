from abc import ABC, abstractmethod
from base64 import urlsafe_b64encode
import csv
import sys
import os
import shutil
import struct
import tarfile
import gzip

import cloudinary
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from utils.misc import logger, Credentials


SUMMARY_FILENAME = "reports/summary.csv"


class BackupRetriever(ABC):
    """To unpack the backups."""

    def __init__(self) -> None:
        self.summary = []
        self.credentials = Credentials()
        logger.info("Initiating Bat Backup v1.0.0.")
        logger.info("Retrieval mode selected.")
        logger.info("Starting the 4-step process now.")

    @abstractmethod
    def download(self) -> None:
        """Extraction logic that would vary based on the providers used."""

    def derive_fernet(self, password: bytes, salt: bytes) -> Fernet:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000, backend=default_backend())
        key = urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)
    
    def decrypt_file(self, enc_path: str, password: bytes, out_path: str):
        with open(enc_path, 'rb') as f:
            salt = f.read(16)
            fernet = self.derive_fernet(password, salt)
            with open(out_path, 'wb') as out:
                while True:
                    len_bytes = f.read(4)
                    if not len_bytes:
                        break
                    (token_len,) = struct.unpack('>I', len_bytes)
                    token = f.read(token_len)
                    pt = fernet.decrypt(token)
                    out.write(pt)
        
    def decrypt(self) -> None:
        """Decrypts files that are encrypted. Also removes all .enc binaries."""
        password = self.credentials.password.encode('utf-8')
        try:
            with open(SUMMARY_FILENAME, 'r', newline='', encoding='utf-8') as csvfile:
                for row in csv.DictReader(csvfile):
                    filename = 'backups/' + row['public_id']
                    if filename[-4:] != '.enc':
                        continue
                    self.decrypt_file(filename, password, filename[:-4])
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
                    original_filename = 'backups/' + row['public_id']
                    folder = os.path.dirname(original_filename)
                    filename = os.path.basename(original_filename)
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

    def cleanup(self) -> None:
        """Delete the unextracted and unencrypted files."""

    def retrieve(self) -> None:
        """To kick-off the entire process."""
        self.download()
        self.decrypt()


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
                    with requests.get(url, stream=True) as r, open(f"backups/{filename}", 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
        except Exception as e:
            print(f"Error reading summary.csv: {e}")
            sys.exit()
        logger.info("Step 1 (Download): Complete!")
        print("Step 1 (Download): Complete!")
