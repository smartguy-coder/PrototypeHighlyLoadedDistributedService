-- ============================================================================
-- ClickHouse: logs table
-- ============================================================================
-- Engine    : MergeTree
-- Partition : (day, log_type) → parts are homogeneous per log_type, so the
--             conditional TTL below can be enforced via cheap whole-part drops
--             (`ttl_only_drop_parts = 1`) instead of expensive row-level merges.
-- Order     : (service, level, toStartOfMinute(timestamp), trace_id)
--             → fast filters by service/level + time range + trace lookups
-- Skip idx  : bloom_filter on point-lookup columns (trace_id, request_id,
--             task_id, user_id), set on http_status, tokenbf_v1 on free-text
--             (message, http_path) for substring search
-- TTL       : app=14d | error=30d | audit=60d (per-log_type, dropped as parts)
-- Codecs    : Delta+ZSTD on timestamp, ZSTD on strings → ~4-6x compression
-- ============================================================================

CREATE TABLE IF NOT EXISTS default.logs
(
    -- ----------------------------------------------------------------
    -- Time (millisecond precision)
    -- ----------------------------------------------------------------
    timestamp     DateTime64(3)           CODEC(Delta(8), ZSTD(1)),

    -- ----------------------------------------------------------------
    -- Routing / low-cardinality fields (stored as dictionary → tiny)
    -- ----------------------------------------------------------------
    environment   LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    service       LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    host          LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    level         LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),
    log_type      LowCardinality(String)  DEFAULT 'app' CODEC(ZSTD(1)),
    logger        LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),

    -- ----------------------------------------------------------------
    -- Distributed tracing (OpenTelemetry-compatible)
    -- ----------------------------------------------------------------
    trace_id      String                  DEFAULT ''    CODEC(ZSTD(1)),
    span_id       String                  DEFAULT ''    CODEC(ZSTD(1)),

    -- ----------------------------------------------------------------
    -- Request identity
    -- ----------------------------------------------------------------
    user_id       Nullable(Int64),
    request_id    String                  DEFAULT ''    CODEC(ZSTD(1)),

    -- ----------------------------------------------------------------
    -- HTTP context
    -- (populate via Django middleware: RequestLoggingMiddleware)
    -- ----------------------------------------------------------------
    http_method   LowCardinality(String)  DEFAULT ''    CODEC(ZSTD(1)),  -- GET POST PUT PATCH DELETE
    http_path     String                  DEFAULT ''    CODEC(ZSTD(1)),  -- /api/v1/users/me
    http_status   UInt16                  DEFAULT 0,                     -- 200 400 500 …

    -- ----------------------------------------------------------------
    -- Celery context
    -- (populate via task logger: logger.info(..., extra={"task_id": self.request.id}))
    -- ----------------------------------------------------------------
    task_id       String                  DEFAULT ''    CODEC(ZSTD(1)),  -- Celery task UUID

    -- ----------------------------------------------------------------
    -- Performance
    -- ----------------------------------------------------------------
    duration_ms   UInt32                  DEFAULT 0,                     -- request / task duration

    -- ----------------------------------------------------------------
    -- Content
    -- ----------------------------------------------------------------
    message       String                  DEFAULT ''    CODEC(ZSTD(1)),
    exception     String                  DEFAULT ''    CODEC(ZSTD(1)),  -- stack trace / error detail
    extra         String                  DEFAULT ''    CODEC(ZSTD(1)),  -- arbitrary JSON context

    -- ----------------------------------------------------------------
    -- Skip indexes (data-skipping secondary indexes)
    --   bloom_filter(p) — point lookups on string/int (false-positive rate p)
    --   set(N)          — small enumerable values; cheaper than bloom
    --   tokenbf_v1      — substring/token search (LIKE '%foo%') on free text
    -- GRANULARITY 4 → 1 skip-index granule covers 4 × 8192 = 32 768 rows
    -- ----------------------------------------------------------------
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
    -- With one log_type per partition, expired parts can be dropped wholesale
    -- instead of merged row-by-row. Massively cheaper on high-volume tables.
    ttl_only_drop_parts = 1;
