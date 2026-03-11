# Tech Stack

Overview of current and planned technologies used in the project.

---

## Current Stack

Technologies already implemented and in use.

| Category | Technology | Status |
|----------|------------|--------|
| **Documentation** | MkDocs + Material | ✅ Active |
| **Containerization** | Docker, Docker Compose | ✅ Active |
| **Frontend** | React 19, TypeScript, Vite | ✅ v0.1.0 |
| **UI Library** | Material UI 7 | ✅ v0.1.0 |
| **Backend** | Django 5, DRF | ✅ v0.1.0 |
| **Database** | PostgreSQL 15 | ✅ Active |

---

## Planned Stack

Technologies planned for future implementation.

### Backend & APIs

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Django** | Main monolith backend | 🔴 High |
| **FastAPI** | High-performance microservices | 🔴 High |
| **Django REST Framework** | REST API for Django | 🔴 High |
| **django-ninja** | Fast API alternative for Django | 🟡 Medium |
| **gRPC** | Inter-service communication | 🟡 Medium |

### Databases & Storage

| Technology | Purpose | Priority |
|------------|---------|----------|
| **PostgreSQL** | Primary relational database | 🔴 High |
| **PostgreSQL + PostGIS** | Geospatial data (tracking) | 🔴 High |
| **Redis** | Caching, sessions, pub/sub | 🔴 High |
| **MongoDB** | Document storage (logs, analytics) | 🟡 Medium |
| **ClickHouse** | Analytics, time-series data | 🟡 Medium |
| **Elasticsearch** | Full-text search, logging | 🟡 Medium |
| **Cassandra** | High-write workloads | 🟢 Low |
| **CockroachDB** | Distributed SQL (evaluation) | 🟢 Low |
| **S3** | File storage (images, documents) | 🔴 High |

### Message Brokers & Streaming

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Apache Kafka** | Event streaming, async communication | 🔴 High |
| **RabbitMQ** | Task queues, simple messaging | 🟡 Medium |
| **FastStream** | Kafka/RabbitMQ framework | 🟡 Medium |

### Task Queues & Workflows

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Temporal.io** | Workflow orchestration | 🔴 High |
| **Celery** | Background tasks | 🟡 Medium |
| **Celery Beat** | Scheduled tasks | 🟡 Medium |
| **TaskIQ** | Modern async task queue | 🟢 Low |

### Frontend & Mobile

| Technology | Purpose | Priority |
|------------|---------|----------|
| **React** | Customer web app | ✅ Done |
| **Flutter** | Mobile apps (iOS, Android) | 🔴 High |
| **WebSockets** | Real-time updates | 🔴 High |

### ORMs & Database Tools

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Django ORM** | Django models | ✅ Done |
| **SQLAlchemy** | FastAPI services | 🔴 High |
| **Tortoise ORM** | Async ORM option | 🟢 Low |
| **PgBouncer** | Connection pooling | 🔴 High |
| **SQLAdmin** | Admin interface for FastAPI | 🟡 Medium |

### Infrastructure & DevOps

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Docker** | Containerization | ✅ Done |
| **Kubernetes** | Container orchestration | 🔴 High |
| **Docker Swarm** | Simple orchestration (alternative) | 🟢 Low |
| **Nginx** | Reverse proxy, load balancer | 🔴 High |
| **Cloudflare** | CDN, DDoS protection | 🟡 Medium |

### Monitoring & Observability

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Prometheus** | Metrics collection | 🔴 High |
| **Grafana** | Dashboards, visualization | 🔴 High |
| **Sentry** | Error tracking | 🔴 High |
| **ELK Stack** | Centralized logging | 🟡 Medium |

### Authentication & Security

| Technology | Purpose | Priority |
|------------|---------|----------|
| **JWT** | Token authentication | 🔴 High |
| **Keycloak** | Identity management (evaluation) | 🟢 Low |
| **Django Tenants** | Multi-tenancy | 🟡 Medium |

### Payments

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Monobank API** | Ukrainian payments | 🔴 High |
| **Stripe** | International payments | 🔴 High |
| **Multi-currency** | Currency conversion | 🟡 Medium |

### Development Tools

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Pre-commit** | Git hooks, code quality | 🔴 High |
| **Ruff** | Python linting | 🔴 High |
| **ESLint** | JavaScript/TypeScript linting | ✅ Done |
| **pytest** | Python testing | 🔴 High |
| **GitHub Actions** | CI/CD pipelines | 🔴 High |

### Experimental / Evaluation

| Technology | Purpose | Status |
|------------|---------|--------|
| **[Databasus](https://github.com/databasus/databasus)** | Database management | 🔍 Evaluating |
| **[Kanchi](https://github.com/getkanchi/kanchi)** | Unknown | 🔍 Evaluating |
| **Video Streaming** | Live video (support chat?) | 🔍 Evaluating |

---

## Architecture Decisions

### Why Django + FastAPI?

| Aspect | Django | FastAPI |
|--------|--------|---------|
| **Use case** | Admin, CRUD, Auth | High-performance APIs |
| **ORM** | Built-in, mature | SQLAlchemy/Tortoise |
| **Async** | Limited | Native |
| **Admin panel** | Excellent | SQLAdmin |
| **Ecosystem** | Huge | Growing |

**Decision:** Use Django for the main monolith (admin, user management) and FastAPI for microservices requiring high performance.

### Why Temporal.io?

- **Durability** — Workflows survive process restarts
- **Visibility** — Full audit trail
- **Reliability** — Built-in retries
- **Language support** — Python, Go, TypeScript

### Why Kafka over RabbitMQ?

| Aspect | Kafka | RabbitMQ |
|--------|-------|----------|
| **Throughput** | Very high | Moderate |
| **Message retention** | Configurable | Until consumed |
| **Replay** | Yes | No |
| **Use case** | Event streaming | Task queues |

**Decision:** Kafka for event streaming between services, RabbitMQ for simple task queues where needed.

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| 🔴 High | Critical for MVP |
| 🟡 Medium | Important but can wait |
| 🟢 Low | Nice to have |
| 🔍 Evaluating | Under consideration |
| ✅ Done | Already implemented |

---

## Related Documentation

- [Project Overview](overview.md)
- [Architecture Diagrams](diagrams.md)
