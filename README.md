# UMNPMSEAC

Proposed Python package framework for spatial permutation analysis of gene categories. This repository currently contains configuration and job execution support. It does not yet contain an analysis method or a runnable PMSEAC pipeline.

The distribution is named `UMNPMSEAC`; Python imports use `umnpmseac`.

## Development

From this repository, install with `python -m pip install -e .`. For optional SLURM support, use `python -m pip install -e '.[slurm]'`.

See [PACKAGE_DESIGN.md](PACKAGE_DESIGN.md) for the proposed input and method boundaries and the decisions still open to the team.
