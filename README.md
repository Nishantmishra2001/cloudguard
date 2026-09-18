# CloudGuard

CloudGuard is a cost-aware self-service preview environment platform that creates temporary Docker-based application environments with automatic expiry and resource monitoring.

## Features

- Self-service preview environment creation
- Temporary Docker containers
- Dynamic host port allocation
- CPU and memory monitoring
- Configurable TTL
- Automatic expired-container cleanup
- Branch and commit metadata
- Flask REST API
- Web monitoring dashboard
- Docker-based deployment
- AWS EC2 deployment
- GitHub Actions CI/CD
- Terraform infrastructure

## Architecture

Developer
    |
    v
GitHub
    |
    v
GitHub Actions
    |
    v
AWS EC2
    |
    v
CloudGuard Flask API
    |
    v
Docker Engine
    |
    v
Temporary Flask Preview Container
    |
    +----> CPU / Memory Monitoring
    |
    +----> TTL Manager
              |
              v
        Automatic Cleanup

## Preview Environment Flow

1. Developer requests a preview environment.
2. CloudGuard validates the request and TTL.
3. CloudGuard creates a Docker container.
4. Docker assigns a dynamic host port.
5. CloudGuard returns a preview URL.
6. CPU and memory metrics are collected.
7. Environment remains active until its TTL expires.
8. Expired containers are automatically removed.

## Technology Stack

- Python
- Flask
- Docker
- Docker SDK
- AWS EC2
- GitHub Actions
- Terraform
- HTML
- CSS
- JavaScript

## Project Structure

cloudguard/
├── app/
│   ├── main.py
│   ├── templates/
│   │   └── index.html
│   └── static/
├── preview_app/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── tests/
├── terraform/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── aws-deploy.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md

## Run Locally

Build the preview application:

docker build -t cloudguard-preview:1.0 ./preview_app

Build CloudGuard:

docker build -t cloudguard:8.0 .

Run CloudGuard:

docker run -d \
  --name cloudguard \
  -p 5000:5000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  cloudguard:8.0

Open:

http://localhost:5000

## API

Health Check:

GET /health

List Environments:

GET /environments

Create Environment:

POST /environments

Example request:

{
  "branch": "feature/demo",
  "commit": "abc123",
  "ttl_minutes": 60
}

Delete Environment:

DELETE /environments/<environment_id>

## AWS Deployment

CloudGuard can run on an AWS EC2 instance with Docker installed.

The CloudGuard container requires access to the Docker socket:

/var/run/docker.sock

The preview application image must also be available on the EC2 Docker host:

docker build -t cloudguard-preview:1.0 ./preview_app

## Why CloudGuard?

Preview environments are useful for testing application changes before merging them into a main environment.

Temporary environments can continue consuming cloud resources after they are no longer needed.

CloudGuard addresses this with:

- On-demand provisioning
- Explicit TTL
- Automatic cleanup
- Resource monitoring
- Dynamic preview URLs

## Project Status

Core functionality has been implemented and tested locally and on AWS EC2.

Verified:

- Docker provisioning
- Flask preview application
- Dynamic port allocation
- CPU monitoring
- Memory monitoring
- TTL expiry
- Automatic cleanup
- AWS EC2 deployment
- GitHub Actions workflow
- Terraform infrastructure

## Author

Nishant Kumar Mishra

DevOps / Cloud Engineering Portfolio Project
