# UMNPMSEAC

Proposed Python package framework for spatial permutation analysis of gene categories. It currently loads Visium HD binned outputs or CosMx transcript CSV files into a shared point-pattern table, and provides configuration and job execution support. It has a first observed-location distance scorer, but does not yet run PMSEAC permutations or significance analysis.

The distribution is named `UMNPMSEAC`; Python imports use `umnpmseac`.

## Development

From this repository, install with `python -m pip install -e .`. For optional SLURM support, use `python -m pip install -e '.[slurm]'`.

See [PACKAGE_DESIGN.md](PACKAGE_DESIGN.md) for the proposed flow and [INPUT_CONTRACT.md](INPUT_CONTRACT.md) for the first shared input contract.

## Point-pattern input

The Visium HD loader reads a Space Ranger run and creates the five-column point-pattern table:

```python
from umnpmseac import load_visium_hd

points = load_visium_hd(
    "/path/to/spaceranger-run",
    sample_id="sample-a",
    bin_size_um=2,
)
print(points.sample_ids)          # ('sample-a',)
print(points.counts_per_sample())
print(points.for_sample("sample-a"))
```

The path may also point to the run's `outs` directory or directly to a `square_XXXum` directory.

## CosMx transcript input

```python
from umnpmseac import load_cosmx

points = load_cosmx(
    "/path/to/slide_tx_file.csv.gz",
    sample_id="sample-a",  # Use this when the whole file is one sample.
)

# If the slide has multiple samples, supply their FOV numbers instead:
points = load_cosmx(
    "/path/to/slide_tx_file.csv.gz",
    fov_to_sample={194: "sample-a", 195: "sample-a", 196: "sample-b", 197: None},
)

# Override the default only when your dataset documents a different scale:
points = load_cosmx(
    "/path/to/slide_tx_file.csv.gz",
    sample_id="sample-a",
    microns_per_pixel=0.18,  # Example of a dataset-specific override.
)
```

One call reads one slide's transcript file. Provide either `sample_id` for a single-sample slide or a mapping for **every** FOV on a multi-sample slide; `None` explicitly excludes a FOV. The loader uses global transcript coordinates and gives each retained transcript `count = 1`. The user supplies the FOV-to-sample assignment; the loader does not infer it from FOV numbers. The default pixel scale is **0.12028 µm/pixel**, as documented for a [Bruker CosMx dataset](https://www.brukerspatialbiology.com/wp-content/uploads/2024/11/MK6578_CosMx_Human_Lymph_Node_FFPE_Dataset_webpage.html). A [different public CosMx dataset](https://datadryad.org/dataset/doi:10.5061/dryad.ksn02v7b1) specifies 0.18 µm/pixel, so check your dataset's documentation and pass `microns_per_pixel` if it differs.

Controls are kept by default for quality control (QC). Pass `include_controls=False` to remove targets beginning with `FalseCode`, `SystemControl`, `NegPrb`, or `Negative` before producing the point table. These prefixes are not guaranteed for every panel. For a dataset with its own control names, pass `control_targets={"name1", "name2"}` alongside `include_controls=False` to remove exactly those targets instead. The choice affects the reads available to later permutations.

## First observed-location score

`score_observed_maxmin(points, category_genes)` calculates a preliminary score at each **unique observed location** in each sample. For every category, it finds the distance to the nearest detected gene in that category; the score is the largest of those distances. Smaller values mean all categories are closer. It uses Euclidean distances in microns and requires every category to have a detection in each sample. It does not create scoring locations, run permutations, calculate p-values, or apply edge filtering.

For example, with category A detected at `(0, 0)` and category B at `(10, 0)`, the only scoring locations are those two observed positions. Both have `maxmin_um = 10`. If another gene is detected at `(5, 0)`, that location is also scored and has `maxmin_um = 5`.

Use `run_and_save_observed_maxmin(points, category_genes, output_root, run_name="my-run")` to calculate and save the scores. Pass `config.paths.output_root` as `output_root` when using a TOML config. It creates a new run directory with `scores.parquet` and `metadata.json`; it refuses to replace an existing run. See [OUTPUT_CONTRACT.md](OUTPUT_CONTRACT.md) for the files and fields.
