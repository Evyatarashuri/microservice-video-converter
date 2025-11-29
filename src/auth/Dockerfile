FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    python3-dev \
    libpq-dev \
    netcat-openbsd \
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
COPY protos /app/protos

# Generate gRPC files for Auth service
RUN python3 -m grpc_tools.protoc \
    --proto_path=/app/protos \
    --python_out=/app/auth \
    --grpc_python_out=/app/auth \
    /app/protos/auth.proto

ENV PYTHONPATH=/app

EXPOSE 5000
EXPOSE 50051

# ==========================================
# Wait for PostgreSQL + Run Alembic + Start Flask
# ==========================================
CMD sh -c "until nc -z $POSTGRES_HOST 5432; do echo 'Waiting for PostgreSQL...'; sleep 2; done; echo 'PostgreSQL is up!'; alembic upgrade head; python3 auth/server.py & python3 auth/grpc_server.py"

# ===========================
# Docker build instructions
# ===========================
# docker build -t evyatar213/auth:latest -f auth/Dockerfile .
# docker push evyatar213/auth:latest
# kubectl rollout restart deployment auth
# kubectl apply -f auth/manifests/
