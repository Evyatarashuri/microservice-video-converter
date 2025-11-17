import pika, os, json
from pymongo import MongoClient
from shared.logger import get_logger

logger = get_logger("result_consumer")

def main():
    # Connect to MongoDB
    client = MongoClient("mongodb", 27017)
    db = client.videos

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )
    channel = connection.channel()

    # Declare the MP3 queue
    mp3_queue = os.environ.get("MP3_QUEUE", "mp3")
    channel.queue_declare(queue=mp3_queue, durable=True)
    logger.info(f"Listening to MP3 queue: {mp3_queue}")

    def callback(ch, method, properties, body):
        try:
            msg = json.loads(body)
            video_fid = msg.get("video_fid")
            mp3_fid = msg.get("mp3_fid")
            username = msg.get("username")

            if not video_fid or not mp3_fid:
                logger.warning(f"Invalid message: {msg}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Update mapping between video_fid and mp3_fid
            db.conversions.update_one(
                {"video_fid": video_fid},
                {"$set": {"mp3_fid": mp3_fid, "username": username}},
                upsert=True
            )

            logger.info(f"Saved mapping: video_fid={video_fid} → mp3_fid={mp3_fid}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Start consuming
    channel.basic_consume(queue=mp3_queue, on_message_callback=callback)
    logger.info("Waiting for MP3 messages...")
    channel.start_consuming()


if __name__ == "__main__":
    main()
