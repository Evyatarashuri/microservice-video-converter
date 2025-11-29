FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app

# Install dependencies
COPY gateway/requirements.txt /app/gateway/requirements.txt
RUN pip install --no-cache-dir -r gateway/requirements.txt

# Copy source code
COPY gateway /app/gateway
COPY shared /app/shared
COPY protos /app/protos

# Create grpc directory before generating code
RUN mkdir -p /app/gateway/clients/grpc && touch /app/gateway/clients/grpc/__init__.py

# Generate gRPC files
RUN python3 -m grpc_tools.protoc \
    --proto_path=/app/protos \
    --python_out=/app/gateway \
    --grpc_python_out=/app/gateway \
    /app/protos/auth.proto

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python3", "gateway/server.py"]
