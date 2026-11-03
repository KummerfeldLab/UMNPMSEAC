# Tests

Run the automated tests from the repository root with:

```sh
python -m unittest discover -s tests -q
```

The nine tests use small, generated inputs:

| File | What the tests check |
| --- | --- |
| `test_framework.py` | Config paths resolve relative to the config file, and local execution is the default. |
| `test_framework.py` | SLURM settings are required when SLURM is selected. |
| `test_framework.py` | Local job submission and mapping return the expected results. |
| `test_framework.py` | Parallel local jobs return results in input order. |
| `test_framework.py` | A valid point-pattern table preserves sample IDs, coordinates, and count weights. |
| `test_framework.py` | Zero counts, nonfinite coordinates, and blank gene names are rejected. |
| `test_framework.py` | An incorrect schema or null values are rejected. |
| `test_visium_hd_loader.py` | Visium HD counts join to bin positions, keep gene-expression features, and produce the expected coordinates and counts. |
| `test_visium_hd_loader.py` | A count barcode without a matching tissue position is rejected. |

The local 10x TinySample check described in `INPUT_CONTRACT.md` was run separately. It is not part of this automated test suite.
