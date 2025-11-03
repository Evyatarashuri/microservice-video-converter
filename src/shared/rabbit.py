import pika, time
from shared.logger import get_logger

logger = get_logger("rabbit")

class RabbitMQConnection:
    def __init__(self, host="rabbitmq", retries=5, delay=3):
        self.host = host
        self.retries = retries
        self.delay = delay
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ with retry logic."""
        for attempt in range(1, self.retries + 1):
            try:
                logger.info(f"[RabbitMQ] Connecting to {self.host} (attempt {attempt})")
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.host)
                )
                self.channel = self.connection.channel()
                logger.info("[RabbitMQ] Connection established successfully")
                return
            except Exception as e:
                logger.warning(f"[RabbitMQ] Connection attempt {attempt} failed: {e}")
                time.sleep(self.delay)
        raise ConnectionError("[RabbitMQ] Could not connect after several attempts.")

    def get_channel(self):
        """Return a valid channel or reconnect if necessary."""
        if not self.connection or self.connection.is_closed:
            logger.warning("[RabbitMQ] Connection closed. Reconnecting...")
            self.connect()
        if not self.channel or self.channel.is_closed:
            logger.warning("[RabbitMQ] Channel closed. Reopening...")
            self.channel = self.connection.channel()
        return self.channel

    def close(self):
        """Gracefully close connection."""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and self.connection.is_open:
                self.connection.close()
            logger.info("[RabbitMQ] Connection closed cleanly")
        except Exception as e:
            logger.warning(f"[RabbitMQ] Error closing connection: {e}")
