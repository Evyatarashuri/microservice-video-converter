# logger_config.py
import logging
import sys

def get_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f"%(asctime)s | {service_name.upper()} | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
