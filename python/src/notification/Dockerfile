FROM python:3.10-slim-bullseye

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
  build-essential \
  && pip install --no-cache-dir --upgrade pip

WORKDIR /app

COPY notification/requirements.txt /app/notification/requirements.txt

RUN pip install --no-cache-dir --requirement /app/notification/requirements.txt

COPY notification /app/notification
COPY shared /app/shared

ENV PYTHONPATH=/app

CMD ["python3", "notification/consumer.py"]

# Running docker build only from src directory

# docker build -t evyatar213/notification:latest -f notification/Dockerfile .
# docker push evyatar213/notification:latest

# kubectl rollout restart deployment notification

# kubectl apply -f notification/manifests/
# kubectl delete -f notification/manifests/