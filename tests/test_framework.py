from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import polars as pl

from umnpmseac import (
    ConfigError,
    ExecutionConfig,
    InputContractError,
    POINT_SCHEMA,
    PointPattern,
    load_config,
)
from umnpmseac.execution import LocalExecutor, make_executor


def square(value: int) -> int:
    return value * value


class FrameworkTests(unittest.TestCase):
    def test_config_resolves_paths_and_defaults_to_local(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            path.write_text('[paths]\ninput_root = "data"\noutput_root = "results"\n')
            config = load_config(path)
            root = Path(directory).resolve()
            self.assertEqual(config.paths.input_root, root / "data")
            self.assertEqual(config.paths.output_root, root / "results")
            self.assertEqual(config.execution, ExecutionConfig())

    def test_slurm_requires_settings(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "settings.toml"
            path.write_text('[paths]\ninput_root = "data"\noutput_root = "results"\n[execution]\nbackend = "slurm"\n')
            with self.assertRaisesRegex(ConfigError, "execution.slurm is required"):
                load_config(path)

    def test_local_executor(self):
        executor = make_executor(ExecutionConfig(), "unused")
        self.assertIsInstance(executor, LocalExecutor)
        self.assertEqual(executor.submit(square, 4).result(), 16)
        self.assertEqual([job.result() for job in executor.map_array(square, [1, 2])], [1, 4])

    def test_local_parallel_jobs_preserve_order(self):
        jobs = LocalExecutor(workers=2).map_array(square, [3, 1, 2])
        self.assertEqual([job.result() for job in jobs], [9, 1, 4])

    def test_point_pattern_preserves_sample_coordinates_and_count_weights(self):
        table = pl.DataFrame(
            {
                "sample_id": ["visium-a", "visium-a", "cosmx-b"],
                "x_um": [2.0, 2.0, 2.0],
                "y_um": [4.0, 4.0, 4.0],
                "gene": ["IL6", "IL6", "CDKN1A"],
                "count": [3, 2, 1],
            },
            schema=POINT_SCHEMA,
        )
        points = PointPattern(table)
        self.assertEqual(points.sample_ids, ("cosmx-b", "visium-a"))
        self.assertEqual(points.counts_per_sample(), {"visium-a": 5, "cosmx-b": 1})
        self.assertEqual(points.for_sample("visium-a")["count"].to_list(), [3, 2])
        self.assertEqual(points.for_sample("cosmx-b")["x_um"].to_list(), [2.0])

    def test_point_pattern_rejects_invalid_counts_and_coordinates(self):
        for name, values, message in (
            ("count", [0], "positive integers"),
            ("x_um", [float("nan")], "finite coordinates"),
            ("gene", ["  "], "cannot be blank"),
        ):
            columns = {
                "sample_id": ["sample-a"],
                "x_um": [2.0],
                "y_um": [4.0],
                "gene": ["IL6"],
                "count": [1],
            }
            columns[name] = values
            with self.subTest(name=name), self.assertRaisesRegex(InputContractError, message):
                PointPattern(pl.DataFrame(columns, schema=POINT_SCHEMA))

    def test_point_pattern_rejects_wrong_schema_and_nulls(self):
        with self.assertRaisesRegex(InputContractError, "table must have"):
            PointPattern(pl.DataFrame({"sample_id": ["sample-a"]}))
        with self.assertRaisesRegex(InputContractError, "cannot contain null"):
            PointPattern(pl.DataFrame({
                "sample_id": ["sample-a"], "x_um": [None], "y_um": [4.0],
                "gene": ["IL6"], "count": [1],
            }, schema=POINT_SCHEMA))


if __name__ == "__main__":
    unittest.main()
