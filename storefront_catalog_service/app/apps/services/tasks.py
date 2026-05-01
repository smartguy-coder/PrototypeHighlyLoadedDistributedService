from __future__ import annotations

import logging
from datetime import UTC, datetime

from celery import Task, chain, chord, shared_task
from utils.celery import CeleryQueueEnum

logger = logging.getLogger(__name__)


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True)
def simple_task(self: Task[..., None]) -> None:
    logger.info("[simple_task] started | task_id=%s retries=%s", self.request.id, self.request.retries)
    logger.info("[simple_task] finished successfully | task_id=%s", self.request.id)


@shared_task(queue=CeleryQueueEnum.EMAILS)
def send_email() -> None:
    logger.info("[send_email] started")


@shared_task(queue=CeleryQueueEnum.HEAVY)
def heavy_task() -> None:
    logger.info("[heavy_task] started — will crash")


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True, name="services.periodic_test_task")
def periodic_test_task(self: Task[..., None]) -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    logger.info(
        "[periodic_test_task] ✔ tick | task_id=%s time=%s retries=%s", self.request.id, now, self.request.retries
    )
    logger.info("[periodic_test_task] done | task_id=%s", self.request.id)


# ============================================================================
# Primitive tasks — building blocks for chain / chord demos
# ============================================================================


@shared_task(queue=CeleryQueueEnum.DEFAULT)
def add(x: int, y: int) -> int:
    """Return the sum of two integers.

    Used as a building block in chain/chord demonstrations.
    Accepts the result of a previous task as the first argument
    when connected via `.s()` (immutable=False) signatures.
    """
    result = x + y
    logger.info("[add] %s + %s = %s", x, y, result)
    return result


@shared_task(queue=CeleryQueueEnum.DEFAULT)
def multiply(x: int, y: int) -> int:
    """Return the product of two integers.

    Works the same way as `add` — can receive the upstream
    result as the first positional arg in a chain.
    """
    result = x * y
    logger.info("[multiply] %s * %s = %s", x, y, result)
    return result


@shared_task(queue=CeleryQueueEnum.DEFAULT)
def aggregate(results: list[int]) -> int:
    """Sum a list of integers.

    Designed as the *callback* (final step) of a chord:
    receives a list of return values from all header tasks.
    """
    total = sum(results)
    logger.info("[aggregate] sum(%s) = %s", results, total)
    return total


# ============================================================================
# Chain demos — sequential pipeline of tasks
# ============================================================================


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True)
def demo_chain_with_s(self: Task[..., None]) -> None:
    """Demonstrate `chain` using mutable signatures (`.s()`).

    Pipeline: add(2, 3) -> multiply(prev, 10) -> add(prev, 100)

    `.s()` (== `.signature()`) creates a *mutable* signature:
    the return value of the previous task is **prepended** to the
    argument list of the next task.  So the intermediate calls are:
      1. add(2, 3)          → 5
      2. multiply(5, 10)    → 50   (5 is injected as first arg)
      3. add(50, 100)       → 150  (50 is injected as first arg)
    """
    pipeline = chain(
        add.s(2, 3),  # -> 5
        multiply.s(10),  # prev=5  -> 5 * 10 = 50
        add.s(100),  # prev=50 -> 50 + 100 = 150
    )
    result = pipeline.apply_async()
    logger.info("[demo_chain_with_s] dispatched chain | root_id=%s", result.id)


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True)
def demo_chain_with_si(self: Task[..., None]) -> None:
    """Demonstrate `chain` using immutable signatures (`.si()`).

    Pipeline: add(2, 3) | multiply(4, 5) | add(10, 20)

    `.si()` (== `.signature(immutable=True)`) creates an *immutable*
    signature: the return value of the previous task is **ignored**
    (not passed to the next task).  Each task receives only the
    arguments explicitly provided.

    Use case: when tasks must run sequentially but are *logically
    independent* (e.g., step-by-step migrations, ordered side-effects).
    """
    pipeline = chain(
        add.si(2, 3),  # -> 5   (result discarded by next step)
        multiply.si(4, 5),  # -> 20  (does NOT receive 5)
        add.si(10, 20),  # -> 30  (does NOT receive 20)
    )
    result = pipeline.apply_async()
    logger.info("[demo_chain_with_si] dispatched chain | root_id=%s", result.id)


# ============================================================================
# Chord demos — parallel header + final callback
# ============================================================================


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True)
def demo_chord_with_s(self: Task[..., None]) -> None:
    """Demonstrate `chord` using mutable signatures (`.s()`).

    Header (parallel):  add(1,2), add(3,4), add(5,6)
    Callback:           aggregate(results)

    All header tasks run in parallel.  When every header task
    finishes, Celery collects their return values into a list
    and passes that list as the first argument to the callback
    (`aggregate`).  Because the callback uses `.s()`, the list
    is injected automatically:
      aggregate([3, 7, 11]) → 21
    """
    task_group = chord(
        [add.s(1, 2), add.s(3, 4), add.s(5, 6)],  # header — parallel
        aggregate.s(),  # callback — receives [3, 7, 11]
    )
    result = task_group.apply_async()
    logger.info("[demo_chord_with_s] dispatched chord | root_id=%s", result.id)


@shared_task(queue=CeleryQueueEnum.DEFAULT, bind=True)
def demo_chord_with_si(self: Task[..., None]) -> None:
    """Demonstrate `chord` using immutable signatures (`.si()`).

    Header (parallel):  add(1,2), add(3,4), add(5,6)
    Callback:           multiply(10, 20)

    The header tasks still run in parallel, but the callback uses
    `.si()` so it **ignores** the collected results.  This is useful
    when you need to wait for a group to complete before firing
    a final task that doesn't depend on their output (e.g., sending
    a notification, updating a status flag).

    multiply(10, 20) → 200  (header results are discarded)
    """
    task_group = chord(
        [add.s(1, 2), add.s(3, 4), add.s(5, 6)],  # header — parallel
        multiply.si(10, 20),  # callback — ignores header results
    )
    result = task_group.apply_async()
    logger.info("[demo_chord_with_si] dispatched chord | root_id=%s", result.id)
