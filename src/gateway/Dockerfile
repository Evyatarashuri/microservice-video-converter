FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY gateway/requirements.txt /app/gateway/requirements.txt

RUN pip install --no-cache-dir -r gateway/requirements.txt

COPY gateway /app/gateway
COPY shared /app/shared
COPY protos /app/protos

# Generate gRPC files for Gateway client
RUN python3 -m grpc_tools.protoc \
    --proto_path=/app/protos \
    --python_out=/app/gateway/clients/grpc \
    --grpc_python_out=/app/gateway/clients/grpc \
    /app/protos/auth.proto

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python3", "gateway/server.py"]


# Running docker build only from src directory

# docker build -t evyatar213/gateway:latest -f gateway/Dockerfile .
# docker push evyatar213/gateway:latest
# kubectl rollout restart deployment gateway

# kubectl apply -f gateway/manifests/
# kubectl delete -f gateway/manifests/


