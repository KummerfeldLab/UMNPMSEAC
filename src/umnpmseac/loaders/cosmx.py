"""Load one CosMx transcript export into the shared point-pattern table."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from math import isfinite
from pathlib import Path

import polars as pl

from umnpmseac.input import InputMetadata, POINT_SCHEMA, PointPattern
from umnpmseac.loaders.errors import LoaderError


CONTROL_PREFIXES = ("FalseCode", "SystemControl", "NegPrb", "Negative")


def load_cosmx(
    path: str | Path,
    *,
    microns_per_pixel: float = 0.12028,
    sample_id: str | None = None,
    fov_to_sample: Mapping[int | str, str | None] | None = None,
    include_controls: bool = True,
    control_targets: Collection[str] | None = None,
) -> PointPattern:
    """Load a single-slide CosMx ``tx_file.csv`` or ``tx_file.csv.gz``.

    For a single-sample slide, provide ``sample_id``. For a multi-sample slide,
    map every FOV to a sample ID; map a FOV to ``None`` to exclude it.
    For example, fov_to_sample={194: "sample-a", 195: "sample-a", 196: "sample-b"}
    says FOVs 194 and 195 belong to one sample, and 196 to another.

    The default pixel scale is 0.12028 microns per pixel. Override it when
    the dataset documents a different scale. Every retained transcript
    contributes one molecule at its global position.
    Set ``include_controls=False`` to remove targets whose names begin with
    FalseCode, SystemControl, NegPrb, or Negative. Supply ``control_targets``
    to remove an exact dataset-specific list instead. Controls are kept by
    default.
    """
    source = Path(path).expanduser()
    if not source.is_file():
        raise LoaderError(f"CosMx transcript file not found: {source}")
    if (
        isinstance(microns_per_pixel, bool)
        or not isinstance(microns_per_pixel, (int, float))
        or not isfinite(microns_per_pixel)
        or microns_per_pixel <= 0
    ):
        raise LoaderError("microns_per_pixel must be a finite positive number")
    if (sample_id is None) == (fov_to_sample is None):
        raise LoaderError("provide exactly one of sample_id or fov_to_sample")
    if not isinstance(include_controls, bool):
        raise LoaderError("include_controls must be a boolean")
    if control_targets is not None:
        if include_controls:
            raise LoaderError("control_targets requires include_controls=False")
        if (
            isinstance(control_targets, (str, bytes))
            or not isinstance(control_targets, Collection)
            or not control_targets
            or any(not isinstance(name, str) or not name.strip() for name in control_targets)
        ):
            raise LoaderError("control_targets must be a nonempty collection of target names")
    if sample_id is not None and (not isinstance(sample_id, str) or not sample_id.strip()):
        raise LoaderError("sample_id must be a nonempty string")
    if fov_to_sample is not None and (
        not isinstance(fov_to_sample, Mapping) or not fov_to_sample
    ):
        raise LoaderError("fov_to_sample must map each FOV to a sample ID or None")

    mapping: dict[str, str | None] = {}
    for fov, mapped_sample in (fov_to_sample or {}).items():
        if isinstance(fov, bool) or not isinstance(fov, (int, str)) or not str(fov).strip():
            raise LoaderError("FOV IDs must be nonempty integers or strings")
        key = str(fov).strip()
        if key in mapping:
            raise LoaderError(f"duplicate FOV mapping: {key}")
        if mapped_sample is not None and (
            not isinstance(mapped_sample, str) or not mapped_sample.strip()
        ):
            raise LoaderError(f"sample ID for FOV {key} must be nonempty or None")
        mapping[key] = mapped_sample.strip() if mapped_sample is not None else None

    required = {"fov", "x_global_px", "y_global_px", "target"}
    try:
        transcripts = pl.scan_csv(source, schema_overrides={"fov": pl.String})
        missing = required.difference(transcripts.collect_schema().names())
        if missing:
            raise LoaderError(f"CosMx transcript file is missing: {', '.join(sorted(missing))}")
        selected = transcripts.select(*sorted(required)).collect(engine="streaming")
    except (OSError, pl.exceptions.PolarsError) as error:
        raise LoaderError(f"cannot read CosMx transcripts from {source}") from error

    observed_fovs = set(selected.get_column("fov").unique().to_list())
    if None in observed_fovs:
        raise LoaderError("CosMx transcripts contain a missing FOV")
    if sample_id is not None:
        mapping = {fov: sample_id.strip() for fov in observed_fovs}
    unmapped = observed_fovs.difference(mapping)
    if unmapped:
        raise LoaderError(f"FOVs missing from fov_to_sample: {', '.join(sorted(unmapped))}")

    if not include_controls:
        if control_targets is None:
            is_control = pl.any_horizontal(
                [
                    pl.col("target").str.starts_with(prefix).fill_null(False)
                    for prefix in CONTROL_PREFIXES
                ]
            )
        else:
            names = [name.strip() for name in control_targets]
            is_control = pl.col("target").is_in(names).fill_null(False)
        selected = selected.filter(~is_control)

    fov_table = pl.DataFrame(
        {"fov": list(mapping), "sample_id": list(mapping.values())},
        schema={"fov": pl.String, "sample_id": pl.String},
    )
    table = (
        selected.join(fov_table, on="fov", how="left")
        .filter(pl.col("sample_id").is_not_null())
        .select(
            pl.col("sample_id"),
            (pl.col("x_global_px").cast(pl.Float64) * microns_per_pixel).alias("x_um"),
            (pl.col("y_global_px").cast(pl.Float64) * microns_per_pixel).alias("y_um"),
            pl.col("target").cast(pl.String).alias("gene"),
            pl.lit(1, dtype=pl.Int64).alias("count"),
        )
        .cast(POINT_SCHEMA)
    )
    if table.is_empty():
        raise LoaderError("no transcripts remain after FOV and control selection")
    return PointPattern(
        table,
        InputMetadata(
            "cosmx",
            microns_per_pixel=microns_per_pixel,
            fov_to_sample=tuple(sorted(mapping.items())),
            include_controls=include_controls,
            control_targets=tuple(sorted(control_targets)) if control_targets is not None else None,
        ),
    )
