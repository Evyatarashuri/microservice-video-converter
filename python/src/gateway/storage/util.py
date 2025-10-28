import pika, json

def upload(f, fs, channel, access):
    try:
        fid = fs.put(f.read())
        f.seek(0)
    except Exception as e:
        print("Failed to store file in GridFS:", e)
        return f"Internal server error: {e}", 500

    message = {
        "video_fid": str(fid),
        "mp3_fid": None,
        "username": access["username"],
    }

    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE,  # make message persistent
            ),
        )
    except Exception as e:
        fs.delete(fid)
        return f"Internal server error: {e}", 500
