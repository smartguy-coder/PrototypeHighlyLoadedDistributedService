# Celery & Django Celery Beat

Celery is a distributed task queue for processing work asynchronously. Django Celery Beat extends it with a database-backed periodic task scheduler manageable from Django Admin.

---

## Table of Contents

1. [Theory](#theory)
2. [Architecture](#architecture)
3. [Key Concepts](#key-concepts)
4. [Deferred Execution: ETA & Countdown](#deferred-execution-eta--countdown)
5. [Signatures: `.s()` vs `.si()`](#signatures-s-vs-si)
6. [Canvas Primitives: chain, chord, group](#canvas-primitives-chain-chord-group)
7. [Django Celery Beat](#django-celery-beat)
8. [Our Implementation](#our-implementation)
9. [Configuration](#configuration)
10. [Usage Examples](#usage-examples)
11. [Monitoring with Flower](#monitoring-with-flower)
12. [Management Commands](#management-commands)
13. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

---

## Theory

### What is Celery?

Celery is an **asynchronous task queue** based on distributed message passing. It allows you to offload time-consuming work from the request/response cycle into background workers.

Typical use cases:

- Sending emails/SMS (don't block the API response)
- Image/video processing
- Periodic cleanup jobs (cron-style)
- Aggregation and report generation
- Anything that takes longer than ~200ms

### When to Use Celery?

| Use Case | Celery | Alternative |
|----------|--------|-------------|
| Background task processing | ✅ Best choice | — |
| Periodic/scheduled tasks | ✅ Best choice | cron |
| Simple task queue (Python) | ✅ Best choice | — |
| High-throughput event streaming | ⚠️ Not ideal | Kafka |
| Real-time pub/sub | ⚠️ Not ideal | Redis Pub/Sub |
| Long-running workflows | ⚠️ Consider | Temporal, Airflow |

### Celery vs Kafka

| Aspect | Celery + RabbitMQ | Kafka |
|--------|-------------------|-------|
| **Model** | Task queue (worker pulls job) | Distributed log (consumer reads stream) |
| **Semantics** | "Do this work" | "This event happened" |
| **Message retention** | Until consumed & acked | Configurable (days/weeks) |
| **Replay** | ❌ No | ✅ Yes |
| **Ordering** | Per queue | Per partition |
| **Throughput** | Tens of thousands/sec | Millions/sec |
| **Best for** | Background jobs, cron | Event streaming, analytics |
| **Our usage** | OTP cleanup, emails, heavy tasks | OTP notifications, inter-service events |

---

## Architecture

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Celery Architecture                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐                                                       │
│   │  Django App     │                                                       │
│   │  (Producer)     │                                                       │
│   │                 │   .delay() / .apply_async()                           │
│   │  task.delay(arg)│───────────────────────┐                               │
│   └─────────────────┘                       │                               │
│                                             ▼                               │
│   ┌─────────────────┐              ┌─────────────────┐                      │
│   │  Celery Beat    │              │    RabbitMQ     │                      │
│   │  (Scheduler)    │─────────────►│    (Broker)     │                      │
│   │                 │  periodic    │                 │                      │
│   │  every 5 min:   │  tasks       │  ┌────────────┐ │                      │
│   │  cleanup_otp    │              │  │ Q: default │ │                      │
│   └─────────────────┘              │  │ Q: emails  │ │                      │
│                                    │  │ Q: heavy   │ │                      │
│                                    │  └────────────┘ │                      │
│                                    └────────┬────────┘                      │
│                                             │                               │
│                                             ▼                               │
│                                    ┌─────────────────┐                      │
│                                    │  Celery Worker  │                      │
│                                    │  (Consumer)     │                      │
│                                    │                 │                      │
│                                    │  -Q default,    │                      │
│                                    │     emails,     │                      │
│                                    │     heavy       │                      │
│                                    └─────────────────┘                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | Role | Our Setup |
|-----------|------|-----------|
| **Producer** | Sends tasks to the broker | Django app (`task.delay()`) |
| **Broker** | Message transport (queue storage) | RabbitMQ (`amqp://`) |
| **Worker** | Executes tasks from queues | `celery -A celery_app worker` |
| **Beat** | Sends periodic tasks on schedule | `celery -A celery_app beat` |
| **Flower** | Web UI for monitoring | `celery -A celery_app flower` |
| **Result Backend** | Stores task return values | `None` (disabled) |

### Docker Compose Services

```
┌───────────────────────────────────────────────────────────────────┐
│                    Our Celery Infrastructure                      │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐   ┌──────────────────┐                      │
│  │  rabbitmq        │   │  celery_worker   │                      │
│  │  Port: 5672      │◄──│  -Q default,     │                      │
│  │  UI:   15672     │   │     emails,heavy │                      │
│  └──────────────────┘   └──────────────────┘                      │
│          ▲                                                        │
│          │                                                        │
│  ┌───────┴──────────┐   ┌──────────────────┐                      │
│  │ celery_beat      │   │  flower          │                      │
│  │ DatabaseScheduler│   │  Port: 5556      │                      │
│  └──────────────────┘   └──────────────────┘                      │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### Tasks

A **task** is a Python function decorated with `@shared_task` or `@app.task`. When called asynchronously, it is serialized and sent to the broker.

```python
from celery import shared_task

@shared_task(queue="default", bind=True)
def simple_task(self):
    print(f"Running task {self.request.id}")
```

Key parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `queue` | Which queue to send to | `"default"`, `"emails"`, `"heavy"` |
| `bind=True` | Gives access to `self` (task instance) | Access `self.request.id`, `self.request.retries` |
| `name` | Explicit task name (overrides auto-naming) | `"services.periodic_test_task"` |
| `max_retries` | Max retry attempts | `3` |
| `default_retry_delay` | Seconds between retries | `60` |

### Queues

Queues separate tasks by priority or type. Workers subscribe to specific queues.

```python
# settings_celery.py
from kombu import Queue

CELERY_TASK_QUEUES = (
    Queue("default"),   # general-purpose tasks
    Queue("emails"),    # email sending
    Queue("heavy"),     # CPU-intensive processing
)

CELERY_TASK_DEFAULT_QUEUE = "default"
```

Worker subscribes to queues:

```bash
celery -A celery_app worker -l info -Q default,emails,heavy
```

### Calling Tasks

| Method | Description | Example |
|--------|-------------|---------|
| `task.delay(*args)` | Shortcut for `apply_async` | `add.delay(2, 3)` |
| `task.apply_async(args, kwargs, ...)` | Full control (eta, countdown, queue) | `add.apply_async(args=(2, 3), countdown=60)` |
| `task.apply(args)` | Execute synchronously (testing) | `add.apply(args=(2, 3))` |
| `task.s(*args)` | Create a mutable signature | `add.s(2, 3)` |
| `task.si(*args)` | Create an immutable signature | `add.si(2, 3)` |

### Acknowledgment and Reliability

```python
# Task is acknowledged AFTER execution (not before)
CELERY_TASK_ACKS_LATE = True

# Worker takes only 1 task at a time
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
```

With `ACKS_LATE=True`: if a worker crashes mid-task, the message returns to the queue and another worker picks it up. Without it, the task would be lost.

---

## Deferred Execution: ETA & Countdown

Sometimes you need to run a task not immediately, but **at a specific time in the future** — a one-shot deferred execution. Celery supports this natively via `eta` and `countdown` parameters of `apply_async()`.

### `eta` — Execute at Exact Time

`eta` (Estimated Time of Arrival) accepts a `datetime` object. The task is published to the broker immediately but the worker will **not execute it until** the specified time.

```python
from datetime import datetime, timedelta, timezone
from apps.users.tasks import simple_task_with_defined_time

# Run this task exactly 1 minute from now
simple_task_with_defined_time.apply_async(
    args=[serializer.data],
    eta=datetime.now(timezone.utc) + timedelta(minutes=1),
)

# Run at a specific wall-clock time
run_at = datetime(2026, 4, 26, 10, 0, 0, tzinfo=timezone.utc)
simple_task_with_defined_time.apply_async(
    args=[{"action": "scheduled_report"}],
    eta=run_at,
)
```

### `countdown` — Execute After N Seconds

`countdown` is a convenience shortcut for `eta`. Instead of computing a datetime you just say "run in N seconds".

```python
# Run after 30 seconds
add.apply_async(args=(2, 3), countdown=30)

# Equivalent to:
from datetime import datetime, timedelta, timezone
add.apply_async(args=(2, 3), eta=datetime.now(timezone.utc) + timedelta(seconds=30))
```

### How It Works Under the Hood

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETA / Countdown Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Producer calls apply_async(eta=future_time)                 │
│  2. Message is sent to RabbitMQ immediately                     │
│  3. Worker picks up the message from the queue                  │
│  4. Worker sees eta > now → holds the task in memory            │
│  5. Worker waits until eta is reached                           │
│  6. Worker executes the task                                    │
│                                                                 │
│   t=0          t=0           t=0              t=60s             │
│   ┌──────┐    ┌──────────┐  ┌──────────────┐  ┌──────────────┐  │
│   │ App  │───►│ RabbitMQ │─►│ Worker       │─►│ Worker       │  │
│   │ send │    │ queue    │  │ receives msg │  │ executes     │  │
│   └──────┘    └──────────┘  │ holds 60s    │  │ the task     │  │
│                             └──────────────┘  └──────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### `eta` vs `countdown` vs Beat

| Feature | `eta` / `countdown` | Celery Beat |
|---------|---------------------|-------------|
| **When to use** | One-time deferred execution | Recurring schedule |
| **Trigger** | From application code | Automatic by scheduler |
| **Persistence** | Message in broker queue | Schedule in database |
| **Survives restart** | ✅ Yes (message stays in broker) | ✅ Yes (schedule in DB) |
| **Example** | "Send reminder in 1 hour" | "Clean up OTP every 5 min" |
| **Cancellable** | ⚠️ Difficult (need `revoke`) | ✅ Easy (disable in Admin) |

### Our Implementation

```python
# users/tasks.py
@shared_task(queue="default", bind=True)
def simple_task_with_defined_time(self, data):
    """Demo task that runs at a scheduled time via apply_async + eta."""
    logger.info(
        "[simple_task_with_defined_time] started | task_id=%s retries=%s data=%s",
        self.request.id, self.request.retries, data,
    )
```

Called from a DRF view/serializer:

```python
# In a view or serializer after successful validation
from datetime import datetime, timedelta, timezone
from apps.users.tasks import simple_task_with_defined_time

simple_task_with_defined_time.apply_async(
    args=[serializer.data],
    eta=datetime.now(timezone.utc) + timedelta(minutes=1),
)
```

### Real-World Use Cases for ETA

| Use Case | ETA Value |
|----------|-----------|
| Send order confirmation after payment processing | `now + 30s` |
| Reminder email if user hasn't completed onboarding | `now + 24h` |
| Auto-cancel unpaid order | `now + 15min` |
| Delayed notification ("Your report is ready") | `now + processing_time` |
| Scheduled social media post | Exact `datetime` |

!!! warning "ETA precision"
    ETA is **not a real-time guarantee**. The task runs *at or after* the specified time. If all workers are busy, the task waits in the queue. For second-level precision, ensure enough worker capacity.

---

## Signatures: `.s()` vs `.si()`

Signatures are the building blocks for composing tasks into workflows (chains, chords, groups). The key difference is whether the **result of the previous task** is passed to the next one.

### `.s()` — Mutable Signature

`.s()` (shortcut for `.signature()`) creates a **mutable** signature. The return value of the previous task is **prepended** as the first argument to the next task.

```python
# The previous result is injected as the first argument
add.s(10)  # → will be called as add(prev_result, 10)
```

### `.si()` — Immutable Signature

`.si()` (shortcut for `.signature(immutable=True)`) creates an **immutable** signature. The return value of the previous task is **completely ignored**. The task receives only the arguments you explicitly provide.

```python
# The previous result is discarded
add.si(10, 20)  # → always called as add(10, 20), regardless of previous result
```

### Side-by-Side Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    .s() vs .si() Comparison                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  .s() — Mutable (result IS passed)                              │
│  ─────────────────────────────────                              │
│  chain(                                                         │
│      add.s(2, 3),      # → 5                                    │
│      multiply.s(10),   # → multiply(5, 10) = 50                 │
│      add.s(100),       # → add(50, 100) = 150                   │
│  )                                                              │
│  Result flows: 5 → 50 → 150                                     │
│                                                                 │
│  ───────────────────────────────────────────────────────────────│
│                                                                 │
│  .si() — Immutable (result is IGNORED)                          │
│  ─────────────────────────────────────                          │
│  chain(                                                         │
│      add.si(2, 3),       # → 5   (discarded)                    │
│      multiply.si(4, 5),  # → 20  (does NOT receive 5)           │
│      add.si(10, 20),     # → 30  (does NOT receive 20)          │
│  )                                                              │
│  No result flow — each task is independent                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### When to Use Each

| Scenario | Use | Why |
|----------|-----|-----|
| Data pipeline (each step transforms output) | `.s()` | Results flow between tasks |
| Independent sequential steps | `.si()` | Tasks don't depend on each other's output |
| Chord callback that needs header results | `.s()` | Callback receives list of results |
| Chord callback that ignores header results | `.si()` | Callback fires after group, but doesn't need data |

---

## Canvas Primitives: chain, chord, group

Celery provides **canvas primitives** for composing tasks into complex workflows.

### chain — Sequential Pipeline

A `chain` executes tasks one after another, optionally passing results forward.

```python
from celery import chain

# With .s() — results flow through the pipeline
pipeline = chain(
    add.s(2, 3),       # → 5
    multiply.s(10),    # → multiply(5, 10) = 50
    add.s(100),        # → add(50, 100) = 150
)
pipeline.apply_async()
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    chain with .s()                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   add(2, 3) ──► multiply(5, 10) ──► add(50, 100)                │
│       │              │                    │                     │
│       ▼              ▼                    ▼                     │
│       5              50                  150                    │
│       └──────────────┘                    ▲                     │
│              result passed ───────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```python
# With .si() — tasks run sequentially but independently
pipeline = chain(
    add.si(2, 3),       # → 5   (discarded)
    multiply.si(4, 5),  # → 20  (independent)
    add.si(10, 20),     # → 30  (independent)
)
pipeline.apply_async()
```

```
┌─────────────────────────────────────────────────────────────────┐
│                    chain with .si()                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   add(2, 3) ──► multiply(4, 5) ──► add(10, 20)                  │
│       │              │                    │                     │
│       ▼              ▼                    ▼                     │
│       5              20                   30                    │
│       (dropped)      (dropped)                                  │
│                                                                 │
│   Each task uses only its own explicit arguments                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### group — Parallel Execution

A `group` executes tasks in parallel and returns a list of results.

```python
from celery import group

# All tasks start simultaneously
parallel = group(
    add.s(1, 2),   # → 3
    add.s(3, 4),   # → 7
    add.s(5, 6),   # → 11
)
result = parallel.apply_async()
# result.get() → [3, 7, 11]
```

```
┌─────────────────────────────────────────────────────────────────┐
│                       group (parallel)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│           ┌── add(1, 2) ──► 3  ──┐                              │
│           │                      │                              │
│   START ──┼── add(3, 4) ──► 7  ──┼──► [3, 7, 11]                │
│           │                      │                              │
│           └── add(5, 6) ──► 11 ──┘                              │
│                                                                 │
│   All tasks run in parallel on available workers                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### chord — Parallel + Callback

A `chord` is a `group` with a **callback** that fires after all parallel tasks complete. The callback receives the collected results as its first argument (if using `.s()`).

```python
from celery import chord

# Header tasks run in parallel, then callback fires
task_group = chord(
    [add.s(1, 2), add.s(3, 4), add.s(5, 6)],  # header (parallel)
    aggregate.s(),                               # callback
)
task_group.apply_async()
# aggregate receives [3, 7, 11] → returns 21
```

```
┌─────────────────────────────────────────────────────────────────┐
│                   chord with .s() callback                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   HEADER (parallel):                                            │
│           ┌── add(1, 2) ──► 3  ──┐                              │
│           │                      │                              │
│   START ──┼── add(3, 4) ──► 7  ──┼──► aggregate([3, 7, 11])     │
│           │                      │           │                  │
│           └── add(5, 6) ──► 11 ──┘           ▼                  │
│                                              21                 │
│                                                                 │
│   Callback receives [3, 7, 11] as first arg via .s()            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

With `.si()` callback — results are discarded:

```python
task_group = chord(
    [add.s(1, 2), add.s(3, 4), add.s(5, 6)],  # header (parallel)
    multiply.si(10, 20),                        # callback ignores results
)
task_group.apply_async()
# multiply(10, 20) → 200 (header results discarded)
```

```
┌─────────────────────────────────────────────────────────────────┐
│                   chord with .si() callback                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   HEADER (parallel):                                            │
│           ┌── add(1, 2) ──► 3  ──┐                              │
│           │                      │                              │
│   START ──┼── add(3, 4) ──► 7  ──┼──► multiply(10, 20)          │
│           │                      │           │                  │
│           └── add(5, 6) ──► 11 ──┘           ▼                  │
│                                 (ignored)   200                 │
│                                                                 │
│   Callback ignores header results — uses only its own args      │
│   Use case: "wait for group, then do unrelated action"          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Canvas Summary

| Primitive | Behavior | Result |
|-----------|----------|--------|
| `chain(a, b, c)` | a → b → c (sequential) | Result of last task |
| `group(a, b, c)` | a ∥ b ∥ c (parallel) | List of all results |
| `chord([a, b, c], callback)` | (a ∥ b ∥ c) → callback | Result of callback |

---

## Django Celery Beat

### What is Django Celery Beat?

`django-celery-beat` stores the periodic task schedule in the **database** instead of a file. This means you can:

- Add/remove/modify periodic tasks via **Django Admin**
- Change schedules at runtime without restarting Beat
- Use **DatabaseScheduler** to sync in-memory schedule with DB

### How Beat Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   Celery Beat Lifecycle                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Beat starts with DatabaseScheduler                          │
│  2. Reads CELERY_BEAT_SCHEDULE from settings → syncs to DB      │
│  3. Reads all PeriodicTask entries from DB                      │
│  4. Every tick (~5s), checks what tasks are due                 │
│  5. Sends due tasks to the broker (RabbitMQ)                    │
│  6. Worker picks up and executes the task                       │
│                                                                 │
│   ┌───────────┐    ┌───────────┐    ┌────────────┐    ┌────────┐│
│   │ Django DB │───►│  Beat     │───►│  RabbitMQ  │───►│ Worker ││
│   │(schedule) │    │(scheduler)│    │  (broker)  │    │        ││
│   └───────────┘    └───────────┘    └────────────┘    └────────┘│
│         ▲                                                       │
│         │                                                       │
│   ┌─────┴──────┐                                                │
│   │ Django     │  Add/edit periodic tasks at runtime            │
│   │ Admin UI   │                                                │
│   └────────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Schedule Types

| Type | Class | Example |
|------|-------|---------|
| **Interval** | `IntervalSchedule` | Every 10 seconds, every 5 minutes |
| **Crontab** | `CrontabSchedule` | "At 08:00 on Monday", "*/15 * * * *" |
| **Solar** | `SolarSchedule` | At sunrise/sunset for a given location |
| **Clocked** | `ClockedSchedule` | One-time at specific datetime |

### Django Admin Integration

After `django-celery-beat` is installed, Django Admin provides these models:

| Admin Model | Purpose |
|-------------|---------|
| **Periodic Tasks** | List of all scheduled tasks (name, task path, schedule, enabled) |
| **Intervals** | Interval-based schedules (every N seconds/minutes/hours) |
| **Crontabs** | Cron-style schedules (minute, hour, day_of_week, etc.) |
| **Solar events** | Sunrise/sunset-based schedules |
| **Clocked** | One-time execution at a specific datetime |

---

## Our Implementation

### Project Structure

```
storefront_catalog_service/app/
├── celery_app.py                  # Celery application instance
├── settings/
│   └── settings_celery.py         # All Celery configuration
└── apps/
    ├── services/
    │   └── tasks.py               # Service tasks (chain/chord demos)
    └── users/
        └── tasks.py               # User tasks (OTP cleanup)
```

### Celery Application

```python
# celery_app.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

app = Celery("celery_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

`autodiscover_tasks()` scans all `INSTALLED_APPS` for `tasks.py` modules and registers the tasks found.

### Task Registry

**services/tasks.py:**

| Task | Queue | Purpose |
|------|-------|---------|
| `simple_task` | default | Basic test task |
| `send_email` | emails | Email sending placeholder |
| `heavy_task` | heavy | CPU-intensive placeholder |
| `periodic_test_task` | default | Beat heartbeat (every 1 min) |
| `add`, `multiply`, `aggregate` | default | Canvas building blocks |
| `demo_chain_with_s` | default | Chain demo (mutable signatures) |
| `demo_chain_with_si` | default | Chain demo (immutable signatures) |
| `demo_chord_with_s` | default | Chord demo (mutable callback) |
| `demo_chord_with_si` | default | Chord demo (immutable callback) |

**users/tasks.py:**

| Task | Queue | Purpose |
|------|-------|---------|
| `simple_task_with_defined_time` | default | ETA/countdown demo |
| `cleanup_expired_otp_codes` | default | Periodic OTP cleanup (every 5 min) |

### Beat Schedule

```python
# settings_celery.py
CELERY_BEAT_SCHEDULE = {
    "periodic-test-every-minute": {
        "task": "users.periodic_test_task",
        "schedule": 60.0,            # every 60 seconds
        "options": {"queue": "default"},
    },
    "cleanup-expired-otp-codes-every-5-min": {
        "task": "users.cleanup_expired_otp_codes",
        "schedule": 300.0,           # every 300 seconds (5 minutes)
        "options": {"queue": "default"},
    },
}
```

---

## Configuration

### Full Settings Reference

```python
# settings/settings_celery.py

from decouple import config
from kombu import Queue

# ── Queues ─────────────────────────────────────────────────────
CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("emails"),
    Queue("heavy"),
)
CELERY_TASK_DEFAULT_QUEUE = "default"

# ── Broker ─────────────────────────────────────────────────────
CELERY_BROKER_URL = config(
    "CELERY_BROKER_URL",
    default="amqp://guest:guest@rabbitmq:5672//",
)

# ── Serialization ──────────────────────────────────────────────
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

# ── Result Backend ─────────────────────────────────────────────
CELERY_RESULT_BACKEND = None  # disabled (no task results stored)

# ── Timezone ───────────────────────────────────────────────────
CELERY_TIMEZONE = "UTC"

# ── Reliability ────────────────────────────────────────────────
CELERY_TASK_ACKS_LATE = True              # ack after execution
CELERY_WORKER_PREFETCH_MULTIPLIER = 1     # 1 task at a time
CELERY_TASK_TRACK_STARTED = True          # show STARTED state

# ── Publish Retry ──────────────────────────────────────────────
CELERY_TASK_PUBLISH_RETRY = True
CELERY_TASK_PUBLISH_RETRY_POLICY = {
    "max_retries": 10,
    "interval_start": 0,
    "interval_step": 0.5,
    "interval_max": 3,
}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
```

### Setting Explanations

| Setting | Value | Why |
|---------|-------|-----|
| `TASK_ACKS_LATE` | `True` | Task is acked only after successful execution. If worker crashes, message returns to queue. |
| `WORKER_PREFETCH_MULTIPLIER` | `1` | Worker reserves only 1 task at a time. Prevents one slow task from blocking others. |
| `TASK_TRACK_STARTED` | `True` | Tasks report STARTED state. Useful for debugging. |
| `RESULT_BACKEND` | `None` | We don't need to retrieve task return values. Saves resources. |
| `TASK_SERIALIZER` | `json` | JSON is human-readable and cross-language. |
| `BROKER_CONNECTION_RETRY_ON_STARTUP` | `True` | Worker retries broker connection on startup instead of crashing. |

### Docker Compose Services

```yaml
# Worker — executes tasks from all 3 queues
celery_worker:
  build:
    dockerfile: Dockerfile
    context: ./storefront_catalog_service
  command: celery -A celery_app worker -l info -Q default,emails,heavy
  environment:
    - CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
  depends_on:
    rabbitmq:
      condition: service_healthy
    pgbouncer:
      condition: service_healthy

# Beat — periodic task scheduler (single instance!)
celery_beat:
  build:
    dockerfile: Dockerfile
    context: ./storefront_catalog_service
  command: >
    celery -A celery_app beat -l info
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
  depends_on:
    rabbitmq:
      condition: service_healthy
    pgbouncer:
      condition: service_healthy

# Flower — monitoring UI (optional, in "ui" profile)
flower:
  build:
    dockerfile: Dockerfile
    context: ./storefront_catalog_service
  command: celery -A celery_app flower --port=5555
  ports:
    - "5556:5555"
  profiles:
    - ui
```

!!! warning "Beat must be a single instance"
    Never run more than one Beat process. Multiple Beat instances will cause duplicate task dispatches.

---

## Usage Examples

### Basic Task Dispatch

```python
from apps.services.tasks import simple_task, add

# Fire-and-forget
simple_task.delay()

# With arguments
add.delay(2, 3)

# With countdown (run after 60 seconds)
add.apply_async(args=(2, 3), countdown=60)

# With ETA (run at specific time)
from datetime import datetime, timedelta, timezone
eta = datetime.now(timezone.utc) + timedelta(minutes=5)
add.apply_async(args=(2, 3), eta=eta)

# Specify queue explicitly
add.apply_async(args=(2, 3), queue="heavy")
```

### One-Time Deferred Execution (ETA)

```python
from datetime import datetime, timedelta, timezone
from apps.users.tasks import simple_task_with_defined_time

# In a DRF view after successful OTP request:
simple_task_with_defined_time.apply_async(
    args=[serializer.data],
    eta=datetime.now(timezone.utc) + timedelta(minutes=1),
)

# With countdown shortcut (equivalent):
simple_task_with_defined_time.apply_async(
    args=[serializer.data],
    countdown=60,  # run after 60 seconds
)
```

### Chain Example

```python
from celery import chain
from apps.services.tasks import add, multiply

# Sequential pipeline: 2+3=5 → 5*10=50 → 50+100=150
pipeline = chain(
    add.s(2, 3),
    multiply.s(10),
    add.s(100),
)
result = pipeline.apply_async()
```

### Chord Example

```python
from celery import chord
from apps.services.tasks import add, aggregate

# Parallel header → callback
task_group = chord(
    [add.s(1, 2), add.s(3, 4), add.s(5, 6)],
    aggregate.s(),
)
result = task_group.apply_async()
# aggregate([3, 7, 11]) → 21
```

### Periodic Task (OTP Cleanup)

```python
# users/tasks.py
@shared_task(queue="default", bind=True)
def cleanup_expired_otp_codes(self):
    """Delete OTPCode records that expired more than 5 minutes ago."""
    cutoff = dj_timezone.now()
    deleted_count, _ = OTPCode.objects.filter(expires_at__lt=cutoff).delete()
    logger.info(
        "[cleanup_expired_otp_codes] deleted %d expired OTP codes | task_id=%s",
        deleted_count,
        self.request.id,
    )
```

Runs automatically every 5 minutes via Beat schedule.

### Creating a New Task

```python
# 1. Define in the appropriate app's tasks.py
@shared_task(queue="emails", bind=True, max_retries=3)
def send_welcome_email(self, user_id: int):
    """Send welcome email to a newly registered user."""
    try:
        user = User.objects.get(id=user_id)
        # ... send email logic ...
        logger.info("[send_welcome_email] sent to user_id=%s", user_id)
    except Exception as exc:
        logger.error("[send_welcome_email] failed for user_id=%s: %s", user_id, exc)
        raise self.retry(exc=exc, countdown=60)

# 2. Call from your view/serializer
send_welcome_email.delay(user.id)
```

---

## Monitoring with Flower

### Access

**URL:** `http://localhost:5556`

Flower is started with the `ui` Docker Compose profile:

```bash
docker compose --profile ui up -d flower
```

### Dashboard Features

| Tab | Shows |
|-----|-------|
| **Dashboard** | Active/processed/failed tasks, workers online |
| **Workers** | Worker status, pool size, queues, processed count |
| **Tasks** | Real-time task log with state, runtime, args |
| **Broker** | Queue sizes, unacked messages |

### RabbitMQ Management UI

**URL:** `http://localhost:15672`

**Credentials:** `guest` / `guest`

Shows queue depths, connections, channels, message rates — useful for diagnosing broker-level issues.

---

## Management Commands

### `celery_worker_report` — Terminal Analog for Flower UI

**Location:** `storefront_catalog_service/app/apps/services/management/commands/celery_worker_report.py`

A Django management command that displays the current state of all Celery workers and their tasks directly in the terminal — without needing Flower or any browser. Internally uses `CeleryWorkersClient` (see `utils/celery.py`) to query the live Celery inspect API.

```bash
python manage.py celery_worker_report [OPTIONS]
```

#### Output

The command renders two levels of output using the `rich` library:

1. **Summary table** — one row per worker, showing pool type, concurrency, and task counts per state.
2. **Per-worker task tables** — one table per worker/state combination, showing task name, ETA, start/received time, and run time.

#### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--worker WORKER` | all workers | Filter output to a specific worker by name |
| `--state {active,reserved,scheduled,all}` | `all` | Show only tasks in the given state |
| `--limit N` | `10` | Max task rows per worker/state table |
| `--show-payload` | off | Add **Args** and **Kwargs** columns to the task table |
| `--show-task-id` | off | Add **Task ID** column to the task table |

#### Task States

| State | Colour | Meaning |
|-------|--------|---------|
| `active` | green | Currently executing on a worker |
| `reserved` | yellow | Prefetched by a worker, waiting to run |
| `scheduled` | cyan | Deferred via ETA/countdown, not yet ready |

#### Examples

```bash
# Show all workers and all task states (default)
python manage.py celery_worker_report

# Show only active tasks on a specific worker
python manage.py celery_worker_report --worker celery@worker-1 --state active

# Show up to 5 reserved tasks with args/kwargs visible
python manage.py celery_worker_report --state reserved --limit 5 --show-payload

# Show task IDs for debugging
python manage.py celery_worker_report --show-task-id
```

#### When to Use

| Situation | Tool |
|-----------|------|
| Quick terminal check during development | `celery_worker_report` |
| CI/CD health check without browser | `celery_worker_report` |
| Full real-time task stream & history | Flower UI (`localhost:5556`) |
| Broker queue depths & message rates | RabbitMQ UI (`localhost:15672`) |

!!! tip
    The command exits with a non-zero code (`CommandError`) if no workers are reachable or the specified `--worker` is not found — safe to use in scripts and health checks.

---

## Troubleshooting

### Common Issues

#### 1. "Received unregistered task" / `KeyError` on task name

**Cause:** Worker doesn't know about the task function, or the task name in Beat schedule doesn't match the auto-generated name.

This commonly happens when `AppConfig.name = "apps.users"` but the Beat schedule references `"users.my_task"`. Celery auto-generates names from the full module path (`apps.users.tasks.my_task`), so the short name causes a `KeyError`.

**Solution:**

```python
# Always use explicit name= to avoid mismatch
@shared_task(queue="default", bind=True, name="users.cleanup_expired_otp_codes")
def cleanup_expired_otp_codes(self): ...
```

```bash
# Check registered tasks to see actual names
docker compose exec celery_worker celery -A celery_app inspect registered

# Ensure the app is in INSTALLED_APPS
# Ensure tasks.py is in the app directory
# Restart worker after adding tasks
docker compose restart celery_worker
```

#### 2. Worker Connects but No Tasks Execute

**Cause:** Worker is not subscribed to the correct queue.

**Solution:**

```bash
# Check which queues the worker listens to
docker compose exec celery_worker celery -A celery_app inspect active_queues

# Ensure -Q flag includes the task's queue
# command: celery -A celery_app worker -l info -Q default,emails,heavy
```

#### 3. Duplicate Periodic Tasks

**Cause:** Multiple Beat instances running, or stale schedule in database.

**Solution:**

```bash
# Ensure only ONE Beat instance
docker compose ps | grep beat

# Clear stale schedule entries
docker compose exec storefront_catalog_service \
    python manage.py shell -c "
from django_celery_beat.models import PeriodicTask
PeriodicTask.objects.all().delete()
"
# Restart Beat (it will re-sync from settings)
docker compose restart celery_beat
```

#### 4. "Connection refused" to RabbitMQ

**Cause:** RabbitMQ is not ready or broker URL is wrong.

**Solution:**

```bash
# Check RabbitMQ health
docker compose ps rabbitmq

# Verify broker URL
echo $CELERY_BROKER_URL
# Expected: amqp://guest:guest@rabbitmq:5672//

# Check RabbitMQ logs
docker compose logs rabbitmq
```

#### 5. chord Callback Never Fires

**Cause:** `CELERY_RESULT_BACKEND` is `None`. Chords require a result backend to track header task completion.

**Solution:**

```python
# Option 1: Enable Redis result backend
CELERY_RESULT_BACKEND = "redis://redis:6379/0"

# Option 2: Use RPC backend (stores in RabbitMQ)
CELERY_RESULT_BACKEND = "rpc://"
```

!!! note "Our chord demos"
    Our demo chord tasks dispatch correctly because they use `apply_async()` which sends to the broker. For production chords with result tracking, enable a result backend.

#### 6. Tasks Stuck in PENDING

**Cause:** No worker is running, or worker crashed.

**Solution:**

```bash
# Check worker status
docker compose ps celery_worker
docker compose logs celery_worker --tail 50

# Restart worker
docker compose restart celery_worker
```

---

## Best Practices

### 1. Always Use Explicit Task Names

Celery auto-generates task names from the full module path: `apps.users.tasks.cleanup_expired_otp_codes`. If your `AppConfig.name` is `apps.users` (not just `users`), the auto-generated name **won't match** a short name like `users.cleanup_expired_otp_codes` in the Beat schedule — and you'll get a `KeyError: 'users.cleanup_expired_otp_codes'` at runtime.

```python
# ✅ Good: explicit name — you control exactly how Beat and other callers reference it
@shared_task(queue="default", bind=True, name="users.cleanup_expired_otp_codes")
def cleanup_expired_otp_codes(self): ...

@shared_task(queue="default", bind=True, name="services.periodic_test_task")
def periodic_test_task(self): ...

# ❌ Bad: relying on auto-generated name
# Auto-name becomes "apps.users.tasks.cleanup_expired_otp_codes"
# but Beat schedule says "users.cleanup_expired_otp_codes" → KeyError!
@shared_task(queue="default", bind=True)
def cleanup_expired_otp_codes(self): ...
```

Explicit names also protect you from breaking callers when you move a task to a different module or rename the package.

### 2. Keep Tasks Idempotent

```python
# ✅ Good: safe to run multiple times
@shared_task
def cleanup_expired_otp_codes():
    OTPCode.objects.filter(expires_at__lt=timezone.now()).delete()

# ❌ Bad: side effects on re-run
@shared_task
def increment_counter():
    Counter.objects.get(id=1).increment()  # double-counts on retry
```

### 3. Pass IDs, Not Objects

```python
# ✅ Good: pass the ID, fetch fresh data inside task
@shared_task
def process_order(order_id: int):
    order = Order.objects.get(id=order_id)
    # ... process ...

# ❌ Bad: serializing a Django model
@shared_task
def process_order(order: Order):  # Can't serialize Django model to JSON!
    pass
```

### 4. Use Appropriate Queues

```python
# ✅ Good: separate heavy work from fast tasks
@shared_task(queue="heavy")
def generate_report(report_id: int): ...

@shared_task(queue="emails")
def send_notification(user_id: int): ...

# ❌ Bad: everything on default queue
@shared_task(queue="default")
def generate_huge_report(): ...  # blocks other default tasks
```

### 5. Handle Failures with Retries

```python
@shared_task(bind=True, max_retries=3)
def send_sms(self, phone: str, message: str):
    try:
        sms_client.send(phone, message)
    except SMSProviderError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
        # Exponential backoff: 1s, 2s, 4s
```

### 6. Never Run Multiple Beat Instances

Beat does not have leader election. Running two Beat processes means every periodic task fires **twice**.

```bash
# ✅ Correct: single beat service
docker compose up -d celery_beat

# ❌ Wrong: scaling beat
docker compose up -d --scale celery_beat=2  # DON'T!
```

### 7. Use `bind=True` for Task Metadata

```python
@shared_task(bind=True)
def my_task(self):
    print(f"task_id={self.request.id}")
    print(f"retries={self.request.retries}")
    print(f"delivery_info={self.request.delivery_info}")
```
