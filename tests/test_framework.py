from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from umnpmseac import ConfigError, ExecutionConfig, load_config
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


if __name__ == "__main__":
    unittest.main()
