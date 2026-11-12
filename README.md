# UMNPMSEAC

Proposed Python package framework for spatial permutation analysis of gene categories. It currently loads Visium HD binned outputs or CosMx transcript CSV files into a shared point-pattern table, and provides configuration and job execution support. It does not yet run PMSEAC analysis.

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
    microns_per_pixel=0.18,  # Example only: use the scale documented for your dataset.
)

# If the slide has multiple samples, supply their FOV numbers instead:
points = load_cosmx(
    "/path/to/slide_tx_file.csv.gz",
    fov_to_sample={194: "sample-a", 195: "sample-a", 196: "sample-b", 197: None},
    microns_per_pixel=0.18,  # Example only: use the scale documented for your dataset.
)
```

One call reads one slide's transcript file. Provide either `sample_id` for a single-sample slide or a mapping for **every** FOV on a multi-sample slide; `None` explicitly excludes a FOV. The loader uses global transcript coordinates and gives each retained transcript `count = 1`. The FOV-to-sample mapping and pixel scale must come from the dataset's documentation or sample annotations, not from the FOV number itself.

Controls are kept by default for quality control (QC). Pass `include_controls=False` to remove targets beginning with `FalseCode`, `SystemControl`, `NegPrb`, or `Negative` before producing the point table. These prefixes are not guaranteed for every panel. For a dataset with its own control names, pass `control_targets={"name1", "name2"}` alongside `include_controls=False` to remove exactly those targets instead. The choice affects the reads available to later permutations.
