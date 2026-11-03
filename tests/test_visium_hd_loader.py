from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import h5py
import numpy as np
import polars as pl

from umnpmseac import LoaderError, load_visium_hd


def write_visium_fixture(root: Path, *, omit_second_position: bool = False) -> None:
    bin_directory = root / "outs" / "binned_outputs" / "square_002um"
    positions_directory = bin_directory / "spatial"
    positions_directory.mkdir(parents=True)

    with h5py.File(bin_directory / "filtered_feature_bc_matrix.h5", "w") as target:
        matrix = target.create_group("matrix")
        matrix.create_dataset("barcodes", data=np.array([b"bin-a", b"bin-b"]))
        matrix.create_dataset("data", data=np.array([3, 1, 2], dtype=np.int32))
        matrix.create_dataset("indices", data=np.array([0, 2, 1], dtype=np.int64))
        matrix.create_dataset("indptr", data=np.array([0, 2, 3], dtype=np.int64))
        matrix.create_dataset("shape", data=np.array([3, 2], dtype=np.int32))
        features = matrix.create_group("features")
        features.create_dataset("name", data=np.array([b"IL6", b"CDKN1A", b"CD3"]))
        features.create_dataset(
            "feature_type",
            data=np.array([b"Gene Expression", b"Gene Expression", b"Antibody Capture"]),
        )

    barcodes = ["bin-a"] if omit_second_position else ["bin-a", "bin-b"]
    pl.DataFrame(
        {
            "barcode": barcodes,
            "in_tissue": [1] * len(barcodes),
            "array_row": [2, 3][: len(barcodes)],
            "array_col": [4, 5][: len(barcodes)],
        }
    ).write_parquet(positions_directory / "tissue_positions.parquet")


class VisiumHDLoaderTests(unittest.TestCase):
    def test_loads_gene_counts_and_joins_bin_coordinates(self):
        with TemporaryDirectory() as directory:
            run = Path(directory) / "sample-run"
            write_visium_fixture(run)
            points = load_visium_hd(run, sample_id="sample-a")

            self.assertEqual(points.sample_ids, ("sample-a",))
            self.assertEqual(points.counts_per_sample(), {"sample-a": 5})
            self.assertEqual(points.table["gene"].to_list(), ["IL6", "CDKN1A"])
            self.assertEqual(points.table["x_um"].to_list(), [8.0, 10.0])
            self.assertEqual(points.table["y_um"].to_list(), [4.0, 6.0])

    def test_rejects_counts_without_matching_tissue_positions(self):
        with TemporaryDirectory() as directory:
            run = Path(directory) / "sample-run"
            write_visium_fixture(run, omit_second_position=True)
            with self.assertRaisesRegex(LoaderError, "matched 1 of 2"):
                load_visium_hd(run, sample_id="sample-a")


if __name__ == "__main__":
    unittest.main()
