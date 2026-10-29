# CloudOps — Complete Observability System

### DevOps Internship Final Project | Project 3

A containerized observability platform that implements **metrics, centralized logging, and distributed tracing** for a Node.js application.

The project uses Docker Compose to deploy and connect seven services, providing visibility into application availability, performance, errors, logs, and request traces.

## 1. Project Overview

The objective of this project is to implement the three pillars of observability:

1. **Metrics:** Monitor application performance and availability using Prometheus.
2. **Logs:** Collect and explore structured application logs using Grafana Alloy and Loki.
3. **Traces:** Trace HTTP requests using OpenTelemetry and Jaeger.

Grafana provides dashboards for metrics visualization and an interface for exploring logs.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Node.js + Express.js | Application |
| Docker + Docker Compose | Containerization and orchestration |
| Prometheus | Metrics collection |
| Grafana | Dashboards and log exploration |
| Grafana Loki | Centralized log storage |
| Grafana Alloy | Container log collection |
| OpenTelemetry | Application instrumentation |
| OpenTelemetry Collector | Trace collection and forwarding |
| Jaeger | Distributed trace visualization |

## 3. System Architecture

**Metrics pipeline**

Node.js Application → Prometheus → Grafana

**Logging pipeline**

Node.js Application → Docker Logs → Grafana Alloy → Loki → Grafana

**Tracing pipeline**

Node.js Application → OpenTelemetry → OpenTelemetry Collector → Jaeger

All components communicate through the Docker Compose network.

## 4. Key Features

- Application health monitoring
- HTTP request counters and request rate
- HTTP 5xx error monitoring
- Average response latency
- Node.js CPU and memory monitoring
- Structured JSON application logs
- Centralized log exploration
- HTTP request tracing
- Automatically provisioned Grafana data sources and dashboard
- Persistent storage for Prometheus, Grafana, and Loki

## 5. Project Structure

```text
Project-3-Observability/
├── app/
│   ├── Dockerfile
│   ├── server.js
│   ├── tracing.js
│   ├── package.json
│   └── package-lock.json
├── prometheus/
│   └── prometheus.yml
├── grafana/
│   ├── dashboards/
│   │   └── cloudops-dashboard.json
│   └── provisioning/
│       ├── dashboards/
│       │   └── dashboards.yml
│       └── datasources/
│           ├── prometheus.yml
│           └── loki.yml
├── loki/
│   └── loki-config.yml
├── alloy/
│   └── config.alloy
├── otel/
│   └── otel-collector.yml
├── screenshots/
│   ├── grafana-dashboard.png
│   └── jaeger-traces.png
├── .env.example
├── .gitignore
├── docker-compose.yml
└── README.md
```

## 6. Prerequisites

- Docker Desktop
- Docker Compose
- Git

Node.js does not need to be installed on the host because the application runs inside a Docker container.

## 7. Installation and Deployment

### Clone the repository

```bash
git clone https://github.com/Tusharjb/devops-complete-observability.git
cd devops-complete-observability
```

### Configure the environment

Create a `.env` file from `.env.example`.

For Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set your own Grafana administrator password.

### Start the application

```bash
docker compose up -d --build
```

### Verify running containers

```bash
docker compose ps
```

The following containers should be running:

- cloudops-app
- cloudops-prometheus
- cloudops-grafana
- cloudops-loki
- cloudops-alloy
- cloudops-otel-collector
- cloudops-jaeger

## 8. Access the Services

| Service | Local URL |
|---|---|
| Node.js Application | http://localhost:3000 |
| Application Health | http://localhost:3000/health |
| Application Metrics | http://localhost:3000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3002 |
| Loki API | http://localhost:3100 |
| Jaeger | http://localhost:16686 |

Grafana username: `admin`

Grafana password: The password configured in `.env`.

## 9. Monitoring Dashboard

Grafana automatically loads the **CloudOps | Application Observability** dashboard.

The dashboard contains six monitoring panels:

1. Application Availability
2. HTTP Requests per Second
3. HTTP 5xx Error Rate
4. Average Response Time
5. Node.js CPU Usage
6. Node.js Memory Usage

### Dashboard Screenshot

![Grafana Monitoring Dashboard](screenshots/grafana-dashboard.png)

## 10. Centralized Logging

Grafana Alloy collects the Node.js application's Docker logs and forwards them to Loki.

Application logs are structured in JSON format.

To explore logs:

1. Open Grafana.
2. Navigate to Explore.
3. Select the Loki data source.
4. Execute the following LogQL query:

```logql
{job="cloudops-app"}
```

To filter demo API requests:

```logql
{job="cloudops-app"} |= "/api/demo"
```
### Loki Centralized Logging Screenshot

![Loki Centralized Application Logs](screenshots/loki-logs.png)

## 11. Distributed Tracing

The application uses OpenTelemetry automatic instrumentation to generate traces for HTTP requests.

Traces are exported through the OpenTelemetry Collector to Jaeger.

To view traces:

1. Open Jaeger.
2. Select the `cloudops-app` service.
3. Choose a suitable time range.
4. Click Find Traces.
5. Open a trace to inspect its spans and duration.

### Jaeger Screenshot

![Jaeger Distributed Tracing](screenshots/jaeger-traces.png)

## 12. Testing and Verification

### Application health

```powershell
Invoke-RestMethod http://localhost:3000/health
```

Expected status: `UP`.

### Generate successful requests

```powershell
1..20 | ForEach-Object { Invoke-RestMethod http://localhost:3000/api/demo | Out-Null }
```

### Generate intentional HTTP 500 errors

```powershell
1..10 | ForEach-Object { try { Invoke-RestMethod http://localhost:3000/api/error | Out-Null } catch {} }
```

### Verify Prometheus

Execute:

```promql
up{job="cloudops-app"}
```

Expected result: `1`.

### Verify Loki

Execute:

```logql
{job="cloudops-app"}
```

Expected result: Application logs.

### Verify Jaeger

Search for the `cloudops-app` service and inspect recorded HTTP request traces.

## 13. Stop the Environment

```bash
docker compose down
```

This stops and removes project containers while preserving named data volumes.

To start again:

```bash
docker compose up -d
```

## 14. Security Considerations

- Local credentials are stored in `.env`, which is excluded from Git.
- `.env.example` provides a safe configuration template.
- Grafana user registration is disabled.
- Loki and Jaeger interfaces are bound to the local host.
- The Docker socket is mounted read-only for Alloy; Docker socket access remains privileged and is intended only for this trusted local development environment.
- This configuration is intended for learning and local demonstrations, not direct production deployment.

## 15. Project Status

**Implementation completed and verified locally.**

- Metrics: Completed
- Grafana dashboard: Completed
- Centralized logging: Completed
- Distributed tracing: Completed
- Docker Compose integration: Completed
- GitHub documentation and final submission: In progress

## 16. Author

**Tusharjb**

DevOps Internship — Elevate Labs

GitHub: https://github.com/Tusharjb