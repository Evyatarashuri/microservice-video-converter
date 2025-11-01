import pika, sys, os, time
from send import email
from shared import logger

logger = logger.get_logger("notification")

def main():

    logger.info("Starting notification service...")

    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq"))
        channel = connection.channel()
        logger.info("Connected to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return
    
    channel.queue_declare(queue=os.environ.get("MP3_QUEUE"), durable=True)

    def callback(ch, method, properties, body):
        err = email.notification(body)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("MP3_QUEUE"),
        on_message_callback=callback
    )

    logger.info("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)