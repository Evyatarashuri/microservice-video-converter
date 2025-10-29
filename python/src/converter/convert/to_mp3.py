import tempfile, moviepy.editor, os, pika, json
from bson.objectid import ObjectId
from monitoring.logger import get_logger

logger = get_logger("converter")

def start(message, fs_videos, fs_mp3s, channel):
    try:
        # Parse message
        message = json.loads(message)
        video_id = message.get("video_fid")
        logger.info(f"Starting conversion process for video_fid={video_id}")

        # Retrieve video from GridFS
        try:
            out = fs_videos.get(ObjectId(video_id))
            logger.info("Fetched video from GridFS successfully.")
        except Exception as e:
            logger.error(f"Failed to fetch video from GridFS: {e}")
            return f"Failed to fetch video: {e}", 500

        # Write to temporary MP4 file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
            tf.write(out.read())
            temp_video_path = tf.name
        logger.info(f"Video written to temporary file: {temp_video_path}")

        # Check file integrity
        file_size = os.path.getsize(temp_video_path)
        if file_size == 0:
            logger.error("Video file is empty after writing from GridFS.")
            return "Empty video file", 500
        else:
            logger.debug(f"Video file size: {file_size} bytes")

        # Extract audio
        try:
            logger.info("Opening video file with MoviePy...")
            clip = moviepy.editor.VideoFileClip(temp_video_path)
            audio = clip.audio
            logger.info("Audio track extracted successfully.")
        except Exception as e:
            logger.error(f"Failed to process video with MoviePy: {e}")
            return f"MoviePy error: {e}", 500

        # Write temporary MP3
        temp_audio_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp3")
        try:
            logger.info(f"Writing audio to temporary MP3 file: {temp_audio_path}")
            audio.write_audiofile(temp_audio_path)
        except Exception as e:
            logger.error(f"Failed to write audio to MP3: {e}")
            return f"Audio write error: {e}", 500
        finally:
            audio.close()
            clip.close()

        # Store MP3 in GridFS
        try:
            with open(temp_audio_path, "rb") as f:
                fid = fs_mp3s.put(f.read())
            logger.info(f"Stored MP3 in GridFS successfully. mp3_fid={fid}")
        except Exception as e:
            logger.error(f"Failed to save MP3 to GridFS: {e}")
            return f"MP3 storage error: {e}", 500

        # Cleanup temp files
        try:
            os.remove(temp_video_path)
            os.remove(temp_audio_path)
            logger.debug("Temporary files deleted successfully.")
        except Exception as e:
            logger.warning(f"Failed to delete temporary files: {e}")

        # Publish result to MP3 queue
        try:
            message["mp3_fid"] = str(fid)
            logger.info(f"Publishing message to MP3 queue: {message}")
            channel.basic_publish(
                exchange="",
                routing_key=os.environ.get("MP3_QUEUE"),
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
            logger.info("Message published to MP3 queue successfully.")
        except Exception as e:
            logger.error(f"Failed to publish to MP3 queue: {e}")
            return f"RabbitMQ publish error: {e}", 500

        logger.info("Conversion process completed successfully.")
        return None

    except Exception as e:
        logger.error(f"Unexpected error in to_mp3.start(): {e}")
        return f"Internal error: {e}", 500
