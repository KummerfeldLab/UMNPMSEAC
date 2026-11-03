"""Small submitit-compatible executor for local computers."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(slots=True)
class LocalJob:
    _value: Any = None
    _error: Exception | None = None

    @classmethod
    def call(cls, function: Callable[..., Any], *args: Any, **kwargs: Any) -> "LocalJob":
        try:
            return cls(_value=function(*args, **kwargs))
        except Exception as error:
            return cls(_error=error)

    def result(self) -> Any:
        if self._error is not None:
            raise self._error
        return self._value

    def wait(self) -> Any:
        return self.result()


class LocalExecutor:
    def __init__(self, workers: int = 1) -> None:
        if workers < 1:
            raise ValueError("workers must be positive")
        self.workers = workers

    def update_parameters(self, **_parameters: Any) -> None:
        """Accept the small subset of the submitit interface used by the framework."""

    def submit(self, function: Callable[..., Any], *args: Any, **kwargs: Any) -> LocalJob:
        return LocalJob.call(function, *args, **kwargs)

    def map_array(self, function: Callable[[Any], Any], items: Iterable[Any]) -> list[LocalJob]:
        items = list(items)
        if self.workers == 1:
            return [LocalJob.call(function, item) for item in items]
        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            futures = [pool.submit(function, item) for item in items]
            jobs = []
            for future in futures:
                try:
                    jobs.append(LocalJob(_value=future.result()))
                except Exception as error:
                    jobs.append(LocalJob(_error=error))
            return jobs

    def batch(self):
        return nullcontext()
