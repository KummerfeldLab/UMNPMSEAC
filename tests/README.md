# Tests

Run the automated tests from the repository root with:

```sh
python -m unittest discover -s tests -q
```

The twenty-one tests use small, generated inputs:

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
| `test_cosmx_loader.py` | Transcript FOVs map to samples, pixel coordinates convert to microns, and individual detections keep `count = 1`. |
| `test_cosmx_loader.py` | A single-sample slide can use one sample ID without listing FOVs. |
| `test_cosmx_loader.py` | The default CosMx pixel scale is 0.12028 µm/pixel and can be overridden. |
| `test_cosmx_loader.py` | Unmapped FOVs are rejected instead of silently dropped. |
| `test_cosmx_loader.py` | An invalid pixel scale or missing required transcript columns are rejected. |
| `test_cosmx_loader.py` | CosMx control targets are kept by default, removed by known prefixes when requested, or removed by an exact user-supplied list. |
| `test_observed_score.py` | A-at-0/B-at-10 scores only the two observed locations, including when counts repeat. |
| `test_observed_score.py` | A midpoint is scored only when another molecule is observed there. |
| `test_observed_score.py` | Scores are calculated separately for each sample. |
| `test_observed_score.py` | A sample missing a requested category raises a clear error. |
| `test_result_output.py` | A run saves readable Parquet scores and JSON metadata under the configured output root, including categories and loader scale. |
| `test_result_output.py` | Existing run directories, unsafe names, and missing categories do not overwrite or create results. |

The local 10x TinySample check described in `INPUT_CONTRACT.md` was run separately. It is not part of this automated test suite.
The public CosMx subset check described there was also run separately; the downloaded file is not in this repository.
