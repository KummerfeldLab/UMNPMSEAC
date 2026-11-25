"""Manual full-table numerical check; requires local sample files.

Run from the repository root:
python tests/check_sample_scores.py --data-root ../sample_data
"""

import argparse
import json

import numpy as np
import polars as pl

from umnpmseac import load_cosmx, load_visium_hd, score_observed_maxmin


def check(points, categories):
    scores = score_observed_maxmin(points, categories)
    reports = []
    for sample_id in points.sample_ids:
        sample = points.for_sample(sample_id)
        result = scores.filter(pl.col("sample_id") == sample_id)
        expected_positions = sample.select("x_um", "y_um").unique().sort("x_um", "y_um")
        assert result.select("x_um", "y_um").equals(expected_positions)
        xy = result.select("x_um", "y_um").to_numpy()
        reference = np.zeros(len(xy))
        target_counts = {}
        for name, genes in categories.items():
            # Direct pairwise distances: no KDTree or scorer helper is used.
            targets = sample.filter(pl.col("gene").is_in(genes)).select("x_um", "y_um").unique().to_numpy()
            assert len(targets), (sample_id, name)
            target_counts[name] = len(targets)
            for start in range(0, len(xy), 128):
                query = xy[start:start + 128]
                distances = np.hypot(
                    query[:, None, 0] - targets[None, :, 0],
                    query[:, None, 1] - targets[None, :, 1],
                )
                reference[start:start + len(query)] = np.maximum(
                    reference[start:start + len(query)], distances.min(axis=1)
                )
        actual = result["maxmin_um"].to_numpy()
        np.testing.assert_allclose(actual, reference, rtol=1e-12, atol=1e-12)
        reports.append({
            "sample_id": sample_id,
            "positions_checked": len(xy),
            "category_target_locations": target_counts,
            "max_absolute_error_um": float(np.max(np.abs(actual - reference))),
        })
    return {"categories": categories, "samples": reports}


if __name__ == "__main__":
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    args = parser.parse_args()
    cosmx = load_cosmx(
        args.data_root / "CosMxToy/toy_tx.csv.gz",
        fov_to_sample={fov: f"fov-{fov}" for fov in [194, 195, 196, 197]},
        include_controls=False,
    )
    visium = load_visium_hd(args.data_root / "TinySample", sample_id="tiny-8um", bin_size_um=8)
    report = {
        "comparison": "all scored locations against batched direct Euclidean distances",
        "rtol": 1e-12,
        "atol_um": 1e-12,
        "cosmx": check(cosmx, {
            "SASP": ["IL1B", "IL6", "CXCL12", "CCL2", "CXCL8", "TGFB1", "VEGFA"],
            "EMC": ["PLAUR", "PLAU", "PAPPA", "MMP14", "ADAMTS4", "COL6A1", "THBS1"],
            "Anti_Apoptotic": ["SERPINE1", "SERPINB2", "SERPINE2", "BCL2L1", "MCL1", "BCL2"],
            "Cell_Cycle_Related": ["CDKN1A", "TP53", "GADD45A", "CDKN2A", "GADD45B"],
        }),
        "visium": check(visium, {"mt-Co3": ["mt-Co3"], "mt-Atp6": ["mt-Atp6"]}),
        "limitations": "CosMx FOVs treated as separate technical units; scale unverified for this subset. Visium categories are illustrative mouse genes. Checks reuse loader output and do not independently validate coordinates or biological interpretation.",
    }
    print(json.dumps(report, indent=2))
