# UMNPMSEAC

Proposed Python package framework for spatial permutation analysis of gene categories. It currently loads Visium HD binned outputs, validates a shared point-pattern table, and provides configuration and job execution support. It does not yet load CosMx files or run PMSEAC analysis.

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

The path may also point to the run's `outs` directory or directly to a `square_XXXum` directory. A CosMx loader is the next thing.
