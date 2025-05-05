from argparse import ArgumentParser, FileType
import sys


class Parser:
    """Custom CLI parser."""

    def __init__(self) -> None:
        self.parser = ArgumentParser(prog="BatBackup v1.0", description="Backup utility to sync local storage to Cloudinary with compression & encryption.", add_help=False)
        self.add_parser_arguments()
        self.args = vars(self.parser.parse_args())

    def __str__(self) -> str:
        return "The main argument parser."
    
    def add_parser_arguments(self) -> None:
        """Adds all required arguments to the parser."""
        positional_arguments_group = self.parser.add_argument_group("POSITIONAL ARGUMENTS")
        positional_arguments_group.add_argument("file", nargs="?", type=FileType("r"), default=sys.stdin, help="The file path from where locations or folders to recurively back up are selected.")
        options_group = self.parser.add_mutually_exclusive_group()
        options_group.add_argument("-h", "--help", action="help", help="To show this help message.")
        options_group.add_argument("-r", "--retrieve", action="store_true", help="To fetch backups from offsite.")
        options_group.add_argument("-r", "--encrypt", action="store_true", help="To encrypt data during backups.")

    def get_file_name(self) -> str:
        """Returns the source file name."""
        return self.args["file"].name

    def needs_retrieval(self) -> bool:
        """Returns if -r flag is passed."""
        return self.args["retrieve"]

    def needs_encryption(self) -> bool:
        """Returns if -e flag is passed."""
        return self.args["encrypt"]
