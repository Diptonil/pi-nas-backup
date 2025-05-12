import csv
import sys
import os
import shutil

import cloudinary
import requests

from utils.misc import logger, Credentials


SUMMARY_FILENAME = "reports/summary.csv"


class BackupRetriever:
    """To unpack the backups."""

    def __init__(self) -> None:
        self.summary = []
        self.credentials = Credentials()
        logger.info("Initiating Bat Backup v1.0.0.")
        logger.info("Retrieval mode selected.")
        logger.info("Starting the 3-step process now.")

    def download(self) -> None:
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

    def decompress(self) -> None:
        """Unzips the files and folders."""

    def decrypt(self) -> None:
        """Decrypts files that are encrypted."""

    def cleanup(self) -> None:
        """Delete the unextracted and unencrypted files."""

    def retrieve(self) -> None:
        """To kick-off the entire process."""
        self.download()
