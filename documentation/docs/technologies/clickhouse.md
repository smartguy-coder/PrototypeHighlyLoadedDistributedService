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

    http_method   LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    http_path     String                  DEFAULT ''    CODEC(ZSTD(1)),
    http_status   UInt16                  DEFAULT 0,

    task_id       String                  DEFAULT ''    CODEC(ZSTD(1)),

    duration_ms   UInt32                  DEFAULT 0,

    message       String                  DEFAULT ''    CODEC(ZSTD(1)),
    exception     String                  DEFAULT ''    CODEC(ZSTD(1)),
    extra         String                  DEFAULT ''    CODEC(ZSTD(1)),

    INDEX idx_trace_id    trace_id    TYPE bloom_filter(0.01)        GRANULARITY 4,
    INDEX idx_request_id  request_id  TYPE bloom_filter(0.01)        GRANULARITY 4,
    INDEX idx_task_id     task_id     TYPE bloom_filter(0.01)        GRANULARITY 4,
    INDEX idx_user_id     user_id     TYPE bloom_filter(0.01)        GRANULARITY 4,
    INDEX idx_http_status http_status TYPE set(20)                   GRANULARITY 4,
    INDEX idx_message     message     TYPE tokenbf_v1(32768, 3, 0)   GRANULARITY 4,
    INDEX idx_http_path   http_path   TYPE tokenbf_v1(8192, 3, 0)    GRANULARITY 4
)
ENGINE = MergeTree
PARTITION BY (toYYYYMMDD(timestamp), log_type)
ORDER BY (service, level, toStartOfMinute(timestamp), trace_id)
TTL
    toDateTime(timestamp) + INTERVAL 14 DAY DELETE WHERE log_type = 'app',
    toDateTime(timestamp) + INTERVAL 30 DAY DELETE WHERE log_type = 'error',
    toDateTime(timestamp) + INTERVAL 60 DAY DELETE WHERE log_type = 'audit'
SETTINGS
    index_granularity = 8192,
    ttl_only_drop_parts = 1;
```

### How services produce records that fit this schema

Every field above corresponds to a key emitted by the JSON formatter on the
application side. Rather than duplicating the formatter, filter, and field
defaults across every service, that wiring lives in the shared utility
package [`prototype-highly-loaded-distributed-service-utils`](../technologies/pypi-publishing.md):

- `ClickHouseFieldsFilter` — a `logging.Filter` that injects defaults for
  every column on every `LogRecord`, renames `levelname` → `level` and
  `name` → `logger` to match column names, and serialises `exc_info` into
  the `exception` column. Because it runs as a handler-level filter, the
  schema invariant holds for any logger in the process — framework code,
  third-party libraries, and ad-hoc `logging.getLogger("x")` calls all
  produce records that map 1:1 onto the table above.
- `build_logging_config(service_name, environment, host, log_level, extra_loggers)` —
  a factory that returns a `logging.config.dictConfig`-compatible dict.
  Each service supplies its own identity and a small set of per-logger
  overrides (`django` / `celery` for `storefront_catalog_service`,
  `faststream` / `uvicorn` for `notification_service`); everything else
  — formatter, filter, console handler, JSON format string — is identical
  by construction.

This means the schema in this file and the application side cannot drift:
adding a new column requires changes in exactly two places (the `CREATE
TABLE` above and the format string in the utility), not one per service.
It also means a new service joins the pipeline by importing
`build_logging_config(...)` and adding the `logging=vector` Docker label
— nothing more.

---

### Design Decisions

**`LowCardinality(String)`** — For fields with few unique values (`level`, `service`, `environment`, `log_type`, `host`, `logger`, `http_method`), ClickHouse stores a dictionary internally. This reduces storage by 3–5x and speeds up `GROUP BY` and `WHERE` filters on these columns significantly.

**`CODEC(Delta(8), ZSTD(1))` on `timestamp`** — The Delta codec stores differences between consecutive values rather than absolute values. Since timestamps are monotonically increasing, differences are small integers, and ZSTD compresses them extremely well. Achieves ~6x compression.

**`CODEC(ZSTD(1))` on strings** — Zstandard compression level 1 provides a good balance between compression ratio (~3–4x) and CPU overhead.

**`DateTime64(3)`** — Millisecond precision. Python's `logging` module provides millisecond timestamps via `%(asctime)s`, so sub-second accuracy is preserved.

**`PARTITION BY (toYYYYMMDD(timestamp), log_type)`** — Composite partition key: one part per day per log_type bucket. The day component aligns with daily TTL boundaries; the `log_type` component makes parts homogeneous so each part holds rows from a single retention tier (`app`, `error`, or `audit`). That homogeneity is what unlocks the cheap whole-part TTL drops below.

**`ORDER BY (service, level, toStartOfMinute(timestamp), trace_id)`** — The primary key determines the sort order on disk. Queries filtered by `service` and `level` skip irrelevant data blocks entirely. `toStartOfMinute` groups similar timestamps to improve compression of adjacent rows.

**Skip indexes** — Secondary data-skipping indexes complement the primary key by accelerating queries that don't filter on the leading `ORDER BY` columns. One skip-index granule covers `GRANULARITY × index_granularity` rows (here 4 × 8192 = 32 768), and ClickHouse uses them to discard entire ranges before reading data.

| Index | Type | Purpose |
|---|---|---|
| `idx_trace_id`, `idx_request_id`, `idx_task_id`, `idx_user_id` | `bloom_filter(0.01)` | Point lookups (`WHERE trace_id = '…'`) without needing the leading `service`/`level` columns. 1% false-positive rate. |
| `idx_http_status` | `set(20)` | Small enumerable value set (200, 301, 404, 500…). Cheaper and exact compared to bloom. |
| `idx_message`, `idx_http_path` | `tokenbf_v1` | Token / substring search (`WHERE message LIKE '%timeout%'`). Splits text on non-alphanumeric chars and stores token bloom filters. |

**Whole-part TTL drops (`ttl_only_drop_parts = 1`)** — With one `log_type` per part, the conditional TTL above (`DELETE WHERE log_type = 'app'`) is satisfied either by every row in a part or by none of them. ClickHouse can therefore drop the entire part in one filesystem operation when its rows expire, instead of running a row-level merge that rewrites the part minus the deleted rows. On high-volume tables this turns TTL maintenance from an ongoing CPU/I-O cost into a near-free directory unlink.

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
-- Note: `idx_trace_id` (bloom_filter) makes this fast even without
-- knowing the service/level/timestamp window upfront.
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
