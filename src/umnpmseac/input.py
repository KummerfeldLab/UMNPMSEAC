"""The platform-independent point-pattern input contract."""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


POINT_SCHEMA = pl.Schema(
    {
        "sample_id": pl.String,
        "x_um": pl.Float64,
        "y_um": pl.Float64,
        "gene": pl.String,
        "count": pl.Int64,
    }
)


class InputContractError(ValueError):
    """A point-pattern table does not satisfy the shared input contract."""


@dataclass(frozen=True, slots=True)
class PointPattern:
    """Validated observations with sample-relative micron coordinates.

    ``table`` remains columnar; counts are not expanded into individual rows.
    """

    table: pl.DataFrame

    def __post_init__(self) -> None:
        table = self.table
        if not isinstance(table, pl.DataFrame):
            raise InputContractError("input must be a polars.DataFrame")
        if table.schema != POINT_SCHEMA:
            raise InputContractError(
                "table must have sample_id, x_um, y_um, gene, count "
                "with string, float64, float64, string, int64 types"
            )
        if table.is_empty():
            raise InputContractError("table must contain at least one observation")

        for name in POINT_SCHEMA.names():
            if table.get_column(name).null_count():
                raise InputContractError(f"{name} cannot contain null values")
        for name in ("sample_id", "gene"):
            if table.select(pl.col(name).str.strip_chars().eq("").any()).item():
                raise InputContractError(f"{name} cannot be blank")
        for name in ("x_um", "y_um"):
            if table.select((~pl.col(name).is_finite()).any()).item():
                raise InputContractError(f"{name} must contain finite coordinates")
        if table.select(pl.col("count").le(0).any()).item():
            raise InputContractError("count must contain positive integers")

    @property
    def sample_ids(self) -> tuple[str, ...]:
        """Sample identifiers present in the observations."""
        return tuple(self.table.get_column("sample_id").unique().sort().to_list())

    def for_sample(self, sample_id: str) -> pl.DataFrame:
        """Five-column observations for one sample, preserving count weights."""
        selected = self.table.filter(pl.col("sample_id") == sample_id)
        if selected.is_empty():
            raise KeyError(f"unknown sample_id: {sample_id}")
        return selected

    def counts_per_sample(self) -> dict[str, int]:
        """Total molecule counts without expanding rows."""
        totals = self.table.group_by("sample_id").agg(pl.col("count").sum())
        return dict(totals.iter_rows())
