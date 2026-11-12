# Point-pattern input contract

The first version accepts one table of detected gene counts at spatial coordinates. An *input loader* is package code that converts platform files into this table. Visium HD and CosMx loaders are implemented.

| Column | Polars type | Meaning |
| --- | --- | --- |
| `sample_id` | string | Sample containing the observation. |
| `x_um` | float64 | x coordinate in microns, consistent within the sample. |
| `y_um` | float64 | y coordinate in microns, consistent within the sample. |
| `gene` | string | Detected gene or target name. |
| `count` | int64 | Positive number of detected molecules at this position. |

For example, a Visium HD sample could produce this table:

| sample_id | x_um | y_um | gene | count |
| --- | ---: | ---: | --- | ---: |
| sample-a | 8.0 | 4.0 | IL6 | 3 |
| sample-a | 10.0 | 6.0 | CDKN1A | 2 |

The first row means that three IL6 molecules were detected at one bin position. These example rows come from the small test fixture, not from a biological sample.

Every row must have a nonempty sample ID and gene, finite coordinates, and a positive integer count. The table must contain at least one observation. Rows for different samples can share coordinates because each sample has its own coordinate system.

CosMx transcript detections typically have `count = 1`. A Visium HD bin can have `count > 1`; the input loader should use the bin's centre coordinate and keep its count in one row. Repeated rows with the same sample, coordinates, and gene are allowed: their counts still represent distinct detected molecules. Downstream permutation code must respect `count` as multiplicity.

For Visium HD, the loader converts the array row and column to microns using the selected bin size. The coordinate origin is arbitrary, but distances between bins are preserved.

For CosMx, `load_cosmx` reads one slide's `tx_file.csv` or `tx_file.csv.gz`. It requires `fov`, `target`, `x_global_px`, and `y_global_px`; other transcript columns are ignored. For a single-sample slide, the user supplies one `sample_id`. For a multi-sample slide, the user maps every FOV to a sample ID (or explicitly excludes it with `None`). The loader scales global pixel coordinates using a required dataset-specific microns-per-pixel value and assigns `count = 1` to each transcript. The shared five-column signature does not change. The loader does not infer biological sample identity or pixel scale.

The loader keeps control targets by default. Set `include_controls=False` to remove targets with names beginning `FalseCode`, `SystemControl`, `NegPrb`, or `Negative`. This is a case-sensitive name rule, not a universal CosMx control catalog. Users can instead supply exact dataset-specific names with `control_targets={...}` and `include_controls=False`. Removal happens before the point table is returned, so it changes which reads are available to downstream permutations.

This version uses observed points as its spatial input. It does not require a separate bin, cell-centre, grid, or tissue-boundary table.

`umnpmseac.PointPattern` validates a Polars DataFrame against this contract. It exposes the validated table, the sample IDs, per-sample tables, and total counts per sample. These are the inputs on which analysis methods can build without creating a Python object for every observation.

I loaded the [10x Visium HD example data](https://www.10xgenomics.com/support/software/space-ranger/latest/resources/visium-hd-example-data) at 2, 8, and 16 µm. Each load produced the five columns and types above, and its total `count` matched the source HDF5 matrix. This was a manual check of the loader and input format, not a test of the PMSEAC analysis.

I also loaded a [public 2.7 MB CosMx transcript subset](https://github.com/dcjones/proseg/issues/149) with 110,683 detections across four FOVs. Assigning FOVs 194–195 to one demonstration sample and 196–197 to another produced 110,683 five-column rows, with per-sample counts of 67,575 and 43,108. Setting `include_controls=False` removed 528 control rows, leaving 110,155 rows. The sample grouping and 0.18 µm/pixel scale used for this structural check are illustrative; the subset does not document either one, so this does not verify biological sample identity or physical distances.
