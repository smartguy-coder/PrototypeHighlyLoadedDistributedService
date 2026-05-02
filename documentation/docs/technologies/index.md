# Technologies

Deep-dive documentation for technologies implemented in this project.

Each guide provides theory, practical implementation details, and best practices.

---

## Implemented Technologies

| Technology | Category | Documentation |
|------------|----------|---------------|
| [Apache Kafka](kafka.md) | Message Broker | Event streaming for async communication |
| [Celery & Django Celery Beat](celery.md) | Task Queue | Background jobs, periodic tasks, canvas workflows |
| [FastStream](faststream.md) | Message Consumer Framework | Async message handling with Kafka, RabbitMQ, NATS, Redis |
| [PgBouncer](pgbouncer.md) | Connection Pooler | PostgreSQL connection pooling for high-concurrency workloads |
| [PyPI Publishing](pypi-publishing.md) | Package Distribution | Shared utilities across microservices |
| [ClickHouse](clickhouse.md) | Log Storage | Column-oriented OLAP database for real-time log analytics |
| [Vector](vector.md) | Log Shipper | High-performance observability data pipeline |
| [Grafana](grafana.md) | Visualisation & Alerting | Dashboards and alerts on top of ClickHouse |

---

## Logging Stack

The three technologies above form an integrated observability pipeline:

```
Application (Django / Celery)
        │ stdout JSON
        ▼
      Vector           ← collects & transforms Docker logs
        │ HTTP INSERT
        ▼
    ClickHouse          ← stores & indexes log data
        │ SQL SELECT
        ▼
     Grafana            ← dashboards, alerts, exploration
```

See each technology page for configuration details, design decisions, and production usage patterns.

---

## Related Documentation

- [Tech Stack Overview](../about/tech-stack.md)
- [Architecture Diagrams](../about/diagrams.md)
- [Quick Start Guide](../guides/quickstart.md)
