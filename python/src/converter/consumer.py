import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3
from monitoring.logger import get_logger


logger = get_logger("converter")


def main():

    logger.info("Starting converter service...")

    # MongoDB connection
    try:
        client = MongoClient("mongodb", 27017)
        db_videos = client.videos
        db_mp3s = client.mp3s
        logger.info("Connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # RabbitMQ connection
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()
        logger.info("Connected to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return

    # GridFS setup
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)


    def callback(ch, method, properties, body):
        logger.debug(f"Received message: {body}.")
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            logger.error(f"Error processing message: {err}")
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            logger.info("Conversion successful.")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"),
        on_message_callback=callback
    )

    # Start consuming messages
    logger.info("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)