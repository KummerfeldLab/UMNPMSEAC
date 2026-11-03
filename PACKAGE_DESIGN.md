# Package structure for discussion

This repository starts with a small framework drawn from the `package` branch of KummerfeldLab/VisHD, which was based on Lee's `uv` branch. It carries over the configuration and local/optional SLURM execution ideas, without copying Lee's analysis modules or Mac's prototypes. No scientific method has been selected.

## Proposed flow

1. Package input loaders accept Visium HD or CosMx data and identify samples. The first implemented loader reads Visium HD binned Space Ranger outputs; CosMx sample/FOV mapping remains to be defined.
2. The input loaders produce the shared point-pattern table `(sample_id, x_um, y_um, gene, count)`.
3. Analysis methods map genes to categories and convert the table into the representation they need. Lee's method can build coordinate arrays and KD-trees; Mac's method can build dense count and distance grids.
4. A result layer saves distances, thresholds, optional p-values, and images as chosen by the user.

Blade and edge filtering are outside this first framework. They can be added later, or documented as an optional preparation step.

We have discussed per-sample or pooled permutations, Euclidean or taxi-cab distance, optional p-values, and output choices. We could offer defaults for permutation pooling and distance metric, since these affect results. Edge filtering (BLADE) is deferred for now. Local execution is the current default; SLURM is optional and GPU execution is still pending.

KD-tree queries (Lee) and dense-grid distance transforms (Mac) are two ways to calculate distances. I think Mac had suggested a KD-tree might suit large CosMx samples where a dense grid would need downsampling or too much memory - a benchmark test we could run later(?) to decide when to use which. A memory warning could suggest another approach – changing the distance metric should be presented separately because it can change the result.

## Options to define
For the input contract, the five columns above are sufficient for the first point-pattern version. Platform loaders may use Visium barcodes, CosMx FOV IDs, bin size, and image transforms while preparing that table. A later analysis method will define which observed points it scores.
