# Point-pattern input contract

The first version accepts one table of detected gene counts at spatial coordinates. An *input loader* is package code that converts platform files into this table. The Visium HD loader is implemented; a CosMx loader is still planned.

| Column | Polars type | Meaning |
| --- | --- | --- |
| `sample_id` | string | Sample containing the observation. |
| `x_um` | float64 | Sample-relative x coordinate in microns. |
| `y_um` | float64 | Sample-relative y coordinate in microns. |
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

This version uses observed points as its spatial input. It does not require a separate bin, cell-centre, grid, or tissue-boundary table.

`umnpmseac.PointPattern` validates a Polars DataFrame against this contract. It exposes the validated table, the sample IDs, per-sample tables, and total counts per sample. These are the inputs on which analysis methods can build without creating a Python object for every observation.

I loaded the [10x Visium HD example data](https://www.10xgenomics.com/support/software/space-ranger/latest/resources/visium-hd-example-data) at 2, 8, and 16 µm. Each load produced the five columns and types above, and its total `count` matched the source HDF5 matrix. This was a manual check of the loader and input format, not a test of the PMSEAC analysis.
