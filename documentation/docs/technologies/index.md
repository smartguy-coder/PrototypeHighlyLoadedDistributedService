# Technologies

Deep-dive documentation for technologies implemented in this project.

Each guide provides theory, practical implementation details, and best practices.

---

## Implemented Technologies

| Technology | Category | Documentation |
|------------|----------|---------------|
| [Apache Kafka](kafka.md) | Message Broker | Event streaming for async communication |
| [Celery & Django Celery Beat](celery.md) | Task Queue | Background jobs, periodic tasks, canvas workflows |
| [PgBouncer](pgbouncer.md) | Connection Pooling | Multiplexing PostgreSQL connections for high concurrency |
| [PostgreSQL Dump & Restore](postgres-dump-restore.md) | Database Operations | Loading databasus dumps + how production handles backups at scale |
| [FastStream](faststream.md) | Message Consumer Framework | Async message handling with Kafka, RabbitMQ, NATS, Redis |
| [PyPI Publishing](pypi-publishing.md) | Package Distribution | Shared utilities across microservices |

---

## Related Documentation

- [Tech Stack Overview](../about/tech-stack.md)
- [Architecture Diagrams](../about/diagrams.md)
- [Quick Start Guide](../guides/quickstart.md)
