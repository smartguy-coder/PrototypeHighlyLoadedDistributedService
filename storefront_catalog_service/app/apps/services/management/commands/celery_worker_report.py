"""
terminal analog for flower ui
"""

from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand, CommandError

from celery import current_app
from rich.console import Console
from rich.table import Table
from utils.celery import (
    CeleryWorkersClient,
    NormalizedTask,
    WorkerTaskView,
    build_worker_view,
    sort_key,
)


class Command(BaseCommand):
    TASK_STATES = ("active", "reserved", "scheduled")
    STATE_STYLES = {
        "active": "green",
        "reserved": "yellow",
        "scheduled": "cyan",
    }

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--worker",
            dest="worker",
            help="Filter output to a specific worker name",
        )
        parser.add_argument(
            "--state",
            choices=(*self.TASK_STATES, "all"),
            default="all",
            help="Task state to render",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Maximum task rows per worker/state table",
        )
        parser.add_argument(
            "--show-payload",
            action="store_true",
            help="Show args/kwargs columns",
        )
        parser.add_argument(
            "--show-task-id",
            action="store_true",
            help="Show Task ID column",
        )

    def _render_summary(self, console: Console, workers: list[WorkerTaskView]) -> None:
        table = Table(title="Celery Worker Task Summary")
        table.add_column("Worker", style="bold")
        table.add_column("Pool")
        table.add_column("Concurrency", justify="right")
        table.add_column("Active", justify="right", style=self.STATE_STYLES["active"])
        table.add_column("Reserved", justify="right", style=self.STATE_STYLES["reserved"])
        table.add_column("Scheduled", justify="right", style=self.STATE_STYLES["scheduled"])
        table.add_column("Total Known", justify="right")

        for worker in workers:
            active = len(worker.tasks["active"])
            reserved = len(worker.tasks["reserved"])
            scheduled = len(worker.tasks["scheduled"])
            table.add_row(
                worker.name,
                worker.pool,
                worker.concurrency,
                str(active),
                str(reserved),
                str(scheduled),
                str(active + reserved + scheduled),
            )

        console.print(table)

    def _render_task_table(
        self,
        console: Console,
        worker_name: str,
        state: str,
        tasks: list[NormalizedTask],
        limit: int,
        show_payload: bool,
        show_task_id: bool,
    ) -> None:
        style = self.STATE_STYLES[state]
        sorted_tasks = sorted(tasks, key=sort_key)
        shown = sorted_tasks[:limit]

        if not shown:
            console.print(f"[dim]{worker_name} · {state.upper()}: no tasks[/dim]")
            return

        table = Table(title=f"{worker_name} · {state.upper()} ({len(sorted_tasks)})")
        table.add_column("#", justify="right")
        table.add_column("Task", style="bold")
        if show_task_id:
            table.add_column("Task ID")
        table.add_column("ETA", style=style)
        table.add_column("Start/Received")
        table.add_column("Run Time", justify="right")
        if show_payload:
            table.add_column("Args")
            table.add_column("Kwargs")

        for idx, task in enumerate(shown, start=1):
            row = [
                str(idx),
                task.name,
            ]
            if show_task_id:
                row.append(task.id)
            row.extend(
                [
                    task.eta,
                    task.start_or_received,
                    task.run_time,
                ]
            )
            if show_payload:
                row.extend([task.args_preview, task.kwargs_preview])
            table.add_row(*row)

        console.print(table)
        omitted = len(sorted_tasks) - len(shown)
        if omitted > 0:
            console.print(f"[dim]{worker_name} · {state.upper()}: +{omitted} more[/dim]")

    def handle(self, *args: Any, **options: Any) -> None:
        worker_client = CeleryWorkersClient(current_app)
        worker_result = worker_client.get_workers()

        if worker_result.error:
            raise CommandError(f"Could not retrieve worker information: {worker_result.error}")

        workers = sorted(worker_result.workers)
        selected_worker = options.get("worker")
        if selected_worker:
            workers = [worker for worker in workers if worker == selected_worker]
            if not workers:
                raise CommandError(f"Worker '{selected_worker}' not found")

        limit = max(options.get("limit", 10), 1)
        state_option = options.get("state", "all")
        selected_states = list(self.TASK_STATES) if state_option == "all" else [state_option]

        console = Console(no_color=options.get("no_color", False))

        worker_views: list[WorkerTaskView] = []
        worker_errors: list[str] = []
        for worker_name in workers:
            detail_page = worker_client.get_worker_detail(worker_name)
            if detail_page.error or detail_page.worker is None:
                worker_errors.append(f"{worker_name}: {detail_page.error or 'unknown worker detail error'}")
                continue

            worker_views.append(build_worker_view(worker_name, detail_page.worker))

        if not worker_views:
            message = "No worker details available"
            if worker_errors:
                message = f"{message}: {'; '.join(worker_errors)}"
            raise CommandError(message)

        self._render_summary(console, worker_views)
        for worker in worker_views:
            for state in selected_states:
                self._render_task_table(
                    console=console,
                    worker_name=worker.name,
                    state=state,
                    tasks=worker.tasks[state],
                    limit=limit,
                    show_payload=options.get("show_payload", True),
                    show_task_id=options.get("show_task_id", False),
                )

        if worker_errors:
            for worker_error in worker_errors:
                console.print(f"[red]worker detail error[/red] {worker_error}")
