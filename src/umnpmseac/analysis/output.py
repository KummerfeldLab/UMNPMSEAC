"""Save one observed-location score run and its basic provenance."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import asdict
import json
from pathlib import Path
import re

from umnpmseac.analysis.observed import score_observed_maxmin
from umnpmseac.input import PointPattern


def run_and_save_observed_maxmin(
    points: PointPattern,
    category_genes: Mapping[str, Collection[str]],
    output_root: str | Path,
    *,
    run_name: str,
) -> Path:
    """Write ``scores.parquet`` and ``metadata.json`` under a new run directory.

    The directory must not already exist, so an earlier run is never replaced.
    Pass ``config.paths.output_root`` as ``output_root`` when using a config.
    """
    if not isinstance(run_name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", run_name):
        raise ValueError("run_name must use letters, digits, dots, hyphens, or underscores")

    root = Path(output_root).expanduser()
    run_dir = root / run_name
    if run_dir.exists():
        raise FileExistsError(f"result directory already exists: {run_dir}")

    scores = score_observed_maxmin(points, category_genes)
    run_dir.mkdir(parents=True, exist_ok=False)

    scores.write_parquet(run_dir / "scores.parquet")
    metadata = {
        "schema_version": 1,
        "method": "observed_maxmin",
        "scoring_positions": "unique observed locations from all retained genes, within each sample",
        "distance_metric": "euclidean",
        "distance_unit": "micron",
        "category_genes": {
            name: sorted(set(genes)) for name, genes in sorted(category_genes.items())
        },
        "input": {
            "loader": asdict(points.metadata) if points.metadata is not None else None,
            "sample_ids": list(points.sample_ids),
            "observation_rows": points.table.height,
            "molecule_count": sum(points.counts_per_sample().values()),
        },
        "result": {"file": "scores.parquet", "row_count": scores.height},
        "permutations": 0,
    }
    (run_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return run_dir
