import os, gridfs, pika, json
from flask import Flask, request, send_file, render_template, redirect, url_for, send_file, flash
from flask_pymongo import PyMongo
from auth import validate
from api import login_api, register_api, download_api
from api.upload_api import create_upload_blueprint
from clients.rest import auth_client
from services import util
from shared.rabbit import RabbitMQConnection
from bson.objectid import ObjectId
import requests


server = Flask(__name__,
               template_folder="templates",
               static_folder="static"
            )

mongo_video = PyMongo(server, uri=os.getenv("MONGO_URI_VIDEO"))
mongo_mp3 = PyMongo(server, uri=os.getenv("MONGO_URI_MP3"))

fs_videos = gridfs.GridFS(mongo_video.db)
fs_mp3s = gridfs.GridFS(mongo_mp3.db)

# ====== RabbitMQ Connection ======
rabbit_connection = RabbitMQConnection()
rabbit_connection.connect()

# ====== Dependency Injection ======
upload_blueprint = create_upload_blueprint(rabbit_connection)


# ====== Routes ======
server.register_blueprint(login_api)
server.register_blueprint(upload_blueprint)
server.register_blueprint(register_api)
server.register_blueprint(download_api)


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)