"""
Management command: clickhouse_logs_stats

Reads log statistics from ClickHouse and optionally inserts a test record.
Uses the ClickHouse HTTP interface (port 8123) — no extra dependencies needed.

Usage:
    # Show stats for the last 24 hours
    python manage.py clickhouse_logs_stats

    # Custom time window
    python manage.py clickhouse_logs_stats --hours 48

    # Show top errors
    python manage.py clickhouse_logs_stats --top-errors 20

    # Also insert a test record to verify writes work
    python manage.py clickhouse_logs_stats --insert-test

    # Custom ClickHouse host (default: localhost)
    python manage.py clickhouse_logs_stats --host clickhouse --port 8123
"""

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from datetime import UTC, datetime
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from rich.console import Console
from rich.rule import Rule
from rich.table import Table

# ============================================================================
# ClickHouse HTTP client (zero extra deps — plain urllib)
# ============================================================================


class ClickHouseClient:
    """Minimal synchronous ClickHouse client over the HTTP interface.

    Supports SELECT (returns list[dict]) and INSERT (posts raw data).
    All queries use JSONEachRow format for easy Python parsing.
    """

    def __init__(
        self,
        host: str,
        port: int,
        database: str = "default",
        user: str = "default",
        password: str = "",  # nosec B107
    ) -> None:
        self._base = f"http://{host}:{port}/"
        self._database = database
        self._user = user
        self._password = password

    def _request(self, sql: str, data: bytes | None = None) -> str:
        params = urllib.parse.urlencode(
            {
                "database": self._database,
                "default_format": "JSONEachRow",
                "user": self._user,
                "password": self._password,
            }
        )
        url = f"{self._base}?{params}"
        req = urllib.request.Request(  # noqa: S310
            url,
            data=data if data is not None else sql.encode(),
            headers={"Content-Type": "text/plain"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310  # nosec B310
                result: str = resp.read().decode()
                return result
        except urllib.error.HTTPError as exc:
            body = exc.read().decode()
            raise CommandError(f"ClickHouse HTTP {exc.code}: {body}") from exc
        except OSError as exc:
            raise CommandError(f"Cannot reach ClickHouse at {self._base}: {exc}") from exc

    def select(self, sql: str) -> list[dict[str, Any]]:
        """Execute a SELECT and return rows as a list of dicts."""
        raw = self._request(sql)
        if not raw.strip():
            return []
        return [json.loads(line) for line in raw.strip().splitlines()]

    def execute(self, sql: str) -> None:
        """Execute a non-SELECT statement (INSERT, CREATE, etc.)."""
        self._request(sql)

    def insert_rows(self, table: str, rows: list[dict[str, Any]]) -> None:
        """Insert a list of dicts into *table* using JSONEachRow format."""
        payload = "\n".join(json.dumps(row, default=str) for row in rows)
        sql_prefix = f"INSERT INTO {table} FORMAT JSONEachRow\n"
        self._request(sql_prefix, data=(sql_prefix + payload).encode())


# ============================================================================
# Management command
# ============================================================================


class Command(BaseCommand):
    help = "Show ClickHouse logs statistics via the HTTP API (no extra deps)"

    # ------------------------------------------------------------------ args
    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--host",
            default=os.getenv("CLICKHOUSE_HOST", "localhost"),
            help="ClickHouse host (default: $CLICKHOUSE_HOST or 'localhost')",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            help="ClickHouse HTTP port (default: $CLICKHOUSE_PORT or 8123)",
        )
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help="Look-back window in hours (default: 24)",
        )
        parser.add_argument(
            "--top-errors",
            type=int,
            default=10,
            dest="top_errors",
            help="How many top error messages to show (default: 10)",
        )
        parser.add_argument(
            "--password",
            default=os.getenv("CLICKHOUSE_PASSWORD", ""),
            help="ClickHouse password (default: $CLICKHOUSE_PASSWORD)",
        )
        parser.add_argument(
            "--user",
            default=os.getenv("CLICKHOUSE_USER", "default"),
            help="ClickHouse user (default: $CLICKHOUSE_USER or 'default')",
        )

        parser.add_argument(
            "--insert-test",
            action="store_true",
            default=False,
            dest="insert_test",
            help="Insert a test audit record to verify writes work",
        )

    # ----------------------------------------------------------------- handle
    def handle(self, *args: Any, **options: Any) -> None:
        host: str = options["host"]
        port: int = options["port"]
        hours: int = options["hours"]
        top_errors: int = options["top_errors"]
        insert_test: bool = options["insert_test"]
        user: str = options["user"]
        password: str = options["password"]

        console = Console(no_color=options.get("no_color", False))
        ch = ClickHouseClient(host=host, port=port, user=user, password=password)

        console.print(Rule(f"[bold cyan]ClickHouse logs · last {hours}h[/bold cyan]"))
        console.print(f"[dim]endpoint: http://{host}:{port}/  table: default.logs[/dim]\n")

        # ── 0. Quick connectivity check ──────────────────────────────────────
        try:
            ch.select("SELECT 1")
        except CommandError as exc:
            raise CommandError(str(exc)) from exc

        # ── 1. Totals by log level ───────────────────────────────────────────
        self._render_level_summary(console, ch, hours)

        # ── 2. Breakdown by service ──────────────────────────────────────────
        self._render_by_service(console, ch, hours)

        # ── 3. Breakdown by log_type ─────────────────────────────────────────
        self._render_by_log_type(console, ch, hours)

        # ── 4. Errors per hour (sparkline) ───────────────────────────────────
        self._render_errors_per_hour(console, ch, hours)

        # ── 5. Top error messages ─────────────────────────────────────────────
        self._render_top_errors(console, ch, hours, top_errors)

        # ── 6. Recent exceptions ──────────────────────────────────────────────
        self._render_recent_exceptions(console, ch)

        # ── 7. Optional: write a test record ─────────────────────────────────
        if insert_test:
            self._insert_test_record(console, ch)

    # ================================================================= sections

    def _render_level_summary(self, console: Console, ch: ClickHouseClient, hours: int) -> None:
        rows = ch.select(f"""
            SELECT
                level,
                count()                                          AS total,
                countIf(toDate(timestamp) = today())            AS today,
                round(count() * 100.0 / sum(count()) OVER (), 1) AS pct
            FROM default.logs
            WHERE timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY level
            ORDER BY total DESC
        """)

        table = Table(title=f"Log counts by level (last {hours}h)", show_lines=False)
        table.add_column("Level", style="bold")
        table.add_column("Total", justify="right")
        table.add_column("Today", justify="right")
        table.add_column("%", justify="right", style="dim")

        _LEVEL_STYLES = {"ERROR": "red", "WARNING": "yellow", "INFO": "green", "DEBUG": "dim"}
        for r in rows:
            level = r.get("level", "?")
            table.add_row(
                f"[{_LEVEL_STYLES.get(level, '')}]{level}[/]",
                str(r.get("total", 0)),
                str(r.get("today", 0)),
                f"{r.get('pct', 0)}%",
            )

        console.print(table)
        console.print()

    def _render_by_service(self, console: Console, ch: ClickHouseClient, hours: int) -> None:
        rows = ch.select(f"""
            SELECT
                service,
                count()                                 AS total,
                countIf(level = 'ERROR')                AS errors,
                countIf(level = 'WARNING')              AS warnings,
                max(timestamp)                          AS last_seen
            FROM default.logs
            WHERE timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY service
            ORDER BY total DESC
            LIMIT 20
        """)

        if not rows:
            console.print("[dim]No data for service breakdown[/dim]\n")
            return

        table = Table(title="By service", show_lines=False)
        table.add_column("Service", style="bold cyan")
        table.add_column("Total", justify="right")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Warnings", justify="right", style="yellow")
        table.add_column("Last seen", style="dim")

        for r in rows:
            table.add_row(
                r.get("service") or "[dim]—[/dim]",
                str(r.get("total", 0)),
                str(r.get("errors", 0)),
                str(r.get("warnings", 0)),
                str(r.get("last_seen", "")),
            )

        console.print(table)
        console.print()

    def _render_by_log_type(self, console: Console, ch: ClickHouseClient, hours: int) -> None:
        rows = ch.select(f"""
            SELECT
                log_type,
                count()  AS total,
                countIf(level = 'ERROR') AS errors
            FROM default.logs
            WHERE timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY log_type
            ORDER BY total DESC
        """)

        if not rows:
            console.print("[dim]No data for log_type breakdown[/dim]\n")
            return

        table = Table(title="By log_type (TTL bucket)", show_lines=False)
        table.add_column("log_type", style="bold magenta")
        table.add_column("Total", justify="right")
        table.add_column("Errors", justify="right", style="red")

        _TTL = {"app": "14d", "error": "30d", "audit": "60d"}
        for r in rows:
            lt = r.get("log_type") or "?"
            table.add_row(
                f"{lt} [dim]({_TTL.get(lt, '?')} TTL)[/dim]",
                str(r.get("total", 0)),
                str(r.get("errors", 0)),
            )

        console.print(table)
        console.print()

    def _render_errors_per_hour(self, console: Console, ch: ClickHouseClient, hours: int) -> None:
        rows = ch.select(f"""
            SELECT
                toStartOfHour(timestamp) AS hour,
                countIf(level = 'ERROR')   AS errors,
                countIf(level = 'WARNING') AS warnings,
                count()                    AS total
            FROM default.logs
            WHERE timestamp >= now() - INTERVAL {hours} HOUR
            GROUP BY hour
            ORDER BY hour ASC
        """)

        if not rows:
            console.print("[dim]No hourly data[/dim]\n")
            return

        table = Table(title=f"Errors/warnings per hour (last {hours}h)", show_lines=False)
        table.add_column("Hour", style="dim")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Warnings", justify="right", style="yellow")
        table.add_column("Total", justify="right")
        table.add_column("Bar", no_wrap=True)

        max_total = max((int(r.get("total", 0)) for r in rows), default=1)
        for r in rows:
            total = int(r.get("total", 0))
            bar_len = int(total / max_total * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            table.add_row(
                str(r.get("hour", "")),
                str(r.get("errors", 0)),
                str(r.get("warnings", 0)),
                str(total),
                f"[cyan]{bar}[/cyan]",
            )

        console.print(table)
        console.print()

    def _render_top_errors(self, console: Console, ch: ClickHouseClient, hours: int, limit: int) -> None:
        rows = ch.select(f"""
            SELECT
                message,
                logger,
                count() AS occurrences,
                max(timestamp) AS last_seen
            FROM default.logs
            WHERE
                timestamp >= now() - INTERVAL {hours} HOUR
                AND level = 'ERROR'
            GROUP BY message, logger
            ORDER BY occurrences DESC
            LIMIT {limit}
        """)

        if not rows:
            console.print(f"[green]✓ No errors in the last {hours}h[/green]\n")
            return

        table = Table(title=f"Top {limit} error messages", show_lines=True)
        table.add_column("#", justify="right", style="dim", width=3)
        table.add_column("Message", style="red", max_width=60)
        table.add_column("Logger", style="dim", max_width=35)
        table.add_column("Count", justify="right")
        table.add_column("Last seen", style="dim")

        for idx, r in enumerate(rows, 1):
            table.add_row(
                str(idx),
                r.get("message") or "—",
                r.get("logger") or "—",
                str(r.get("occurrences", 0)),
                str(r.get("last_seen", "")),
            )

        console.print(table)
        console.print()

    def _render_recent_exceptions(self, console: Console, ch: ClickHouseClient) -> None:
        rows = ch.select("""
            SELECT
                timestamp,
                service,
                message,
                exception
            FROM default.logs
            WHERE
                exception != ''
                AND timestamp >= now() - INTERVAL 24 HOUR
            ORDER BY timestamp DESC
            LIMIT 5
        """)

        if not rows:
            console.print("[green]✓ No exceptions in the last 24h[/green]\n")
            return

        console.print(Rule("[bold red]Recent exceptions (last 24h)[/bold red]"))
        for r in rows:
            console.print(
                f"[dim]{r.get('timestamp')}[/dim]  [cyan]{r.get('service')}[/cyan]  [bold]{r.get('message')}[/bold]"
            )
            exc = (r.get("exception") or "").strip()
            if exc:
                # Show only the last 5 lines of the traceback
                lines = exc.splitlines()
                preview = "\n".join(lines[-5:])
                console.print(f"[dim]{preview}[/dim]")
            console.print()

    # ============================================================ write demo

    def _insert_test_record(self, console: Console, ch: ClickHouseClient) -> None:
        """Insert a synthetic audit record directly via HTTP INSERT.

        Demonstrates that the service CAN write to ClickHouse directly
        (not only via stdout → Vector pipeline).
        """
        console.print(Rule("[bold yellow]Write test — direct INSERT[/bold yellow]"))

        now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        record = {
            "timestamp": now,
            "environment": os.getenv("ENVIRONMENT", "production"),
            "service": "storefront-catalog-service",
            "host": socket.gethostname(),
            "level": "INFO",
            "log_type": "audit",
            "logger": "apps.services.management.commands.clickhouse_logs_stats",
            "trace_id": "",
            "span_id": "",
            "user_id": None,
            "request_id": "",
            "message": "clickhouse_logs_stats management command executed",
            "exception": "",
            "extra": json.dumps({"source": "direct_insert", "via": "http_api"}),
        }

        ch.insert_rows("default.logs", [record])

        console.print("[green]✓ Test record inserted successfully[/green]")
        console.print(f"  timestamp : [cyan]{now}[/cyan]")
        console.print("  log_type  : [magenta]audit[/magenta]")
        console.print("  message   : clickhouse_logs_stats management command executed")
        console.print()
        console.print(
            "[dim]Verify: SELECT * FROM default.logs WHERE message LIKE '%clickhouse_logs_stats%' "
            "ORDER BY timestamp DESC LIMIT 1[/dim]"
        )
        console.print()
