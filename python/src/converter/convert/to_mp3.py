import tempfile, moviepy.editor, os, pika, json
from bson.objectid import ObjectId

def start(message, fs_videos, fs_mp3s, channel):
    message = json.loads(message)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tf:
        out = fs_videos.get(ObjectId(message["video_fid"]))
        tf.write(out.read())
        temp_video_path = tf.name

    if os.path.getsize(temp_video_path) == 0:
        print("❌ Error: video file is empty!")
        return "Empty video file", 500


    clip = moviepy.editor.VideoFileClip(temp_video_path)
    audio = clip.audio

    temp_audio_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(temp_audio_path)

    with open(temp_audio_path, "rb") as f:
        fid = fs_mp3s.put(f.read())

    os.remove(temp_video_path)
    os.remove(temp_audio_path)

    print(f"✅ MP3 saved with id: {fid}")

    message["mp3_fid"] = str(fid)
    channel.basic_publish(
        exchange="",
        routing_key=os.environ.get("MP3_QUEUE"),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        )
    )
