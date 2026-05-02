-- ============================================================================
-- ClickHouse: logs table
-- ============================================================================
-- Engine  : MergeTree
-- Partition: by day  → efficient TTL merges & data management
-- Order   : (service, level, toStartOfMinute(timestamp), trace_id)
--           → fast filters by service/level + time range + trace lookups
-- TTL     : app=14d | error=30d | audit=60d (row-level, per log_type)
-- Codecs  : Delta+ZSTD on timestamp, ZSTD on strings → ~4-6x compression
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
    extra         String                  DEFAULT ''    CODEC(ZSTD(1))   -- arbitrary JSON context
)
ENGINE = MergeTree
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (service, level, toStartOfMinute(timestamp), trace_id)
TTL
    toDateTime(timestamp) + INTERVAL 14 DAY DELETE WHERE log_type = 'app',
    toDateTime(timestamp) + INTERVAL 30 DAY DELETE WHERE log_type = 'error',
    toDateTime(timestamp) + INTERVAL 60 DAY DELETE WHERE log_type = 'audit'
SETTINGS
    index_granularity = 8192;
