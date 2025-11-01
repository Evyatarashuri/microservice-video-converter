FROM python:3.10-slim-bullseye

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  build-essential ffmpeg \
  && pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY converter/requirements.txt /app/converter/requirements.txt

RUN pip install --no-cache-dir --requirement /app/converter/requirements.txt

COPY converter /app/converter
COPY shared /app/shared

ENV PYTHONPATH=/app

CMD ["python3", "converter/consumer.py"]


# Running docker build only from src directory

# docker build -t evyatar213/converter:latest -f converter/Dockerfile .
# docker push evyatar213/converter:latest
# kubectl apply -f converter/manifests/
# kubectl delete -f converter/manifests/


# kubectl rollout restart deployment converter