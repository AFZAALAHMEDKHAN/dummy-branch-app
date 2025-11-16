# Branch Loan API - Production Ready Documentation

Minimal REST API for microloans, now containerized and production-ready with CI/CD and multi-environment support.

---

## Architecture Diagram

The service architecture relies on a Reverse Proxy (Nginx) to handle encrypted HTTPS traffic and forward it to the internal application container. The application communicates with a dedicated PostgreSQL database container on the internal Docker network.

````mermaid
graph LR
subgraph External Access
USER[Borrower/Engineer]
end

    subgraph Internal Docker Network
        NGINX_C(Nginx Reverse Proxy)
        API_C(Loan API Service)
        DB_C[PostgreSQL Database]
    end

    USER -- 1. HTTPS (branchloans.com:443) --> NGINX_C
    NGINX_C -- 2. HTTP (api:8000) --> API_C
    API_C -- 3. Internal DB Connection --> DB_C

    NGINX_C -. Uses .-> SSL_CERT[Self-Signed Certificate]
    API_C -. Reads .-> ENV_VARS[Environment Variables]
    DB_C -- Data Persistence --> VOLUME[db_data Volume]
````

## How to Run Locally (Development Environment)
This setup runs the API over **HTTPS** via (https://branchloans.com).

### Prerequisites
- **Docker** and **Docker Compose** installed.

- **Clone the repository** and ensure you have an `.env` file (copied from `.env.example`) with necessary secrets.

### Step-by-Step Instructions

1. **Generate Self-Signed SSL Certificate (Crucial!)**:The Nginx proxy requires a self-signed certificate and key to serve HTTPS locally.Run the following command from the project root to generate the files and place them in the `nginx/` directory:

```Bash
# Generate the certificate and key (valid for 365 days)

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
 -keyout nginx/branchloans.key \
 -out nginx/branchloans.crt \
 -subj "/CN=branchloans.com"
````

2. **Update Local Hosts File**: You must map the domain **branchloans.com** to your local machine `(127.0.0.1)`.

- **Linux/macOS**: Edit `/etc/hosts`

- **Windows**: Edit `C:\Windows\System32\drivers\etc\hosts`

- Add the following line to the file:

    ```
    127.0.0.1 branchloans.com
    ```

3. **Start Services (Development)**: We use the base `docker-compose.yml` and the development override file.

```Bash

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

4. **Run DB Migrations**:

```Bash

docker compose exec api alembic upgrade head
```

5. **Seed Dummy Data**:

```Bash

docker compose exec api python scripts/seed.py
```

6. **Verify & Test**: You must use `https` and the mapped domain. Your browser/client will show a certificate warning, which is expected for a self-signed certificate.

```Bash

# Test Health Check

curl -k https://branchloans.com/health

# Expected output: {"database": "reachable", "status": "ok"}

# List Loans

curl -k https://branchloans.com/api/loans
```

## Environment Management
The application supports three environments (**development**, **staging**, and **production**) using a core `docker-compose.yml` file combined with environment-specific override files.

### Switching Environments
To switch, substitute the override file name in the `docker compose` command:


| Environment | Use Case                                                                          | Command                                                                    |
| :---        |  :---                                                                             | :---                                                                       |
| Development | Local coding, hot reload enabled, debug logging, local ports exposed.             | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`     |
| Staging     | QA testing, resource limits applied, standard logging, mimicks prod setup.        | `docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d` |
| Production  | Optimized resource limits, higher Gunicorn worker count, structured JSON logging. | `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`    |


### Environment Variable Reference
These variables are defined in the `.env` file and consumed by the services.
 
| Variable              | Service | Default Value (Example)     | Description                                        |
| :---                  | :---    | :---                        | :---                                               |
| **POSTGRES_USER**     | `db`    | `postgres`                  | Database superuser username.                       |
| **POSTGRES_PASSWORD** | `db`    | `postgres`                  | Database superuser password. (Must be kept secret) |
| **POSTGRES_DB**       | `db`    | `microloans`                | Name of the initial database.                      |
| **API_DATABASE_URL**  | `api`   | `postgresql+psycopg2://...` | Full connection string used by the API service.    |

Variable,Service,Default Value (Example),Description
POSTGRES_USER,db,postgres,Database superuser username.
POSTGRES_PASSWORD,db,postgres,Database superuser password. (Must be kept secret)
POSTGRES_DB,db,microloans,Name of the initial database.
API_DATABASE_URL,api,postgresql+psycopg2://...,Full connection string used by the API service.

CI/CD Pipeline (.github/workflows/ci-cd.yml)
The pipeline automates quality checks and deployment readiness using GitHub Actions.

Stage,Triggered By,Purpose,Artifacts,Failure Criteria

1. Test,"Push, Pull Request",Installs dependencies and runs unit tests.,None,Tests fail
2. Build & Scan,Success of Test Stage,Builds the Docker image and scans it for vulnerabilities.,Built Docker Image (as artifact),Critical vulnerabilities found by Trivy.
3. Push,Success of Build & Scan Stage,Tags and pushes the verified image to GitHub Container Registry (ghcr.io).,Pushed Image,Only runs on push to main branch.

Key Security and Workflow Details
Secrets: All registry login credentials are handled securely using the built-in ${{ secrets.GITHUB_TOKEN }} variable; no sensitive passwords are hardcoded or visible in logs.

Tagging: Images are tagged with the short Git SHA, the branch name, and the latest tag (only for main branch pushes).

PRs: Pull Requests trigger the Test and Build & Scan stages but do NOT proceed to the Push stage, ensuring that only merged code is released.

Troubleshooting
Issue,Description,Fix/Check
Cannot access https://branchloans.com,The browser gives a DNS error or connection refused.,Did you update your /etc/hosts file? Check that Docker containers are running (docker ps).
curl shows certificate error (expected),curl: (60) SSL certificate problem: self-signed certificate,This is expected for local development. Use the -k or --insecure flag with curl to proceed.
API Container Restarting (Crash Loop),The api container shows restarting status.,Run docker compose logs api to check the logs. It's likely a database connection issue or a misconfigured environment variable in the .env file.
Database connection fails (503),"Hitting /health returns {""database"": ""unreachable""} (503).",Check the database health: docker compose logs db. Ensure the DB container is fully running and healthy (health check passed).
