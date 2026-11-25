import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import polars as pl

from umnpmseac import (
    AnalysisError,
    load_config,
    load_cosmx,
    run_and_save_observed_maxmin,
)


class ResultOutputTests(unittest.TestCase):
    def test_saves_scores_and_run_metadata_under_configured_output_root(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transcript_file = root / "tx_file.csv"
            transcript_file.write_text(
                "fov,x_global_px,y_global_px,target\n"
                "1,0,0,A\n"
                "1,10,0,B\n"
            )
            config_file = root / "settings.toml"
            config_file.write_text(
                '[paths]\ninput_root = "."\noutput_root = "results"\n'
            )
            config = load_config(config_file)
            points = load_cosmx(transcript_file, sample_id="sample-a", microns_per_pixel=0.18)

            run_dir = run_and_save_observed_maxmin(
                points,
                {"B": ["B"], "A": ["A"]},
                config.paths.output_root,
                run_name="first-run",
            )

            self.assertEqual(run_dir.resolve(), (root / "results" / "first-run").resolve())
            scores = pl.read_parquet(run_dir / "scores.parquet")
            for score in scores["maxmin_um"].to_list():
                self.assertAlmostEqual(score, 1.8)
            metadata = json.loads((run_dir / "metadata.json").read_text())
            self.assertEqual(metadata["category_genes"], {"A": ["A"], "B": ["B"]})
            self.assertEqual(metadata["input"]["loader"]["microns_per_pixel"], 0.18)
            self.assertEqual(metadata["input"]["loader"]["source_format"], "cosmx")
            self.assertEqual(metadata["input"]["loader"]["fov_to_sample"], [["1", "sample-a"]])
            self.assertTrue(metadata["input"]["loader"]["include_controls"])
            self.assertEqual(metadata["scoring_positions"], "unique observed locations from all retained genes, within each sample")
            self.assertEqual(metadata["distance_metric"], "euclidean")
            self.assertEqual(metadata["result"]["row_count"], 2)

            with self.assertRaises(FileExistsError):
                run_and_save_observed_maxmin(
                    points, {"A": ["A"], "B": ["B"]},
                    config.paths.output_root, run_name="first-run",
                )
            self.assertTrue(pl.read_parquet(run_dir / "scores.parquet").equals(scores))

    def test_invalid_name_and_missing_category_create_no_output(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            transcript_file = root / "tx_file.csv"
            transcript_file.write_text(
                "fov,x_global_px,y_global_px,target\n1,0,0,A\n"
            )
            points = load_cosmx(transcript_file, sample_id="sample-a")
            output_root = root / "results"

            with self.assertRaisesRegex(ValueError, "run_name"):
                run_and_save_observed_maxmin(
                    points, {"A": ["A"]}, output_root, run_name="../escape"
                )
            with self.assertRaisesRegex(AnalysisError, "category 'B'"):
                run_and_save_observed_maxmin(
                    points, {"A": ["A"], "B": ["B"]},
                    output_root, run_name="missing-category",
                )
            self.assertFalse(output_root.exists())


if __name__ == "__main__":
    unittest.main()
