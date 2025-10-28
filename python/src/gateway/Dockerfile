FROM python:3.10-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    python3-dev \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python3", "server.py"]
