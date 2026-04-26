from decouple import config
from kombu import Queue

CELERY_TASK_QUEUES = (
    Queue("default"),
    Queue("emails"),
    Queue("heavy"),
)

CELERY_TASK_DEFAULT_QUEUE = "default"

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="amqp://guest:guest@rabbitmq:5672//")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_BACKEND = None  # or Redis, if needed

CELERY_TIMEZONE = "UTC"

# The task is acknowledged by the broker only after execution completes.
# If the worker crashes — the task will be returned to the queue instead of being lost.
CELERY_TASK_ACKS_LATE = True

# The worker picks up only 1 task at a time (important for heavy/long-running tasks).
CELERY_WORKER_PREFETCH_MULTIPLIER = 1

# Enables real-time visibility of the STARTED state (useful for debugging).
CELERY_TASK_TRACK_STARTED = True

CELERY_TASK_PUBLISH_RETRY = True

CELERY_TASK_PUBLISH_RETRY_POLICY = {
    "max_retries": 10,
    "interval_start": 0,
    "interval_step": 0.5,
    "interval_max": 3,
}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# ============================================================================
# Celery Beat — periodic tasks
# ============================================================================
# The schedule is synced to the DB on beat startup and is visible in Django Admin → Periodic Tasks.
CELERY_BEAT_SCHEDULE = {
    "periodic-test-every-minute": {
        "task": "services.periodic_test_task",
        "schedule": 60.0,  # seconds (every minute)
        "options": {"queue": "default"},
    },
    "cleanup-expired-otp-codes-every-5-min": {
        "task": "users.cleanup_expired_otp_codes",
        "schedule": 300.0,  # every 5 minutes
        "options": {"queue": "default"},
    },
}
