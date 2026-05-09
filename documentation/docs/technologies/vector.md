# Vector

## What Is Vector?

Vector is an open-source, high-performance **observability data pipeline** built by Datadog (previously Timber.io). It collects, transforms, and routes logs, metrics, and traces between sources and destinations with minimal resource overhead.

Vector is written in Rust, which gives it:

- Near-zero CPU overhead at idle
- Throughput of millions of events per second on modest hardware
- Memory safety without a garbage collector (no GC pauses)
- A tiny container footprint (`distroless-libc` image is ~50MB)

---

## Role in This Project

Vector is the **log shipper** that bridges application containers and ClickHouse:

```
┌─────────────────────────────────────────┐
│         Docker Host                     │
│                                         │
│  ┌──────────────┐   ┌────────────────┐  │
│  │ Django app   │   │ Celery worker  │  │
│  │ stdout (JSON)│   │ stdout (JSON)  │  │
│  └──────┬───────┘   └───────┬────────┘  │
│         │ Docker logging    │           │
│         ▼ driver            ▼           │
│  ┌─────────────────────────────────┐    │
│  │      /var/run/docker.sock       │    │
│  └──────────────┬──────────────────┘    │
│                 │ docker_logs source    │
│                 ▼                       │
│         ┌──────────────┐                │
│         │    Vector    │                │
│         │  transforms  │                │
│         │  (VRL remap) │                │
│         └──────┬───────┘                │
│                │ clickhouse sink        │
│                ▼                        │
│         ┌──────────────┐                │
│         │  ClickHouse  │                │
│         │    :8123     │                │
│         └──────────────┘                │
└─────────────────────────────────────────┘
```

Vector reads every log line written to stdout by any Docker container, applies a VRL transform to parse and validate the JSON structure, then inserts valid records into ClickHouse via the HTTP interface.

---

## Configuration Breakdown

### Source: `docker_logs`

```toml
[sources.docker_logs]
type = "docker_logs"
include_labels = ["logging=vector"]
```

Vector connects to `/var/run/docker.sock` and subscribes to the Docker log stream. This is equivalent to `docker logs -f <container>` for all containers simultaneously, but with structured metadata (container name, image, stream type).

**Container selection via labels.** Without a filter, Vector would tail every container on the host — Kafka brokers, Postgres, RabbitMQ, UIs, ClickHouse itself, even Vector — and the VRL transform would discard most of it after parsing. That wastes CPU and creates a self-logging cycle (Vector → ClickHouse → ClickHouse logs → Vector). The `include_labels` filter pushes the decision down to the Docker API: only containers carrying the `logging=vector` label are subscribed to in the first place.

In `docker-compose.yml`, the four application services opt in:

```yaml
storefront_catalog_service:
  labels:
    logging: vector
celery_worker:
  labels:
    logging: vector
celery_beat:
  labels:
    logging: vector
notification_service:
  labels:
    logging: vector
```

New services join the pipeline by adding the same label — no changes to `vector.toml` required. This is the same convention used by Fluent Bit's `kubernetes.io/log` annotation and by Loki's Promtail label discovery.

### Structured logging in the application: `python-json-logger`

The filter on the source side only works because every application service produces JSON on stdout in a consistent shape. That shape comes from the [`python-json-logger`](https://pypi.org/project/python-json-logger/) package, wired into each service's `logging` configuration as the formatter:

```python
# pseudo-code from each service's logging setup
from pythonjsonlogger.json import JsonFormatter

formatter = JsonFormatter(
    "%(asctime)s %(name)s %(levelname)s %(message)s",
    rename_fields={"levelname": "level", "name": "logger"},
)
```

Key reasons for this choice:

- **`asctime` is the marker field.** The VRL transform uses `if !exists(parsed.asctime) { abort }` as a sanity check that a JSON line actually came from our logger and not from some library that happens to print `{...}` (FastAPI startup, rdkafka diagnostics, etc.).
- **Stable schema.** The formatter is configured to always emit the same top-level keys (`environment`, `service`, `host`, `level`, `log_type`, `trace_id`, ...), which lets Vector's transform rebuild the event with `. = {...}` and pass it to ClickHouse without `400 Bad Request` from unknown columns.
- **Single dependency.** `python-json-logger` is a ~200-line library with no transitive dependencies. It is the de-facto standard for JSON logging in Python and is what Datadog, Sentry, and most observability vendors document for their Python SDKs.

### Transform: `remap` (VRL)

```toml
[transforms.parse_json]
type = "remap"
inputs = ["docker_logs"]
source = '''
# Drop non-JSON lines silently (rdkafka noise, plain text)
parsed, err = parse_json(.message)
if err != null || !is_object(parsed) {
    abort
}

# Drop lines without asctime — not from our structured logger
if !exists(parsed.asctime) {
    abort
}

# Python asctime uses comma before ms: "2026-05-01 15:26:35,852"
asctime_fixed = replace(string!(parsed.asctime), ",", ".")
ts, err = parse_timestamp(asctime_fixed, "%Y-%m-%d %H:%M:%S%.3f")
if err != null {
    ts, err = parse_timestamp(asctime_fixed, "%Y-%m-%d %H:%M:%S")
    if err != null { abort }
}

# Rebuild event with ONLY schema fields
# Extra fields cause ClickHouse HTTP 400 Bad Request
. = {
    "timestamp":   format_timestamp!(ts, "%Y-%m-%d %H:%M:%S%.3f"),
    "environment": string(parsed.environment) ?? "production",
    ...
}
'''
```

The transform uses **VRL (Vector Remap Language)** — a purpose-built expression language for log transformation. Key decisions:

- **`abort` on non-JSON** — silently drops rdkafka noise, Postgres startup messages, RabbitMQ plain text, etc.
- **`abort` without `asctime`** — only records from `python-json-logger` carry this field; it acts as a filter for our structured logs.
- **Explicit object reconstruction** — `". = {...}"` replaces the entire event with only the 15 fields in the ClickHouse schema. Without this, Vector includes Docker metadata (`container_id`, `stream`, `source_type`) which causes ClickHouse to return `400 Bad Request`.
- **Comma → dot in asctime** — Python's `logging.Formatter` outputs `"2026-05-01 15:26:35,852"` (locale-style comma separator before milliseconds). VRL's `parse_timestamp` requires a dot: `"2026-05-01 15:26:35.852"`.

### Sink: `console_debug` (optional, debug-only)

```toml
[sinks.console_debug]
type = "console"
inputs = ["parse_json"]
encoding.codec = "json"
```

A second sink that prints every transformed event to Vector's own stdout, visible via `docker logs vector`. Its purpose is purely diagnostic: when iterating on the VRL transform or the ClickHouse schema, it lets you see the **exact JSON payload** that would be sent to ClickHouse before the HTTP request happens. The ClickHouse sink doesn't echo failed payloads in its error messages — a `400 Bad Request` on an unknown field tells you the column name but not the row — so without `console_debug` you'd be reverse-engineering the transform from error logs.

The sink reads from the same `parse_json` transform as the ClickHouse sink, so what you see in `docker logs vector` is byte-for-byte what ClickHouse receives.

**Why it doesn't cause a feedback loop.** A naive concern: Vector writes to its own stdout, Docker captures stdout, Vector reads Docker logs — isn't that an infinite cycle? It would be, except `include_labels = ["logging=vector"]` on the source filters out the `vector` container itself (which has no such label). The debug output stays in `docker logs vector` and never re-enters the pipeline.

**When to remove it.** Once the pipeline is stable and you're confident in the schema, comment out or delete this sink. It adds a small amount of CPU overhead (every event is JSON-encoded twice — once for ClickHouse, once for stdout) and clutters `docker logs vector` with operational events that you'd otherwise query directly from ClickHouse.

### Sink: `clickhouse`

```toml
[sinks.clickhouse]
type = "clickhouse"
inputs = ["parse_json"]
endpoint = "http://clickhouse:8123"
database = "default"
table = "logs"
skip_unknown_fields = true

[sinks.clickhouse.auth]
strategy = "basic"
user = "${CLICKHOUSE_USER}"
password = "${CLICKHOUSE_PASSWORD}"
```

Vector batches events and sends them as `INSERT INTO logs FORMAT JSONEachRow` over HTTP. `skip_unknown_fields = true` passes `input_format_skip_unknown_fields=1` to ClickHouse as a query parameter — a safety net that prevents `400` errors if any unexpected field slips through the transform.

Authentication uses HTTP Basic Auth via the `auth` block. Credentials are injected from environment variables at runtime.

---

## VRL — Vector Remap Language

VRL is a domain-specific language designed for log transformation. It is:

- **Statically typed** — type errors are caught at configuration load time, not at runtime
- **Fail-safe** — every function that can fail returns a `result, err` tuple; unhandled errors cause a compile-time warning
- **Sandboxed** — no network access, no filesystem access, no infinite loops possible
- **Fast** — compiles to native code; throughput is typically 1–10M events/second

The `!` suffix (e.g., `parse_json!`) is shorthand for "abort the entire event if this fails" instead of the `result, err` pattern.

---

## Image Choice: `nightly-distroless-libc`

| Image | Size | Shell | Use Case |
|---|---|---|---|
| `latest-debian` | ~200MB | Yes | Development, debugging |
| `latest-alpine` | ~80MB | sh only | General purpose |
| `nightly-distroless-libc` | ~50MB | None | Production, minimal attack surface |

`distroless` images contain only the Vector binary and its glibc dependency — no shell, no package manager, no system utilities. This reduces:

- **Attack surface** — no shell means no RCE via shell injection
- **Image size** — faster pull and startup in autoscaling scenarios
- **Vulnerability surface** — fewer OS packages to patch

The `nightly` tag provides the latest Vector version (0.56.0+ in this project), which includes the most recent VRL functions and ClickHouse sink features.

---

## Where This Stack Is Used in Production

Vector is the log shipper of choice at companies that need high-throughput, low-overhead log collection:

| Company | Use Case |
|---|---|
| **Datadog** | Vector is their internal log pipeline (they acquired Timber.io) |
| **Shopify** | Ships logs from 10,000+ containers to ClickHouse and S3 |
| **Discord** | Processes billions of events/day for observability |
| **T-Mobile** | Centralised log collection across Kubernetes clusters |
| **Fastly** | Edge CDN log streaming at global scale |

The pattern in this project — `Docker logs → Vector → ClickHouse` — is the standard production setup for self-hosted log analytics. In Kubernetes environments, Vector typically runs as a `DaemonSet` (one pod per node), collecting logs from all pods on that node via the node's `/var/log/pods/` directory instead of the Docker socket.
