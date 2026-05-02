# ClickHouse

## What Is ClickHouse?

ClickHouse is an open-source **column-oriented OLAP database** designed for real-time analytical queries on large volumes of data. It was originally built by Yandex (2016) to power their web analytics platform and is now maintained by ClickHouse Inc.

Unlike row-oriented databases (PostgreSQL, MySQL) that store each row together, ClickHouse stores each column separately. This makes it extremely efficient for aggregation queries like `COUNT`, `SUM`, `AVG`, `GROUP BY` because it reads only the columns involved in the query rather than scanning entire rows.

---

## Why Not PostgreSQL for Logs?

| Feature | PostgreSQL | ClickHouse |
|---|---|---|
| Storage model | Row-oriented | Column-oriented |
| INSERT throughput | ~50K rows/s | ~1M+ rows/s |
| SELECT on 1B rows | Minutes | Milliseconds |
| Compression ratio | 1x | 5–10x (column codecs) |
| TTL / data expiry | Manual partitioning | Native TTL per row |
| Best for | Transactional workloads | Analytical / log workloads |

Storing application logs in PostgreSQL would create index bloat, slow `VACUUM` cycles, and high disk usage. ClickHouse is purpose-built for this pattern.

---

## Role in This Project

ClickHouse serves as the **central log storage** for all application events:

```
Django / Celery / Notification Service
        │ stdout (JSON)
        ▼
    Docker runtime
        │ /var/run/docker.sock
        ▼
      Vector
        │ HTTP POST /  (INSERT INTO logs FORMAT JSONEachRow)
        ▼
    ClickHouse :8123
        │
        ▼
    Grafana (dashboards & alerts)
```

Every service writes structured JSON logs to stdout. Vector collects them via the Docker socket and inserts them into ClickHouse. Grafana queries ClickHouse for dashboards and alerting.

---

## Table Schema

```sql
CREATE TABLE IF NOT EXISTS default.logs
(
    timestamp     DateTime64(3)           CODEC(Delta(8), ZSTD(1)),

    environment   LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    service       LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    host          LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    level         LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    log_type      LowCardinality(String)  DEFAULT 'app' CODEC(ZSTD(1)),
    logger        LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),

    trace_id      String                  DEFAULT ''    CODEC(ZSTD(1)),
    span_id       String                  DEFAULT ''    CODEC(ZSTD(1)),

    user_id       Nullable(Int64),
    request_id    String                  DEFAULT ''    CODEC(ZSTD(1)),

    message       String                  DEFAULT ''    CODEC(ZSTD(1)),
    exception     String                  DEFAULT ''    CODEC(ZSTD(1)),
    extra         String                  DEFAULT ''    CODEC(ZSTD(1))
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (service, level, toStartOfMinute(timestamp), trace_id)
TTL
    toDateTime(timestamp) + INTERVAL 14 DAY DELETE WHERE log_type = 'app',
    toDateTime(timestamp) + INTERVAL 30 DAY DELETE WHERE log_type = 'error',
    toDateTime(timestamp) + INTERVAL 60 DAY DELETE WHERE log_type = 'audit'
SETTINGS index_granularity = 8192;
```

### Design Decisions

**`LowCardinality(String)`** — For fields with few unique values (`level`, `service`, `environment`, `log_type`), ClickHouse stores a dictionary internally. This reduces storage by 3–5x and speeds up `GROUP BY` and `WHERE` filters on these columns significantly.

**`CODEC(Delta(8), ZSTD(1))` on `timestamp`** — The Delta codec stores differences between consecutive values rather than absolute values. Since timestamps are monotonically increasing, differences are small integers, and ZSTD compresses them extremely well. Achieves ~6x compression.

**`CODEC(ZSTD(1))` on strings** — Zstandard compression level 1 provides a good balance between compression ratio (~3–4x) and CPU overhead.

**`DateTime64(3)`** — Millisecond precision. Python's `logging` module provides millisecond timestamps via `%(asctime)s`, so sub-second accuracy is preserved.

**`PARTITION BY toYYYYMMDD(timestamp)`** — Daily partitions align with the TTL rules. ClickHouse drops entire partitions rather than scanning rows, making TTL expiry nearly free.

**`ORDER BY (service, level, toStartOfMinute(timestamp), trace_id)`** — The primary key determines the sort order on disk. Queries filtered by `service` and `level` skip irrelevant data blocks entirely. `toStartOfMinute` groups similar timestamps to improve compression of adjacent rows.

**TTL per `log_type`** — Three retention tiers:
- `app` — 14 days (routine operational logs)
- `error` — 30 days (errors, for post-incident review)
- `audit` — 60 days (auth events, security-sensitive actions)

---

## Accessing ClickHouse

### HTTP Interface (port 8123)
Used by Vector, Grafana, and the Django management command.

```bash
# Quick query via curl
curl "http://localhost:8123/?user=default&password=clickhouse_secret" \
  --data "SELECT count() FROM default.logs"

# Format as table
curl "http://localhost:8123/?user=default&password=clickhouse_secret" \
  --data "SELECT level, count() FROM default.logs GROUP BY level FORMAT PrettyCompact"
```

### Native TCP (port 9000)
Used by DBeaver, clickhouse-client, and Python drivers.

```bash
# Interactive CLI inside the container
docker exec -it clickhouse clickhouse-client \
  --user default --password clickhouse_secret

# One-off query
docker exec -it clickhouse clickhouse-client \
  --user default --password clickhouse_secret \
  --query "SELECT * FROM default.logs ORDER BY timestamp DESC LIMIT 10"
```

### Django Management Command
```bash
# Statistics for last 24h
python manage.py clickhouse_logs_stats

# Custom window + write test
python manage.py clickhouse_logs_stats --hours 48 --insert-test
```

---

## Useful Analytical Queries

```sql
-- Error rate by service (last hour)
SELECT
    service,
    countIf(level = 'ERROR') AS errors,
    count() AS total,
    round(countIf(level = 'ERROR') * 100.0 / count(), 2) AS error_pct
FROM default.logs
WHERE timestamp >= now() - INTERVAL 1 HOUR
GROUP BY service
ORDER BY error_pct DESC;

-- Top 10 most frequent errors (last 24h)
SELECT message, logger, count() AS n
FROM default.logs
WHERE level = 'ERROR'
  AND timestamp >= now() - INTERVAL 24 HOUR
GROUP BY message, logger
ORDER BY n DESC
LIMIT 10;

-- Trace reconstruction: all events for a given trace
SELECT timestamp, service, level, message, extra
FROM default.logs
WHERE trace_id = 'your-trace-id-here'
ORDER BY timestamp ASC;

-- Audit log: all auth events for a user
SELECT timestamp, service, message, extra
FROM default.logs
WHERE log_type = 'audit'
  AND JSONExtractString(extra, 'channel') != ''
ORDER BY timestamp DESC
LIMIT 50;
```

---

## Where This Stack Is Used in Production

ClickHouse is the log analytics backend at companies operating at massive scale:

| Company | Use Case | Scale |
|---|---|---|
| **Cloudflare** | DNS query logs, HTTP request analytics | Trillions of events/day |
| **Uber** | Marketplace analytics, driver/rider events | Billions of rows/day |
| **eBay** | User behaviour analytics, A/B testing | Petabytes of data |
| **Spotify** | Streaming analytics, recommendation metrics | Millions of events/s |
| **Contentsquare** | Session replay, UX heatmaps | 1PB+ data |
| **Bloomberg** | Financial data aggregation | Real-time market feeds |

The typical production pattern mirrors this project exactly: application logs → log shipper (Vector/Fluent Bit) → ClickHouse → Grafana. The difference is scale — production deployments use ClickHouse clusters with sharding and replication across multiple nodes.
