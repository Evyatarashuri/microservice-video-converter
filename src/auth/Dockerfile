FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY auth/requirements.txt /app/auth/requirements.txt

RUN pip install --no-cache-dir -r auth/requirements.txt

COPY auth /app/auth
COPY auth/alembic.ini /app/
COPY auth/migrations /app/migrations
COPY shared /app/shared

ENV PYTHONPATH=/app

EXPOSE 5000

# =============================
# Alembic migration integration
# =============================
# Run database migrations automatically before starting the app
# This will only apply pending migrations (it’s idempotent)
CMD alembic upgrade head && python3 auth/server.py

# Running docker build only from src directory

# docker build -t evyatar213/auth:latest -f auth/Dockerfile .
# docker push evyatar213/auth:latest
# kubectl rollout restart deployment auth

# kubectl apply -f auth/manifests/
