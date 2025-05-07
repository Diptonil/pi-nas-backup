from datetime import datetime
import logging
import subprocess
import sys
import os


LOG_FILENAME = datetime.now().strftime("%Y-%m-%d") + ".log"

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
            self.password = os.getenv("PASSWORD")
            self.validate_existence()
        except Exception:
            print("ERROR: Failed to access environment variables.")
            logger.error("Failed to access environment variables.")
            sys.exit()
    
    def validate_existence(self) -> None:
        if not self.cloud_name or not self.api_key or not self.api_secret or not self.password:
            raise Exception
        