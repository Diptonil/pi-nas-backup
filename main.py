from application import BackupGenerator
from parser import Parser


def main() -> None:
    parser = Parser()
    is_encryption_required = parser.needs_encryption()
    is_for_retrieval = parser.needs_retrieval() 
    if not is_for_retrieval:
        backup_generator = BackupGenerator(is_encrypted=is_encryption_required)
        backup_generator.start()
    else:
        pass


if __name__ == '__main__':
    main()
