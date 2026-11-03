# Package structure for discussion

This repository starts with a small framework drawn from the `package` branch of KummerfeldLab/VisHD, which was based on Lee's `uv` branch. It carries over the configuration and local/optional SLURM execution ideas, without copying Lee's analysis modules or Mac's prototypes. No scientific method has been selected.

## Proposed flow

1. Platform readers accept Visium HD or CosMx data and identify samples.
2. Readers produce a common point-oriented input, initially proposed as `(sample, x, y, gene, count)`. Coordinates, units, sample/FOV mapping, and the measured area need metadata.
3. A defined internal representation supplies read positions, category assignments, and locations to score to the chosen method. The exact table(s) still need agreement: Lee currently builds long-form barcode and position tables; Mac's supplied scripts build dense count and distance grids.
4. A method computes observed scores and permutations, then a result layer saves distances, thresholds, optional p-values, and images as chosen by the user.

Blade and edge filtering are outside this first framework. They can be added later, or documented as an optional preparation step.

## Options to define

The team has discussed per-sample or pooled permutations, Euclidean or taxi-cab distance, edge filtering, optional p-values, and output choices. Local execution is the current default; SLURM is optional. We should choose scientific defaults and validate them against representative data before adding analysis methods. A memory estimate could suggest a different distance method, while making clear that a metric change can change results.

SaTScan is a related example of spatial permutation-based inference, not an implementation of this method.
