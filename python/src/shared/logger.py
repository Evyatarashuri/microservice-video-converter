import logging
import sys
import json
from datetime import datetime

def get_json_logger(service_name: str):
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "service": service_name,
                "message": record.getMessage(),
            }
            return json.dumps(log_entry)

    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    return logger
