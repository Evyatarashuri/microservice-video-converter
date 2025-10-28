from python:3.10-slim

WORKDIR /app

COPY ../shared/ /app/shared/

ENV PYTHONPATH="/app"

RUN pip install --no-cache-dir pika python-dotenv requests

CMD ["python3", "-c", "print('Base image ready with shared modules')"]
