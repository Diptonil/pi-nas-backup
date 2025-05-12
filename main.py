from utils.backup_generator import CloudinaryBackupGenerator
from utils.backup_unpacker import CloudinaryBackupRetriever
from utils.parser import Parser


def main() -> None:
    parser = Parser()
    is_encryption_required = parser.needs_encryption()
    is_for_retrieval = parser.needs_retrieval() 
    if is_for_retrieval:
        backup_retriever = CloudinaryBackupRetriever()
        backup_retriever.retrieve()
    else:
        backup_generator = CloudinaryBackupGenerator(is_encrypted=is_encryption_required)
        backup_generator.back_up()


if __name__ == '__main__':
    main()
