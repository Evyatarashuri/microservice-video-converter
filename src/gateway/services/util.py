import pika, json
from shared.logger import get_logger

logger = get_logger("storage")

def upload(f, fs, channel, access):
    try:
        logger.info(f"Uploading file: {f.filename}")
        fid = fs.put(f.read())
        f.seek(0)
        logger.info(f"File stored in GridFS with ID: {fid}")
    except Exception as e:
        logger.error(f"Failed to store file in GridFS: {e}")
        return f"Internal server error: {e}", 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    logger.info(f"Publishing message to RabbitMQ: {message}")

    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,  # make message persistent
            ),
        )
        
        channel.close()
        connection.close()
        logger.info(f"Message published to RabbitMQ for file ID: {fid}")

    except Exception as e:
        fs.delete(fid)
        logger.error(f"Failed to publish message to RabbitMQ: {e}")
        return f"Internal server error: {e}", 500
