from utils.misc import get_size_gb, logger, Credentials

        
class BackupRetriever:
    """To unpack the backups."""

    def __init__(self) -> None:
        self.summary = []
        self.credentials = Credentials()
        self.location_data = self.get_location_data()
        logger.info("Initiating Bat Backup v1.0.0.")
        logger.info("Retrieval mode selected.")
        logger.info("Starting the 3-step process now.")

    def download(self) -> None:
        """Fetches files from Cloudinary."""

    def retrieve(self) -> None:
        """To kick-off the entire process."""
        self.download()
