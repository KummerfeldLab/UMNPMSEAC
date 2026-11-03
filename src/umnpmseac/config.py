"""Explicit, machine-specific settings supplied by the user."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib
from typing import Literal, Mapping, Any


class ConfigError(ValueError):
    """Invalid package configuration."""


@dataclass(frozen=True, slots=True)
class PathConfig:
    input_root: Path
    output_root: Path


@dataclass(frozen=True, slots=True)
class SlurmConfig:
    account: str
    memory_gb: int = 64
    cpus: int = 4
    time_limit: str = "06:00:00"
    partition: str | None = None

    def __post_init__(self) -> None:
        if not self.account.strip():
            raise ConfigError("execution.slurm.account cannot be empty")
        if self.memory_gb < 1 or self.cpus < 1:
            raise ConfigError("SLURM memory_gb and cpus must be positive")


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    backend: Literal["local", "slurm"] = "local"
    workers: int = 1
    slurm: SlurmConfig | None = None

    def __post_init__(self) -> None:
        if self.backend not in {"local", "slurm"}:
            raise ConfigError("execution.backend must be 'local' or 'slurm'")
        if self.workers < 1:
            raise ConfigError("execution.workers must be positive")
        if self.backend == "slurm" and self.slurm is None:
            raise ConfigError("execution.slurm is required for the SLURM backend")


@dataclass(frozen=True, slots=True)
class UMNPMSEACConfig:
    paths: PathConfig
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)


def _check_keys(section: str, values: Mapping[str, Any], allowed: set[str]) -> None:
    unknown = set(values) - allowed
    if unknown:
        raise ConfigError(f"unknown key(s) in [{section}]: {', '.join(sorted(unknown))}")


def _path(value: Any, base: Path, name: str) -> Path:
    if not isinstance(value, str):
        raise ConfigError(f"{name} must be a path string")
    path = Path(value).expanduser()
    return path if path.is_absolute() else (base / path).resolve()


def load_config(path: str | Path) -> UMNPMSEACConfig:
    """Read TOML; resolve relative data paths against the TOML file's directory."""
    config_path = Path(path).expanduser().resolve()
    with config_path.open("rb") as source:
        raw = tomllib.load(source)

    _check_keys("root", raw, {"paths", "execution"})
    paths_raw = raw.get("paths")
    if not isinstance(paths_raw, dict):
        raise ConfigError("a [paths] section is required")
    _check_keys("paths", paths_raw, {"input_root", "output_root"})
    for name in ("input_root", "output_root"):
        if name not in paths_raw:
            raise ConfigError(f"paths.{name} is required")
    paths = PathConfig(
        input_root=_path(paths_raw["input_root"], config_path.parent, "paths.input_root"),
        output_root=_path(paths_raw["output_root"], config_path.parent, "paths.output_root"),
    )

    execution_raw = raw.get("execution", {})
    if not isinstance(execution_raw, dict):
        raise ConfigError("[execution] must be a table")
    _check_keys("execution", execution_raw, {"backend", "workers", "slurm"})
    slurm_raw = execution_raw.get("slurm")
    slurm = None
    if slurm_raw is not None:
        if not isinstance(slurm_raw, dict):
            raise ConfigError("[execution.slurm] must be a table")
        _check_keys("execution.slurm", slurm_raw, {"account", "memory_gb", "cpus", "time_limit", "partition"})
        try:
            slurm = SlurmConfig(**slurm_raw)
        except TypeError as error:
            raise ConfigError(f"invalid [execution.slurm] settings: {error}") from error
    execution = ExecutionConfig(
        backend=execution_raw.get("backend", "local"),
        workers=execution_raw.get("workers", 1),
        slurm=slurm,
    )
    return UMNPMSEACConfig(paths=paths, execution=execution)
