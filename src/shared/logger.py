import logging
import sys
from logging.handlers import SysLogHandler

# ================================================================
#  Centralized Logger - sends logs to both console and Logstash
# ================================================================

LOGSTASH_HOST = "logstash.monitoring.svc.cluster.local"  # internal DNS name inside Minikube
LOGSTASH_PORT = 5000

def get_logger(service_name: str):
    """
    Creates a logger that sends logs both to stdout and to Logstash.
    Each log line includes timestamp, service name, level, and message.
    """

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if the logger was already configured
    if logger.hasHandlers():
        logger.handlers.clear()

    # ===== Console Handler =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # ===== Logstash Handler =====
    try:
        syslog_handler = SysLogHandler(address=(LOGSTASH_HOST, LOGSTASH_PORT))
        syslog_handler.setFormatter(console_format)
        logger.addHandler(syslog_handler)
    except Exception as e:
        logger.warning(f"Could not connect to Logstash at {LOGSTASH_HOST}:{LOGSTASH_PORT} ({e})")

    return logger
