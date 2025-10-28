import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/")
    JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
    SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
