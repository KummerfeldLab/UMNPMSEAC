# Observed-location score output

`run_and_save_observed_maxmin(points, category_genes, output_root, run_name="my-run")` calculates scores and creates a new `output_root/my-run/` directory:

```text
my-run/
  scores.parquet
  metadata.json
```

`scores.parquet` is a Polars-readable table with one row for each unique observed coordinate in each sample:

| Column | Type | Meaning |
| --- | --- | --- |
| `sample_id` | string | Sample scored independently. |
| `x_um`, `y_um` | float64 | Observed scoring position in microns. |
| `maxmin_um` | float64 | Largest nearest-category Euclidean distance; smaller means all categories are closer. |

`metadata.json` records the method, scoring-position rule, distance metric, category gene lists, sample IDs, input and output row counts, and the loader settings available on the input `PointPattern`. For CosMx, those settings include the pixel scale, FOV-to-sample mapping, and control-filter choice. For Visium HD, they include the bin size. A manually constructed `PointPattern` may have no loader metadata, which is written as `null`.

The writer does not save the source data or create permutations, p-values, thresholds, or images. Keep the original input files to reproduce a run. It refuses to overwrite an existing run directory.
