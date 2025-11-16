# Design Decisions

This document outlines the architectural choices, trade-offs, and future improvements considered during the process of containerizing and productionizing the Branch Loan API service.

## Part 1: Containerization & HTTPS

**Reverse Proxy Choice (Nginx)**

I chose **Nginx** as the reverse proxy to handle the mandatory HTTPS requirement. Nginx is robust, lightweight, and widely understood, which makes it easy for other engineers to support.

- **Alternatives Considered**: I considered **Traefik** and **Caddy**. Caddy is excellent for automatically managing certificates (like Let's Encrypt), and Traefik is powerful for microservices and automatic discovery. However, for a simple, self-contained local development requirement, Nginx provided the most straightforward path with the least amount of complex setup code.

- **Nginx Configuration**: The Nginx configuration (`nginx.conf`) and the generated certificate/key files are made available to the Nginx container using **bind mounts**. This allows changes to the configuration to be applied quickly in development without rebuilding the Nginx image.

**API Health Check**

A robust health check is essential for readiness and monitoring. The API service now includes a health check in its Docker Compose definition: `["CMD", "curl", "-f", "http://localhost:8000/health"]`.

**Reasoning**: This approach is superior to a simple `echo "OK"` because the `/health` endpoint in the Flask application (`app/routes/health.py`) performs an actual **database connectivity test** before reporting success. If the database is down, the container will report as unhealthy, correctly reflecting the service's operational status.

**curl in Dockerfile**: I installed curl in the main Dockerfile specifically to make this Docker Compose health check possible. While slightly increasing the image size, using a standard tool like `curl` is more reliable and simpler than trying to implement the HTTP request purely in Python within the health check context.

## Part 2: Multi-Environment Setup

**Docker Compose Structure**

The decision was made to use a base `docker-compose.yml` for common definitions (API, DB, volumes, environment variables) and separate **override** files (`.dev.yml`, `.staging.yml`, `.prod.yml`).

**Rationale**: This fulfills the requirement for a single setup while allowing for clear differentiation. The base file guarantees core functionality and shared network names, while overrides handle specific changes like resource limits (`deploy: resources`), exposed ports, and environment-specific commands.

**Environment Variables**: I used Docker Compose's ability to interpolate variables (e.g., `${POSTGRES_USER}`) from a `.env` file, ensuring no secrets are hardcoded in any configuration file. This is a crucial security best practice.

**Logging**: I planned for **Structured JSON Logging** in production by defining the `LOG_FORMAT: json` variable in `docker-compose.prod.yml` and including it in `app/config.py`. The actual implementation of the JSON formatter is a clear next step (improvement area).

## Part 3: CI/CD Pipeline

**Pipeline Structure (Separate Jobs)**

The CI/CD workflow uses three distinct jobs: **Test**, **Build & Scan**, and **Push**, linked sequentially using `needs:`.

**Rationale vs. Trade-off**: I could have combined the **Build, Scan, and Push** stages into a single job. However, separating them provides **clearer visibility** into which exact step failed (e.g., did the build fail, or did the scan fail?). More importantly, separating the jobs allows us to pass the built image as an artifact. This ensures the exact same binary (the scanned image) is the one that is pushed, eliminating any possibility of an un-scanned image being released.

**Image Tagging and Security**

**Tagging**: I used the `docker/metadata-action` to tag images with multiple informative tags (Git SHA and branch name). This ensures traceability—we know exactly which commit corresponds to which image.

**Image Digest**: I did not rely solely on the image digest for tracking. While digests are immutable and cryptographically sound, they are less human-readable than SHA tags, making it harder for a human to quickly identify the version running in an environment. I prioritized traceability while still achieving immutability through the SHA tag.

**Conditional Push Logic**: The push job includes an `if: github.ref == 'refs/heads/main' `condition. This implements the core requirement to **only push images when code is merged to the main branch**, preventing the registry from being cluttered with images from feature branch Pull Requests.

## What Would I Improve with More Time?

1. **Observability and Monitoring**: The top priority would be implementing the **Prometheus and Grafana** setup. This involves:

   - Adding a proper metrics exporter (e.g., `prometheus_flask_exporter`) to the Flask app.

   - Setting up the Prometheus and Grafana services in Docker Compose.

   - This would provide real-time visibility into request counts, latencies, and error rates.

2. **Structured Logging Implementation**: I would complete the implementation of **JSON-formatted logging** using a library like `python-json-logger`. Currently, the environment variable is set, but the actual formatter logic within `app/__init__.py` needs to be finalized to make the logs machine-readable and parsable by log aggregation systems.

3. **Full DB Migration Automation**: While we run the migration step manually via `docker compose exec`, a more production-ready approach for cloud environments would be an entrypoint script that runs migrations automatically on startup (or via a separate job) before the API service starts.

**Note**: All procedural instructions, environment variable details, and troubleshooting guides are located in the `README.md` file.
