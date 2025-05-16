from datetime import datetime
import psutil
import os
import time
import platform
import logging

from utils.backup_generator import CloudinaryBackupGenerator
from utils.backup_unpacker import CloudinaryBackupRetriever


def get_logger(filename: str):
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    log_handler = logging.FileHandler(f'reports/{filename}')
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(log_formatter)
    logger.addHandler(log_handler)
    return logger


def benchmark_code(log_filename: str):
    if log_filename == "backup-generation.log":
        backup_generator = CloudinaryBackupGenerator(is_encrypted=True)
        backup_generator.back_up()
    else:
        backup_retriever = CloudinaryBackupRetriever()
        backup_retriever.retrieve()


def log_resource_usage(log_filename: str):
    logger = get_logger(log_filename)
    process = psutil.Process(os.getpid())
    start_time = time.time()
    
    cpu_times_start = process.cpu_times()
    io_counters_start = process.io_counters()
    
    benchmark_code(log_filename)
    
    end_time = time.time()
    cpu_times_end = process.cpu_times()
    mem_info_end = process.memory_info()
    io_counters_end = process.io_counters()

    logger.info("Benchmarking Bat Backup v1.0.0. The numbers below are approximate figures.")
    logger.info("Backup mode selected (with encryption)." if log_filename == "backup-generation.log" else "Retrieval mode selected.")
    logger.info(f"Date & Time: {datetime.now()}")
    logger.info("")
    logger.info(f"OS: {platform.system()}")
    logger.info(f"OS Version: {platform.version()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architcture: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Total Memory (GB): {psutil.virtual_memory().total / 1000000000}")
    logger.info(f"Disk (GB): {psutil.disk_usage('/').total / 1000000000}")
    logger.info("")
    logger.info(f"Execution Time (minutes): {(end_time - start_time) / 60}")
    logger.info(f"CPU (User) Time (minutes): {(cpu_times_end.user - cpu_times_start.user) / 60}")
    logger.info(f"CPU (System) Time (minutes): {(cpu_times_end.system - cpu_times_start.system) / 60}")
    logger.info(f"Virtual Memory (MB): {mem_info_end.vms / (1024 * 1024)}")
    logger.info(f"Resident Set Memory (MB): {mem_info_end.rss / (1024 * 1024)}")
    logger.info(f"I/O Read (MB): {(io_counters_end.read_bytes - io_counters_start.read_bytes) / (1024 * 1024)}")
    logger.info(f"I/O Write (MB): {(io_counters_end.write_bytes - io_counters_start.write_bytes) / (1024 * 1024)}")


if __name__ == "__main__":
    log_resource_usage("backup-generation.log")
    log_resource_usage("backup-unpacking.log")
