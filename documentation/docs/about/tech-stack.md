# Tech Stack

Overview of current and planned technologies used in the project.

---

## Current Stack

Technologies already implemented and in use.

| Category | Technology | Status | Documentation |
|----------|------------|--------|---------------|
| **Documentation** | MkDocs + Material | ✅ Active | — |
| **Containerization** | Docker, Docker Compose | ✅ Active | — |
| **Frontend** | React 19, TypeScript, Vite | ✅ v0.1.0 | — |
| **UI Library** | Material UI 7 | ✅ v0.1.0 | — |
| **Backend** | Django 6, DRF | ✅ v0.1.0 | — |
| **Database** | PostgreSQL 18 | ✅ Active | — |
| **Message Broker** | Apache Kafka (3-broker cluster) | ✅ Active | [Kafka Guide](../technologies/kafka.md) |

---

## Planned Stack

Technologies planned for future implementation.

### Backend & APIs

| Technology | Purpose | Priority |
|------------|---------|----------|
| **FastAPI** | High-performance microservices | 🔴 High |
| **django-ninja** | Fast API alternative for Django | 🟡 Medium |
| **gRPC** | Inter-service communication | 🟡 Medium |

### Databases & Storage

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Redis** | Caching, sessions, pub/sub | 🔴 High |
| **MongoDB** | Document storage (logs, analytics) | 🟡 Medium |
| **ClickHouse** | Analytics, time-series data | 🟡 Medium |
| **Elasticsearch** | Full-text search, logging | 🟡 Medium |
| **S3** | File storage (images, documents) | 🔴 High |

### Message Brokers & Streaming

| Technology | Purpose | Priority |
|------------|---------|----------|
| **RabbitMQ** | Task queues, simple messaging | 🟡 Medium |
| **FastStream** | Kafka/RabbitMQ framework | 🟡 Medium |

### Task Queues & Workflows

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Temporal.io** | Workflow orchestration | 🔴 High |
| **Celery** | Background tasks | 🟡 Medium |
| **Celery Beat** | Scheduled tasks | 🟡 Medium |

### Frontend & Mobile

| Technology | Purpose | Priority |
|------------|---------|----------|
| **ReactNative** | Mobile apps (iOS, Android) | 🔴 High |
| **Flet** | Mobile apps (Android) | 🔴 High |
| **WebSockets** | Real-time updates | 🔴 High |

### ORMs & Database Tools

| Technology | Purpose | Priority |
|------------|---------|----------|
| **SQLAlchemy** | FastAPI services | 🔴 High |
| **PgBouncer** | Connection pooling | 🔴 High |
| **SQLAdmin** | Admin interface for FastAPI | 🟡 Medium |

### Infrastructure & DevOps

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Kubernetes** | Container orchestration | 🔴 High |
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
| **Django Tenants** | Multi-tenancy | 🟡 Medium |

### Payments

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Monobank API** | Ukrainian payments | 🔴 High |
| **Stripe** | International payments | 🔴 High |

### Development Tools

| Technology | Purpose | Priority |
|------------|---------|----------|
| **Pre-commit** | Git hooks, code quality | 🔴 High |
| **Ruff** | Python linting | 🔴 High |
| **pytest** | Python testing | 🔴 High |
| **GitHub Actions** | CI/CD pipelines | 🔴 High |

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

### Why Kafka over RabbitMQ?

| Aspect | Kafka | RabbitMQ |
|--------|-------|----------|
| **Throughput** | Very high | Moderate |
| **Message retention** | Configurable | Until consumed |
| **Replay** | Yes | No |
| **Use case** | Event streaming | Task queues |

**Decision:** Kafka for event streaming between services, RabbitMQ for simple task queues where needed.

See [Kafka documentation](../technologies/kafka.md) for implementation details.

---

## Priority Legend

| Priority | Meaning |
|----------|---------|
| 🔴 High | Critical for MVP |
| 🟡 Medium | Important but can wait |
| 🟢 Low | Nice to have |
| ✅ Done | Already implemented |

---

## Related Documentation

- [Project Overview](overview.md)
- [Architecture Diagrams](diagrams.md)
- [Technologies Deep-Dive](../technologies/index.md)
