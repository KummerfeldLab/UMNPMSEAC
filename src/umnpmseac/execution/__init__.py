"""Local and optional SLURM job execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from umnpmseac.config import ExecutionConfig
from umnpmseac.execution.local_backend import LocalExecutor


def make_executor(config: ExecutionConfig, log_dir: str | Path) -> Any:
    if config.backend == "local":
        return LocalExecutor(workers=config.workers)
    from umnpmseac.execution.slurm import make_slurm_executor

    return make_slurm_executor(config, log_dir)


__all__ = ["LocalExecutor", "make_executor"]
