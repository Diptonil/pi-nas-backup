from argparse import ArgumentParser


class Parser:
    """To parser CLI inputs particular to this application."""

    def __init__(self) -> None:
        self.parser = ArgumentParser(prog="BatBackup v1.0", description="Backup utility to sync local storage to Cloudinary with compression & encryption.", add_help=False)
        self.add_parser_arguments()
        self.args = vars(self.parser.parse_args())

    def __str__(self) -> str:
        return "The main argument parser."
    
    def add_parser_arguments(self) -> None:
        """Adds all required arguments to the parser."""
        options_group = self.parser.add_mutually_exclusive_group()
        options_group.add_argument("-h", "--help", action="help", help="To show this help message.")
        options_group.add_argument("-r", "--retrieve", action="store_true", help="To fetch backups from offsite.", default=False)
        options_group.add_argument("-e", "--encrypt", action="store_true", help="To encrypt data during backups.", default=False)

    def needs_retrieval(self) -> bool:
        """Returns if -r flag is passed."""
        return self.args["retrieve"]

    def needs_encryption(self) -> bool:
        """Returns if -e flag is passed."""
        return self.args["encrypt"]
