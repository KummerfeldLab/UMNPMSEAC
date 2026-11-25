"""Maximin distances evaluated at observed molecule locations."""

from __future__ import annotations

from collections.abc import Collection, Mapping

import numpy as np
import polars as pl
from scipy.spatial import KDTree

from umnpmseac.input import PointPattern


class AnalysisError(ValueError):
    """The requested score cannot be calculated from these observations."""


SCORE_SCHEMA = pl.Schema(
    {
        "sample_id": pl.String,
        "x_um": pl.Float64,
        "y_um": pl.Float64,
        "maxmin_um": pl.Float64,
    }
)


def score_observed_maxmin(
    points: PointPattern,
    category_genes: Mapping[str, Collection[str]],
) -> pl.DataFrame:
    """Score unique observed positions within each sample.

    At each position, find the nearest detected location for each gene category,
    then return the largest of those distances. Smaller scores mean that all
    categories are nearby. No new positions, permutations, or p-values are made.
    Counts do not change observed distances; they matter when permuting reads.
    """
    if not isinstance(points, PointPattern):
        raise AnalysisError("points must be a PointPattern")
    if not isinstance(category_genes, Mapping) or not category_genes:
        raise AnalysisError("category_genes must be a nonempty mapping")

    categories: dict[str, set[str]] = {}
    for name, genes in category_genes.items():
        if not isinstance(name, str) or not name.strip():
            raise AnalysisError("category names must be nonempty strings")
        if (
            isinstance(genes, (str, bytes))
            or not isinstance(genes, Collection)
            or not genes
            or any(not isinstance(gene, str) or not gene.strip() for gene in genes)
        ):
            raise AnalysisError(f"category {name!r} needs a nonempty collection of gene names")
        categories[name] = set(genes)

    results = []
    for sample_id in points.sample_ids:
        sample = points.for_sample(sample_id)
        query = sample.select("x_um", "y_um").unique().sort("x_um", "y_um")
        query_xy = query.to_numpy()
        maxmin = np.zeros(len(query_xy), dtype=np.float64)

        for name, genes in categories.items():
            targets = sample.filter(pl.col("gene").is_in(genes)).select("x_um", "y_um").unique()
            if targets.is_empty():
                raise AnalysisError(f"sample {sample_id!r} has no detected genes in category {name!r}")
            distances, _ = KDTree(targets.to_numpy()).query(query_xy)
            np.maximum(maxmin, distances, out=maxmin)

        results.append(
            pl.DataFrame(
                {
                    "sample_id": [sample_id] * len(query_xy),
                    "x_um": query["x_um"],
                    "y_um": query["y_um"],
                    "maxmin_um": maxmin,
                },
                schema=SCORE_SCHEMA,
            )
        )
    return pl.concat(results)
