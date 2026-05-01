from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

TaskPayload = dict[str, Any]


@dataclass(frozen=True)
class WorkerListPage:
    workers: list[str]
    error: str | None = None


@dataclass(frozen=True)
class WorkerDetail:
    name: str
    pool: str
    concurrency: str
    active_tasks: list[TaskPayload]
    reserved_tasks: list[TaskPayload]
    scheduled_tasks: list[TaskPayload]


@dataclass(frozen=True)
class WorkerDetailPage:
    worker: WorkerDetail | None
    error: str | None = None


@dataclass(frozen=True)
class NormalizedTask:
    id: str
    name: str
    eta: str
    start_or_received: str
    run_time: str
    args_preview: str
    kwargs_preview: str


@dataclass(frozen=True)
class WorkerTaskView:
    name: str
    pool: str
    concurrency: str
    tasks: dict[str, list[NormalizedTask]]


class CeleryWorkersClient:
    def __init__(self, app: Any):
        self.app = app

    def get_workers(self) -> WorkerListPage:
        try:
            inspect = self.app.control.inspect()
            worker_stats = inspect.stats()
        except Exception as exc:
            return WorkerListPage(
                workers=[],
                error=f"Error connecting to Celery: {exc}",
            )

        if worker_stats is None:
            return WorkerListPage(workers=[], error="No workers are currently running")

        return WorkerListPage(workers=list(worker_stats.keys()))

    def get_worker_detail(self, worker_id: str) -> WorkerDetailPage:
        try:
            inspect = self.app.control.inspect(destination=[worker_id])
            worker_stats = inspect.stats()

            if worker_stats is None or worker_id not in worker_stats:
                return WorkerDetailPage(
                    worker=None,
                    error=f"Worker '{worker_id}' not found or not responding",
                )

            stats = worker_stats[worker_id]
            pool = stats.get("pool", {})

            return WorkerDetailPage(
                worker=WorkerDetail(
                    name=worker_id,
                    pool=str(pool.get("implementation", "N/A")),
                    concurrency=str(pool.get("max-concurrency", "N/A")),
                    active_tasks=_get_worker_tasks(inspect.active(), worker_id),
                    reserved_tasks=_get_worker_tasks(inspect.reserved(), worker_id),
                    scheduled_tasks=_get_worker_tasks(inspect.scheduled(), worker_id),
                )
            )
        except Exception as exc:
            return WorkerDetailPage(
                worker=None,
                error=f"Error retrieving worker details: {exc}",
            )


def _get_worker_tasks(result: Any, worker_id: str) -> list[TaskPayload]:
    if not isinstance(result, dict):
        return []
    tasks = result.get(worker_id, [])
    return tasks if isinstance(tasks, list) else []


def safe_preview(value: Any, max_len: int = 80) -> str:
    if value in (None, "", [], {}, ()):
        return "-"

    text = value if isinstance(value, str) else str(value)
    return text if len(text) <= max_len else f"{text[: max_len - 1]}..."


def parse_timestamp(value: Any) -> float | None:
    if value in (None, "", "-", "N/A"):
        return None

    if isinstance(value, int | float):
        parsed = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = float(stripped)
        except ValueError:
            return None
    else:
        return None

    if parsed > 1_000_000_000_000:
        parsed /= 1000.0
    return parsed


def format_timestamp(value: Any) -> str:
    parsed = parse_timestamp(value)
    if parsed is None:
        if isinstance(value, str) and value.strip():
            return value.strip()
        return "-"

    try:
        return datetime.fromtimestamp(parsed, tz=UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    except (OSError, OverflowError, ValueError):
        return str(value)


def format_runtime(seconds: float | None) -> str:
    if seconds is None:
        return "-"

    total = max(int(seconds), 0)
    if total < 60:
        return f"{total}s"
    if total < 3600:
        minutes, secs = divmod(total, 60)
        return f"{minutes}m {secs}s"
    if total < 86400:
        hours, rem = divmod(total, 3600)
        minutes = rem // 60
        return f"{hours}h {minutes:02d}m"

    days, rem = divmod(total, 86400)
    hours = rem // 3600
    return f"{days}d {hours:02d}h"


def normalize_task(
    task: TaskPayload,
    now: datetime | None = None,
) -> NormalizedTask:
    request = task.get("request", task) if isinstance(task, dict) else {}
    eta = request.get("eta") or task.get("eta")
    time_value = request.get("time_start") or request.get("time_received") or "-"
    parsed_start = parse_timestamp(time_value)
    runtime_seconds = None
    if parsed_start is not None:
        current_time = now or datetime.now(UTC)
        runtime_seconds = current_time.timestamp() - parsed_start

    return NormalizedTask(
        id=str(request.get("id") or "-"),
        name=str(request.get("name") or "-"),
        eta=str(eta or "-"),
        start_or_received=format_timestamp(time_value),
        run_time=format_runtime(runtime_seconds),
        args_preview=safe_preview(request.get("argsrepr", request.get("args"))),
        kwargs_preview=safe_preview(request.get("kwargsrepr", request.get("kwargs"))),
    )


def sort_key(task: NormalizedTask) -> tuple[bool, str, str, str]:
    has_eta = task.eta not in ("-", "")
    return not has_eta, task.eta, task.name, task.id


def build_worker_view(
    worker_name: str,
    worker_detail: WorkerDetail,
    now: datetime | None = None,
) -> WorkerTaskView:
    return WorkerTaskView(
        name=worker_name,
        pool=worker_detail.pool,
        concurrency=worker_detail.concurrency,
        tasks={
            "active": [normalize_task(task, now=now) for task in worker_detail.active_tasks],
            "reserved": [normalize_task(task, now=now) for task in worker_detail.reserved_tasks],
            "scheduled": [normalize_task(task, now=now) for task in worker_detail.scheduled_tasks],
        },
    )
