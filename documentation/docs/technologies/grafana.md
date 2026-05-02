# Grafana

## What Is Grafana?

Grafana is an open-source **observability and data visualisation platform**. It connects to data sources (ClickHouse, Prometheus, PostgreSQL, Elasticsearch, and 150+ others) and provides interactive dashboards, alerting, and exploration tools — all without requiring any data to be moved or copied.

Grafana does not store metrics or logs itself. It queries the original data source on demand and renders the results as charts, tables, heatmaps, and alerts.

---

## Role in This Project

Grafana is the **visualisation and alerting layer** on top of ClickHouse:

```
ClickHouse (logs storage)
        │
        │  SQL queries on demand
        ▼
     Grafana
        │
        ├── Dashboards (error rates, service health, audit trails)
        ├── Alerts    (error spike → PagerDuty / Slack / email)
        └── Explore   (ad-hoc log search, trace inspection)
```

### Access

Grafana is available at [http://localhost:3000](http://localhost:3000) when the stack is running.

Default credentials: `admin` / `admin` (change on first login).

---

## Connecting Grafana to ClickHouse

Grafana queries ClickHouse via the **Grafana ClickHouse plugin** (by Grafana Labs). It uses the ClickHouse HTTP interface on port 8123.

### Plugin Installation

In Grafana UI: **Administration → Plugins → Search "ClickHouse" → Install**.

Or pre-install via environment variable in `docker-compose.yml`:

```yaml
grafana:
  image: grafana/grafana:latest
  environment:
    GF_INSTALL_PLUGINS: grafana-clickhouse-datasource
```

### Data Source Configuration

| Field | Value |
|---|---|
| Server address | `clickhouse` (Docker hostname) |
| Server port | `8123` |
| Protocol | HTTP |
| Database | `default` |
| Username | `default` |
| Password | `clickhouse_secret` |

---

## Example Dashboards

### Service Health Overview

```sql
-- Panel: Error rate per service (last 1h)
SELECT
    toStartOfMinute(timestamp) AS time,
    service,
    countIf(level = 'ERROR') AS errors
FROM default.logs
WHERE timestamp >= now() - INTERVAL 1 HOUR
GROUP BY time, service
ORDER BY time ASC
```

```sql
-- Panel: Log volume by level (time series)
SELECT
    toStartOfMinute(timestamp) AS time,
    level,
    count() AS count
FROM default.logs
WHERE timestamp >= $__timeFilter(timestamp)
GROUP BY time, level
ORDER BY time ASC
```

### Audit Trail

```sql
-- Panel: Auth events table
SELECT
    timestamp,
    host,
    message,
    JSONExtractString(extra, 'channel') AS channel,
    JSONExtractString(extra, 'task_id') AS task_id
FROM default.logs
WHERE log_type = 'audit'
  AND timestamp >= $__timeFilter(timestamp)
ORDER BY timestamp DESC
LIMIT 100
```

### Exception Explorer

```sql
-- Panel: Recent exceptions with stack traces
SELECT
    timestamp,
    service,
    logger,
    message,
    exception
FROM default.logs
WHERE exception != ''
  AND timestamp >= $__timeFilter(timestamp)
ORDER BY timestamp DESC
```

---

## Alerting

Grafana can fire alerts when ClickHouse query results cross a threshold.

**Example: Alert on error spike**

1. Create a panel with the query:
```sql
SELECT count() AS error_count
FROM default.logs
WHERE level = 'ERROR'
  AND timestamp >= now() - INTERVAL 5 MINUTE
```
2. Set alert condition: `error_count > 50`
3. Configure notification channel: Slack, PagerDuty, email, webhook

Grafana evaluates alert queries on a configurable interval (e.g., every 1 minute) and fires/resolves automatically.

---

## Grafana vs Kibana vs Datadog

| Feature | Grafana + ClickHouse | Kibana + Elasticsearch | Datadog |
|---|---|---|---|
| Self-hosted | ✅ | ✅ | ❌ (SaaS) |
| Storage cost | Very low (ClickHouse compression) | High (Elasticsearch is expensive at scale) | Per-GB pricing |
| Query language | SQL | KQL / Lucene | Proprietary |
| Metrics + Logs + Traces | ✅ | Partial | ✅ |
| Setup complexity | Medium | High | Low (agent-based) |
| Best for | OLAP + logs at scale | Full-text search, ELK ecosystem | Managed observability |

The Grafana + ClickHouse combination is chosen here because ClickHouse's SQL is familiar, storage costs are low due to compression, and the setup is entirely self-hosted with no per-seat or per-GB fees.

---

## Where This Stack Is Used in Production

The Grafana + ClickHouse pairing is a popular production observability stack:

| Company | Use Case |
|---|---|
| **GitLab** | GitLab.com uses Grafana for infrastructure dashboards across thousands of services |
| **CERN** | Physics experiment monitoring and alerting |
| **Grafana Labs itself** | Grafana Cloud observability built on their own platform |
| **Booking.com** | Operational dashboards for microservices at scale |
| **New York Times** | Content delivery and reader engagement metrics |

In production Kubernetes environments, Grafana typically runs as a `Deployment` with persistent storage for dashboard definitions, connected to ClickHouse clusters and Prometheus for metrics. Alerts route to PagerDuty or OpsGenie for on-call escalation.

---

## Full Logging Stack Interaction

The complete flow from log emission to dashboard:

```
1. Django/Celery logger.info("otp_request received", extra={...})
        │
        │ python-json-logger formats as JSON to stdout
        ▼
2. Docker captures stdout → available via /var/run/docker.sock
        │
        │ Vector reads via docker_logs source
        ▼
3. Vector VRL transform:
   - parse_json(.message)
   - validate asctime exists
   - convert timestamp format
   - rebuild event with schema fields only
        │
        │ HTTP POST INSERT INTO logs FORMAT JSONEachRow
        ▼
4. ClickHouse stores row in default.logs
   - MergeTree engine compresses and indexes
   - TTL runs asynchronously to drop old partitions
        │
        │ SQL SELECT on demand
        ▼
5. Grafana renders dashboard panel
   - Time series charts for error rates
   - Tables for audit trail
   - Alerts fire if thresholds exceeded
```
