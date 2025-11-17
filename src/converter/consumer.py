import pika, sys, os, time, json
from pymongo import MongoClient
import gridfs
from convert import to_mp3
from shared.logger import get_logger

logger = get_logger("converter")

def handle_video_message(ch, method, properties, body, fs_videos, fs_mp3s):
    """Handles messages from VIDEO_QUEUE — performs video → mp3 conversion"""
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"[VIDEO_QUEUE] Processing message (attempt {attempt+1}): {body}")
            err = to_mp3.start(body, fs_videos, fs_mp3s, ch)

            if not err:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info("[VIDEO_QUEUE] Conversion successful.")
                return

            raise Exception(err)

        except Exception as e:
            logger.error(f"[VIDEO_QUEUE] Attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)  # Exponential backoff

    logger.error(f"[VIDEO_QUEUE] Message failed after {MAX_RETRIES} attempts — skipping.")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def handle_mp3_message(ch, method, properties, body, db):
    """Handles messages from MP3_QUEUE — updates MongoDB with mapping info"""
    try:
        msg = json.loads(body)
        video_fid = msg.get("video_fid")
        mp3_fid = msg.get("mp3_fid")
        username = msg.get("username")

        if not video_fid or not mp3_fid:
            logger.warning(f"[MP3_QUEUE] Invalid message: {msg}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        db.conversions.update_one(
            {"video_fid": video_fid},
            {"$set": {"mp3_fid": mp3_fid, "username": username}},
            upsert=True
        )

        logger.info(f"[MP3_QUEUE] Saved mapping: video_fid={video_fid} → mp3_fid={mp3_fid}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"[MP3_QUEUE] Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    logger.info("Starting converter service (combined queues)...")

    # === MongoDB connection ===
    try:
        client = MongoClient("mongodb", 27017)
        db_videos = client.videos
        db_mp3s = client.mp3s
        logger.info("Connected to MongoDB.")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return

    # === RabbitMQ connection ===
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host="rabbitmq")
        )
        channel = connection.channel()
        logger.info("Connected to RabbitMQ.")
    except Exception as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        return

    # === Declare queues ===
    video_queue = os.environ.get("VIDEO_QUEUE", "video")
    mp3_queue = os.environ.get("MP3_QUEUE", "mp3")

    channel.queue_declare(queue=video_queue, durable=True)
    channel.queue_declare(queue=mp3_queue, durable=True)

    # === GridFS setup ===
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # === Bind callbacks ===
    channel.basic_consume(
        queue=video_queue,
        on_message_callback=lambda ch, m, p, b: handle_video_message(ch, m, p, b, fs_videos, fs_mp3s),
    )

    channel.basic_consume(
        queue=mp3_queue,
        on_message_callback=lambda ch, m, p, b: handle_mp3_message(ch, m, p, b, db_videos),
    )

    logger.info(f"Listening on queues: VIDEO_QUEUE='{video_queue}', MP3_QUEUE='{mp3_queue}'")
    logger.info("Waiting for messages. Press CTRL+C to exit.")

    # === Start consuming ===
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down gracefully")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == "__main__":
    main()
