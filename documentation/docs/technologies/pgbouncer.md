# PgBouncer

PgBouncer is a lightweight connection pooler for PostgreSQL that sits between your application and the database, managing and reusing connections to reduce overhead.

---

## Table of Contents

1. [Theory](#theory)
2. [Architecture](#architecture)
3. [Pool Modes](#pool-modes)
4. [Why PgBouncer in Kubernetes](#why-pgbouncer-in-kubernetes)
5. [Our Implementation](#our-implementation)
6. [Configuration](#configuration)
7. [Django Integration](#django-integration)
8. [Best Practices](#best-practices)

---

## Theory

### What is Connection Pooling?

Every time an application connects to PostgreSQL, the database creates a new **backend process**. This is expensive:

| Operation | Time | Memory |
|-----------|------|--------|
| TCP connection | ~1-5ms | — |
| SSL handshake | ~10-50ms | — |
| PostgreSQL fork | ~50-100ms | ~10MB per connection |
| Authentication | ~5-20ms | — |
| **Total** | **~70-175ms** | **~10MB** |

**Connection pooling** solves this by maintaining a pool of pre-established connections that can be reused.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Without Connection Pooling                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Request 1 ──► [Connect 100ms] ──► Query 5ms ──► [Close]       │
│   Request 2 ──► [Connect 100ms] ──► Query 5ms ──► [Close]       │
│   Request 3 ──► [Connect 100ms] ──► Query 5ms ──► [Close]       │
│                                                                 │
│   Total: 315ms (300ms overhead!)                                │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    With Connection Pooling                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   [Pool: 10 pre-connected]                                      │
│                                                                 │
│   Request 1 ──► [Get from pool] ──► Query 5ms ──► [Return]      │
│   Request 2 ──► [Get from pool] ──► Query 5ms ──► [Return]      │
│   Request 3 ──► [Get from pool] ──► Query 5ms ──► [Return]      │
│                                                                 │
│   Total: 15ms (20x faster!)                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### When to Use PgBouncer?

| Scenario | Need PgBouncer? | Why |
|----------|-----------------|-----|
| Single Django instance | ⚠️ Maybe | Django has `CONN_MAX_AGE` |
| Multiple Django instances | ✅ Yes | Connections multiply quickly |
| Kubernetes with autoscaling | ✅ Critical | Pods × workers × threads = explosion |
| Serverless (Cloud Run, Lambda) | ✅ Critical | Each invocation = new connection |
| High-traffic API | ✅ Yes | Reduce connection overhead |
| Low-traffic internal tool | ❌ No | Overhead not significant |

### PgBouncer vs Django CONN_MAX_AGE

| Aspect | Django `CONN_MAX_AGE` | PgBouncer |
|--------|----------------------|-----------|
| **Scope** | Per-process | Cluster-wide |
| **Connection reuse** | Within same worker | Across all apps |
| **Multiple instances** | Each has own pool | Shared pool |
| **Kubernetes scaling** | Connections multiply | Connections controlled |
| **Memory efficiency** | Lower | Higher |

```
┌─────────────────────────────────────────────────────────────────┐
│                    Django CONN_MAX_AGE Only                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Pod 1 (4 workers) ──► 4 connections ─┐                        │
│   Pod 2 (4 workers) ──► 4 connections ─┼──► PostgreSQL          │
│   Pod 3 (4 workers) ──► 4 connections ─┤    (12 connections)    │
│   ...                                  │                        │
│   Pod 10 (4 workers) ──► 4 connections─┘    (40 connections!)   │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                    With PgBouncer                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Pod 1 ──┐                                                     │
│   Pod 2 ──┼──► PgBouncer ──► PostgreSQL                         │
│   Pod 3 ──┤    (pool: 20)    (20 connections)                   │
│   ...     │                                                     │
│   Pod 10 ─┘                                                     │
│                                                                 │
│   200 client connections → 20 real database connections         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Connection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    PgBouncer Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                                               │
│   │  Django 1   │─┐                                             │
│   └─────────────┘ │    ┌─────────────────┐    ┌──────────────┐  │
│   ┌─────────────┐ │    │                 │    │              │  │
│   │  Django 2   │─┼───►│   PgBouncer     │───►│  PostgreSQL  │  │
│   └─────────────┘ │    │   Port: 6432    │    │  Port: 5432  │  │
│   ┌─────────────┐ │    │                 │    │              │  │
│   │  Django 3   │─┘    │  ┌───────────┐  │    │              │  │
│   └─────────────┘      │  │ Pool: 50  │  │    │  max_conn:   │  │
│                        │  │connections│  │    │  100         │  │
│   Many client          │  └───────────┘  │    │              │  │
│   connections          └─────────────────┘    └──────────────┘  │
│   (hundreds)               Few real              Handles        │
│                            connections           less load      │
│                            (tens)                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Description | Our Value |
|-----------|-------------|-----------|
| **Listen Port** | Port clients connect to | 6432 |
| **Pool Size** | Connections to PostgreSQL | 50 |
| **Max Client Conn** | Max client connections | 200 |
| **Pool Mode** | How connections are reused | transaction |

---

## Pool Modes

PgBouncer has three pool modes that determine when connections are returned to the pool:

### Session Mode

Connection is held for the **entire client session**.

```
┌─────────────────────────────────────────────────────────────────┐
│                       Session Mode                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Client connects ──────────────────────────────────────────►   │
│                    │                                        │   │
│                    │  Connection held entire time           │   │
│                    │  (even between queries)                │   │
│                    │                                        │   │
│   Query 1 ─────────┤                                        │   │
│   [idle 5 sec]     │  ← Connection NOT released             │   │
│   Query 2 ─────────┤                                        │   │
│   [idle 10 sec]    │  ← Connection NOT released             │   │
│   Query 3 ─────────┤                                        │   │
│                    │                                        │   │
│   Client disconnects ───────────────────────────────────────►   │
│                         Connection returned to pool             │
│                                                                 │
│   ✅ Supports: All PostgreSQL features                          │
│   ❌ Efficiency: Same as no pooling                             │
│   Use case: Only when other modes don't work                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Transaction Mode (Recommended)

Connection is returned to pool **after each transaction**.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Transaction Mode ⭐                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   BEGIN ─────────────────────► Connection acquired              │
│     │                                                           │
│     ├── SELECT * FROM users                                     │
│     ├── UPDATE users SET ...                                    │
│     │                                                           │
│   COMMIT ────────────────────► Connection returned to pool      │
│                                                                 │
│   [idle time] ───────────────► Other clients can use it!        │
│                                                                 │
│   BEGIN ─────────────────────► May get different connection     │
│     │                                                           │
│     ├── INSERT INTO orders                                      │
│     │                                                           │
│   COMMIT ────────────────────► Connection returned              │
│                                                                 │
│   ✅ Efficiency: Excellent (connections reused between txns)    │
│   ✅ Django: Works perfectly (autocommit mode)                  │
│   ⚠️ Limitations: No session-level state between transactions   │
│   Use case: Web applications, APIs (most common)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Statement Mode

Connection is returned to pool **after each statement**.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Statement Mode                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SELECT * FROM users ───────► Get connection, execute, return  │
│   UPDATE users SET ... ──────► Get connection, execute, return  │
│   INSERT INTO orders ────────► Get connection, execute, return  │
│                                                                 │
│   ⚠️ Each statement may use different connection!               │
│                                                                 │
│   ✅ Efficiency: Maximum                                        │
│   ❌ Transactions: NOT SUPPORTED                                │
│   ❌ Multi-statement queries: NOT SUPPORTED                     │
│   Use case: Very specific read-only workloads                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Mode Comparison

| Feature | Session | Transaction | Statement |
|---------|---------|-------------|-----------|
| **Connection reuse** | Per session | Per transaction | Per statement |
| **Efficiency** | Low | High | Highest |
| **Transactions** | ✅ Full | ✅ Full | ❌ No |
| **Prepared statements** | ✅ Yes | ⚠️ Per-txn only | ❌ No |
| **SET commands** | ✅ Persist | ❌ Reset after txn | ❌ No |
| **Advisory locks** | ✅ Yes | ❌ No | ❌ No |
| **LISTEN/NOTIFY** | ✅ Yes | ❌ No | ❌ No |
| **Django compatibility** | ✅ Full | ✅ Good | ❌ Limited |
| **Recommended for** | Special cases | Web apps ⭐ | Read-only |

### Our Choice: Transaction Mode

We use **transaction mode** because:

1. **Django uses autocommit** — Each query is a transaction
2. **High efficiency** — Connections released immediately after query
3. **Good compatibility** — Works with most Django ORM operations
4. **Web-friendly** — Perfect for request-response pattern

---

## Why PgBouncer in Kubernetes

### The Connection Explosion Problem

```
┌─────────────────────────────────────────────────────────────────┐
│              Kubernetes Connection Math                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Base setup:                                                   │
│   • 10 pods                                                     │
│   • 4 Gunicorn workers per pod                                  │
│   • 2 threads per worker                                        │
│                                                                 │
│   Connections = 10 × 4 × 2 = 80 connections                     │
│                                                                 │
│   ───────────────────────────────────────────────────────────   │
│                                                                 │
│   Under load (autoscaling to 50 pods):                          │
│   Connections = 50 × 4 × 2 = 400 connections                    │
│                                                                 │
│   PostgreSQL default max_connections = 100                      │
│                                                                 │
│   ⚠️  Result: "FATAL: too many connections"                     │
│                                                                 │
│   ───────────────────────────────────────────────────────────   │
│                                                                 │
│   With PgBouncer:                                               │
│   • 400 client connections → PgBouncer                          │
│   • PgBouncer → 50 real PostgreSQL connections                  │
│   • PostgreSQL handles 50, not 400                              │
│                                                                 │
│   ✅ Result: System works under load                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Additional Kubernetes Benefits

| Benefit | Description |
|---------|-------------|
| **Graceful restarts** | Pods can restart without losing connections |
| **Rolling updates** | New pods connect via pool, old ones drain |
| **Connection limits** | PgBouncer enforces limits, not each pod |
| **Failover handling** | PgBouncer can retry connections |
| **Resource efficiency** | PostgreSQL uses less memory |

### Deployment Options in Kubernetes - TODO

---

## Our Implementation

### Docker Compose Setup (concept)

```yaml
# docker-compose.yml
services:
  postgres_storefront_catalog_service:
    image: postgres:17
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: storefront_catalog
    ports:
      - "5555:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d storefront_catalog"]
      interval: 5s
      timeout: 5s
      retries: 10

  pgbouncer:
    image: edoburu/pgbouncer:latest
    ports:
      - "6432:6432"
    environment:
      DB_HOST: postgres_storefront_catalog_service
      DB_PORT: "5432"
      DB_USER: postgres
      DB_PASSWORD: postgres
      DB_NAME: storefront_catalog
      LISTEN_PORT: "6432"
      AUTH_TYPE: scram-sha-256
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 200
      DEFAULT_POOL_SIZE: 50
      MIN_POOL_SIZE: 10
      RESERVE_POOL_SIZE: 10
      SERVER_RESET_QUERY: "DISCARD ALL"
    depends_on:
      postgres_storefront_catalog_service:
        condition: service_healthy
```

### Environment Variables

| Variable | Description | Our Value |
|----------|-------------|-----------|
| `DB_HOST` | PostgreSQL host | postgres_storefront_catalog_service |
| `DB_PORT` | PostgreSQL port | 5432 |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | postgres |
| `DB_NAME` | Database name | storefront_catalog |
| `LISTEN_PORT` | PgBouncer listen port | 6432 |
| `AUTH_TYPE` | Authentication method | scram-sha-256 |
| `POOL_MODE` | Pool mode | transaction |
| `MAX_CLIENT_CONN` | Max client connections | 200 |
| `DEFAULT_POOL_SIZE` | Default pool size | 50 |
| `MIN_POOL_SIZE` | Minimum pool size | 10 |
| `RESERVE_POOL_SIZE` | Reserve connections | 10 |
| `SERVER_RESET_QUERY` | Query to reset connection | DISCARD ALL |

---

## Configuration

### Pool Size Tuning

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pool Size Guidelines                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   PostgreSQL max_connections = 100 (example)                    │
│                                                                 │
│   Reserve for:                                                  │
│   • Superuser connections: 3                                    │
│   • Monitoring: 2                                               │
│   • Migrations (direct): 5                                      │
│   • Buffer: 10                                                  │
│   ─────────────────────────────                                 │
│   Available for PgBouncer: 80                                   │
│                                                                 │
│   PgBouncer settings:                                           │
│   • default_pool_size = 50  (normal operations)                 │
│   • min_pool_size = 10      (always keep ready)                 │
│   • reserve_pool_size = 10  (burst handling)                    │
│   ─────────────────────────────                                 │
│   Max PgBouncer connections: 70 (within 80 limit)               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Important Settings

```ini
[pgbouncer]
; Connection limits
max_client_conn = 200          ; Max clients connecting to PgBouncer
default_pool_size = 50         ; Connections per user/database pair
min_pool_size = 10             ; Minimum connections to keep
reserve_pool_size = 10         ; Extra connections for bursts
reserve_pool_timeout = 5       ; Seconds before using reserve

; Pool behavior
pool_mode = transaction        ; Return connection after transaction
server_reset_query = DISCARD ALL  ; Clean connection state

; Timeouts
server_connect_timeout = 15    ; Timeout connecting to PostgreSQL
server_login_retry = 15        ; Retry interval on connection failure
query_timeout = 0              ; 0 = no timeout (use Django's)
client_idle_timeout = 0        ; 0 = no timeout

; Logging
log_connections = 1            ; Log client connections
log_disconnections = 1         ; Log client disconnections
log_pooler_errors = 1          ; Log pooler errors
```

### MAX_CLIENT_CONN: Limits and Scaling

The `max_client_conn` setting controls how many client connections PgBouncer accepts. The default of 200 is conservative — PgBouncer can handle **much more**.

#### Theoretical Limits

| Component | Limit | Bottleneck |
|-----------|-------|------------|
| **PgBouncer** | ~50,000+ | OS file descriptors |
| **PostgreSQL** | 100-500 (practical) | Each connection = ~10MB RAM + process |

#### Recommended Values by Scenario

| Scenario | MAX_CLIENT_CONN | Rationale |
|----------|-----------------|------------|
| Dev/Local | 100-200 | Sufficient for development |
| Small production | 500-1,000 | Typical web application |
| Medium load | 2,000-5,000 | Multiple services/pods |
| High load | 5,000-10,000+ | Kubernetes autoscaling |

#### Calculating MAX_CLIENT_CONN

```
MAX_CLIENT_CONN = pods × workers × threads × connections_per_thread × safety_factor

Example for Kubernetes:
• 20 pods
• 4 Gunicorn workers per pod
• 2 threads per worker
• 1.5 safety factor

MAX_CLIENT_CONN = 20 × 4 × 2 × 1.5 = 240 → round up to 500
```

#### Docker Compose Configuration for High Values

When increasing `max_client_conn` significantly, you must also increase OS file descriptor limits:

```yaml
# docker-compose.yml
pgbouncer:
  environment:
    MAX_CLIENT_CONN: 1000  # or 5000, 10000
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
```

#### Connection Ratio: Clients to PostgreSQL

```
┌─────────────────────────────────────────────────────────────────┐
│                    Connection Multiplexing                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   MAX_CLIENT_CONN = 1000     (clients → PgBouncer)              │
│   DEFAULT_POOL_SIZE = 50     (PgBouncer → PostgreSQL)           │
│                                                                 │
│   Ratio: 20:1 (1000 clients share 50 real connections)          │
│                                                                 │
│   ✅ This is normal for transaction mode!                       │
│   ✅ Web app connections are active <1% of the time             │
│   ✅ PgBouncer efficiently multiplexes idle connections         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Django Integration

### How Django Transactions Work with PgBouncer

In `transaction pooling` mode, PgBouncer holds the PostgreSQL connection for the duration of the transaction, then returns it to the pool.

```
┌─────────────────────────────────────────────────────────────────┐
│           Django Transaction Flow with PgBouncer               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Django App              PgBouncer              PostgreSQL     │
│                                                                 │
│   BEGIN ─────────────────► Acquires conn ───────► Starts TX     │
│   SELECT * FROM ... ─────► (holds conn) ────────► Executes      │
│   UPDATE ... ────────────► (holds conn) ────────► Executes      │
│   INSERT ... ────────────► (holds conn) ────────► Executes      │
│   COMMIT ────────────────► Returns conn ────────► Commits TX    │
│                            to pool ✓                            │
│                                                                 │
│   [idle time] ───────────► Other clients can use it!            │
│                                                                 │
│   BEGIN ─────────────────► May get different ───► New TX        │
│                            connection                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Transaction Mode: What Works and What Doesn't

#### ✅ Fully Supported

| Operation | Example | Explanation |
|-----------|---------|-------------|
| `@transaction.atomic` | View decorator | Connection held until COMMIT/ROLLBACK |
| `with transaction.atomic():` | Context manager | Same as above |
| Nested atomic (savepoints) | Nested blocks | Works within single transaction |
| `select_for_update()` | Row locking | Locks live within transaction |
| Bulk operations | `bulk_create()`, `bulk_update()` | Atomic operations |
| `on_commit()` callbacks | Post-commit hooks | Execute after COMMIT |

#### ⚠️ NOT Supported (use `direct` connection)

| Operation | Reason | Solution |
|-----------|--------|----------|
| `CREATE INDEX CONCURRENTLY` | Requires session mode | `connections['direct']` |
| `pg_advisory_lock()` | Lock lost when returned to pool | `connections['direct']` |
| `SET search_path` (outside TX) | Not preserved between transactions | Set in each TX |
| Prepared statements | Disappear after TX | Disable or use session mode |
| `LISTEN/NOTIFY` | Requires persistent connection | Separate worker with direct |

### Code Examples

#### Regular Transactions — Work Through PgBouncer

```python
from django.db import transaction

# ✅ Decorator — everything in one transaction
@transaction.atomic
def create_order(user, items):
    order = Order.objects.create(user=user, status='pending')
    OrderItem.objects.bulk_create([
        OrderItem(order=order, product=item['product'], quantity=item['qty'])
        for item in items
    ])
    # COMMIT happens automatically on exit
    return order

# ✅ Context manager — explicit control
def transfer_money(from_account, to_account, amount):
    with transaction.atomic():
        from_account.balance -= amount
        from_account.save()

        to_account.balance += amount
        to_account.save()
        # COMMIT here

# ✅ Nested transactions (savepoints)
@transaction.atomic
def complex_operation():
    do_critical_stuff()

    try:
        with transaction.atomic():  # Savepoint
            risky_operation()       # May fail
    except SomeException:
        pass  # Rollback only savepoint

    do_more_stuff()  # Continue main TX
```

#### Select for Update — Works

```python
# ✅ Row locking within transaction
@transaction.atomic
def reserve_product(product_id, quantity):
    # Lock row until end of transaction
    product = Product.objects.select_for_update().get(id=product_id)

    if product.stock >= quantity:
        product.stock -= quantity
        product.save()
        return True
    return False
```

#### On Commit Callbacks — Work

```python
from django.db import transaction

@transaction.atomic
def create_user_with_notification(data):
    user = User.objects.create(**data)

    # Executes ONLY if TX succeeds
    transaction.on_commit(
        lambda: send_welcome_email.delay(user.id)
    )

    return user
```

#### Special Operations — Require Direct Connection

```python
from django.db import connections

# ⚠️ CREATE INDEX CONCURRENTLY — only via direct
def create_concurrent_index():
    with connections['direct'].cursor() as cursor:
        cursor.execute(
            'CREATE INDEX CONCURRENTLY idx_orders_created '
            'ON orders(created_at)'
        )

# ⚠️ Advisory locks — only via direct
def with_advisory_lock(lock_id):
    with connections['direct'].cursor() as cursor:
        cursor.execute('SELECT pg_advisory_lock(%s)', [lock_id])
        try:
            do_exclusive_work()
        finally:
            cursor.execute('SELECT pg_advisory_unlock(%s)', [lock_id])

# ⚠️ LISTEN/NOTIFY — requires persistent connection
def listen_for_events():
    conn = connections['direct']
    conn.ensure_connection()

    with conn.cursor() as cursor:
        cursor.execute('LISTEN order_events')

        while True:
            # Wait for notifications
            if select.select([conn.connection], [], [], 5) != ([], [], []):
                conn.connection.poll()
                while conn.connection.notifies:
                    notify = conn.connection.notifies.pop(0)
                    process_event(notify.payload)
```

### CONN_MAX_AGE: Critically Important!

```python
DATABASES = {
    "default": {
        # ...
        # ⚠️ MUST be 0 when using PgBouncer!
        "CONN_MAX_AGE": 0 if USE_PGBOUNCER else 600,
    }
}
```

**Why `CONN_MAX_AGE=0`?**

```
┌─────────────────────────────────────────────────────────────────┐
│           Problem with CONN_MAX_AGE > 0 + PgBouncer             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CONN_MAX_AGE=600 (Django caches connection):                  │
│                                                                 │
│   Django Worker ───► [Cached conn to PgBouncer]                 │
│                      │                                          │
│                      │ PgBouncer may close                      │
│                      │ server connection via                    │
│                      │ server_idle_timeout                      │
│                      ▼                                          │
│   Django thinks connection is alive,                            │
│   but PgBouncer already closed it!                              │
│                                                                 │
│   Result: "server closed the connection unexpectedly"           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   CONN_MAX_AGE=0 (Django doesn't cache):                        │
│                                                                 │
│   Request 1 ──► Get from PgBouncer ──► Query ──► Return to pool │
│   Request 2 ──► Get from PgBouncer ──► Query ──► Return to pool │
│                                                                 │
│   PgBouncer manages the entire pool ✓                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Database Settings

```python
# settings/settings_databases.py

from decouple import config

# Switch between PgBouncer and direct connection
USE_PGBOUNCER = config("USE_PGBOUNCER", default="true").lower() == "true"

if USE_PGBOUNCER:
    DB_HOST = config("PGBOUNCER_HOST", default="pgbouncer")
    DB_PORT = config("PGBOUNCER_PORT", default="6432")
else:
    DB_HOST = config("POSTGRES_HOST", default="postgres_storefront_catalog_service")
    DB_PORT = config("POSTGRES_PORT", default="5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="storefront_catalog"),
        "USER": config("POSTGRES_USER", default="postgres"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="postgres"),
        "HOST": DB_HOST,
        "PORT": DB_PORT,
        # Let PgBouncer handle pooling
        "CONN_MAX_AGE": 0 if USE_PGBOUNCER else 600,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}

# Direct connection for migrations
DATABASES["direct"] = {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": config("POSTGRES_DB", default="storefront_catalog"),
    "USER": config("POSTGRES_USER", default="postgres"),
    "PASSWORD": config("POSTGRES_PASSWORD", default="postgres"),
    "HOST": config("POSTGRES_HOST", default="postgres_storefront_catalog_service"),
    "PORT": config("POSTGRES_PORT", default="5432"),
    "CONN_MAX_AGE": 600,
}
```

### Key Settings Explained

| Setting | With PgBouncer | Without PgBouncer | Why |
|---------|----------------|-------------------|-----|
| `CONN_MAX_AGE` | `0` | `600` | PgBouncer manages pooling |
| `HOST` | `pgbouncer` | `postgres` | Different endpoints |
| `PORT` | `6432` | `5432` | PgBouncer's port |

### Running Migrations

Migrations should run **directly against PostgreSQL**, not through PgBouncer:

```bash
# In docker-compose command
USE_PGBOUNCER=false python manage.py migrate

# Or manually
docker compose exec storefront_catalog_service \
    sh -c "USE_PGBOUNCER=false uv run python manage.py migrate"
```

**Why?** Transaction mode doesn't support:

- `CREATE INDEX CONCURRENTLY`
- Long-running DDL operations
- Advisory locks used by migration frameworks

---

## Testing (concept, not implemented yet)

### The Problem

Django tests **cannot run through PgBouncer** in transaction mode because they require:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Django Test Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. CREATE DATABASE test_storefront_catalog  ← DDL operation   │
│   2. Run migrations                           ← DDL operations  │
│   3. Run tests                                                  │
│   4. DROP DATABASE test_storefront_catalog    ← DDL operation   │
│                                                                 │
│   Transaction mode PgBouncer does NOT support:                  │
│   • CREATE DATABASE / DROP DATABASE                             │
│   • Some DDL operations                                         │
│   • Session-level state required for test transactions          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Running Tests
### Pytest Configuration
### CI/CD
### Test Isolation

Each test runs in a transaction that's rolled back:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Test Isolation                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   test_create_user():                                           │
│   ├── BEGIN                                                     │
│   ├── INSERT INTO users ...                                     │
│   ├── Assertions                                                │
│   └── ROLLBACK  ← Database unchanged!                           │
│                                                                 │
│   test_update_user():                                           │
│   ├── BEGIN                                                     │
│   ├── UPDATE users SET ...                                      │
│   ├── Assertions                                                │
│   └── ROLLBACK  ← Database unchanged!                           │
│                                                                 │
│   This requires session-level control that PgBouncer            │
│   transaction mode doesn't provide.                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### 1. Always Use Transaction Mode for Web Apps

```yaml
POOL_MODE: transaction
```

### 2. Set CONN_MAX_AGE = 0 in Django

```python
# Let PgBouncer manage pooling
"CONN_MAX_AGE": 0,
```

### 3. Run Migrations Directly

```bash
USE_PGBOUNCER=false python manage.py migrate
```

### 4. Run Tests Directly

```bash
# Automatic with our settings, or explicit:
USE_PGBOUNCER=false python manage.py test
```

### 5. Size Your Pool Correctly

```
default_pool_size = (PostgreSQL max_connections - reserved) / number_of_databases
```

### 6. Monitor Wait Times

If `cl_waiting > 0` frequently, increase pool size.

### 7. Use Health Checks

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -h 127.0.0.1 -p 6432"]
  interval: 5s
  timeout: 5s
  retries: 10
```

### 8. Clean Connection State

```yaml
SERVER_RESET_QUERY: "DISCARD ALL"
```

This resets:
- Temporary tables
- Prepared statements
- Session variables
- Advisory locks

---

## Related Documentation

- [Technologies Overview](index.md)
- [Architecture Diagrams](../about/diagrams.md)
- [Quick Start Guide](../guides/quickstart.md)
