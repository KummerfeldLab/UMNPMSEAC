"""Load Visium HD binned outputs produced by 10x Space Ranger."""

from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import polars as pl

from umnpmseac.input import POINT_SCHEMA, PointPattern


class LoaderError(ValueError):
    """A platform input cannot be converted to a point-pattern table."""


def _bin_directory(path: str | Path, bin_size_um: int) -> Path:
    root = Path(path).expanduser()
    if isinstance(bin_size_um, bool) or not isinstance(bin_size_um, int) or bin_size_um < 1:
        raise LoaderError("bin_size_um must be a positive integer")

    bin_name = f"square_{bin_size_um:03d}um"
    candidates = (
        root / "outs" / "binned_outputs" / bin_name,
        root / "binned_outputs" / bin_name,
        root / bin_name,
        root,
    )
    for candidate in candidates:
        matrix_path = candidate / "filtered_feature_bc_matrix.h5"
        positions_path = candidate / "spatial" / "tissue_positions.parquet"
        if matrix_path.is_file() and positions_path.is_file():
            if candidate.name.startswith("square_") and candidate.name != bin_name:
                raise LoaderError(
                    f"{candidate} is {candidate.name}, but bin_size_um={bin_size_um}"
                )
            return candidate

    raise LoaderError(
        f"could not find {bin_name}/filtered_feature_bc_matrix.h5 and "
        f"{bin_name}/spatial/tissue_positions.parquet below {root}"
    )


def _decode(values: np.ndarray) -> np.ndarray:
    """Decode fixed-width HDF5 byte strings into NumPy Unicode strings."""
    return np.asarray(values).astype(str)


def _read_gene_counts(matrix_path: Path) -> pl.DataFrame:
    try:
        with h5py.File(matrix_path, "r") as source:
            matrix = source["matrix"]
            data = np.asarray(matrix["data"])
            feature_indices = np.asarray(matrix["indices"], dtype=np.int64)
            column_offsets = np.asarray(matrix["indptr"], dtype=np.int64)
            barcodes = _decode(matrix["barcodes"][:])
            genes = _decode(matrix["features/name"][:])
            feature_types = _decode(matrix["features/feature_type"][:])
            shape = tuple(int(value) for value in matrix["shape"][:])
    except (OSError, KeyError) as error:
        raise LoaderError(f"cannot read a 10x feature-barcode matrix from {matrix_path}") from error

    if shape != (len(genes), len(barcodes)) or len(column_offsets) != len(barcodes) + 1:
        raise LoaderError(f"inconsistent matrix dimensions in {matrix_path}")
    if len(data) != len(feature_indices) or int(column_offsets[-1]) != len(data):
        raise LoaderError(f"inconsistent sparse-matrix arrays in {matrix_path}")

    barcode_indices = np.repeat(
        np.arange(len(barcodes), dtype=np.int64), np.diff(column_offsets)
    )
    gene_expression = feature_types[feature_indices] == "Gene Expression"
    if not np.any(gene_expression):
        raise LoaderError(f"no Gene Expression counts found in {matrix_path}")

    return pl.DataFrame(
        {
            "barcode": barcodes[barcode_indices[gene_expression]],
            "gene": genes[feature_indices[gene_expression]],
            "count": data[gene_expression],
        }
    ).with_columns(
        pl.col("barcode").cast(pl.String),
        pl.col("gene").cast(pl.String),
        pl.col("count").cast(pl.Int64),
    )


def load_visium_hd(
    path: str | Path,
    *,
    sample_id: str,
    bin_size_um: int = 2,
) -> PointPattern:
    """Load one Visium HD sample from a Space Ranger output directory.

    ``path`` may point to the Space Ranger run, its ``outs`` directory, or a
    specific ``square_XXXum`` directory. Only nonzero Gene Expression counts
    from the filtered feature-barcode matrix are returned.
    """
    if not isinstance(sample_id, str) or not sample_id.strip():
        raise LoaderError("sample_id must be a nonempty string")

    bin_directory = _bin_directory(path, bin_size_um)
    counts = _read_gene_counts(bin_directory / "filtered_feature_bc_matrix.h5")
    positions_path = bin_directory / "spatial" / "tissue_positions.parquet"

    try:
        positions = (
            pl.scan_parquet(positions_path)
            .select("barcode", "in_tissue", "array_row", "array_col")
            .filter(pl.col("in_tissue") == 1)
        )
        joined = counts.lazy().join(positions, on="barcode", how="inner").collect(
            engine="streaming"
        )
    except (OSError, pl.exceptions.PolarsError) as error:
        raise LoaderError(f"cannot read tissue positions from {positions_path}") from error

    expected_barcodes = counts.get_column("barcode").n_unique()
    matched_barcodes = joined.get_column("barcode").n_unique()
    if matched_barcodes != expected_barcodes:
        raise LoaderError(
            f"tissue positions matched {matched_barcodes} of {expected_barcodes} "
            "barcodes with nonzero Gene Expression counts"
        )
    if joined.height != counts.height:
        raise LoaderError("tissue positions must contain exactly one row per barcode")

    table = joined.select(
        pl.lit(sample_id.strip(), dtype=pl.String).alias("sample_id"),
        (pl.col("array_col").cast(pl.Float64) * bin_size_um).alias("x_um"),
        (pl.col("array_row").cast(pl.Float64) * bin_size_um).alias("y_um"),
        pl.col("gene").cast(pl.String),
        pl.col("count").cast(pl.Int64),
    ).cast(POINT_SCHEMA)
    return PointPattern(table)
