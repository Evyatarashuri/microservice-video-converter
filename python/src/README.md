# 🎬 Microservices Media Converter

This project demonstrates a production-grade microservice architecture using:
- Python (FastAPI, Flask)
- RabbitMQ (message broker)
- MongoDB + MySQL
- Kubernetes (Minikube)
- Dockerized microservices with CI/CD

## 🧩 Architecture
![Architecture Diagram](docs/architecture.png)

Each service:
- Auth → Manages JWT and users
- Converter → Processes video/audio tasks
- Notification → Sends email updates
- Gateway → Entry point (API Gateway)
