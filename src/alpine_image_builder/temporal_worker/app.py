"""Temporal worker entrypoint for the alpine-image-builder activity fleet.

This module is used to start workers that execute build activities.
The external project (orchestrator) defines workflows that call these
activities by name; it does NOT import this package.

Usage:
    python -m alpine_image_builder.temporal_worker [OPTIONS]
"""

import asyncio
import logging
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import click

from .._yaml import ConfigError

if TYPE_CHECKING:
    from temporalio.client import Client
    from temporalio.worker import Worker

logger = logging.getLogger(__name__)

DEFAULT_TASK_QUEUE = "alpine-image-build"


def _get_activities() -> list[Callable[..., Any]]:
    """Import and return the activity functions.

    Deferred so that the module can be imported without ``temporalio``
    installed (e.g. for the CLI entrypoint generation).
    """
    from .activities import build_image, discover_build_catalog  # noqa: PLC0415

    return [build_image, discover_build_catalog]


async def _run_worker(
    *,
    task_queue: str,
    temporal_host: str,
    max_concurrent_activities: int,
) -> None:
    """Start a Temporal worker that executes build activities."""
    try:
        from temporalio.client import Client
        from temporalio.worker import Worker
    except ModuleNotFoundError as exc:
        raise ConfigError(
            "temporalio is not installed. Install with: "
            "pip install 'alpine-image-builder[temporal]'"
        ) from exc

    client = await Client.connect(temporal_host)
    worker = Worker(
        client,
        task_queue=task_queue,
        activities=_get_activities(),
        max_concurrent_activities=max_concurrent_activities,
    )
    logger.info(
        "Starting alpine-image-builder worker on task queue '%s' "
        "with %d concurrent activity slots (temporal=%s)",
        task_queue,
        max_concurrent_activities,
        temporal_host,
    )
    await worker.run()


@click.command(help="Start a Temporal worker for alpine-image-builder activities")
@click.option(
    "--task-queue",
    default=DEFAULT_TASK_QUEUE,
    show_default=True,
    help="Task queue to listen on",
)
@click.option(
    "--temporal-host",
    default=lambda: os.environ.get("TEMPORAL_HOST", "localhost:7233"),
    show_default=True,
    help="Temporal server address (falls back to TEMPORAL_HOST env var)",
)
@click.option(
    "--max-concurrent-activities",
    default=1,
    show_default=True,
    type=int,
    help="Maximum concurrent build activities (Packer is resource-intensive)",
)
@click.option(
    "--log-level",
    default="INFO",
    show_default=True,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
    help="Logging level",
)
def main(
    task_queue: str,
    temporal_host: str,
    max_concurrent_activities: int,
    log_level: str,
) -> None:
    """Start a Temporal worker that executes build activities.

    The external project (orchestrator) defines workflows that call these
    activities by name; it does NOT import this package.
    """
    logging.basicConfig(level=getattr(logging, log_level.upper()))
    asyncio.run(
        _run_worker(
            task_queue=task_queue,
            temporal_host=temporal_host,
            max_concurrent_activities=max_concurrent_activities,
        )
    )
