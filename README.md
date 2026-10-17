# Graph Network Attributions Track Atom Degree Before Training

Code and materials accompanying the manuscript.

Talha Kırca, Hasan Yıldırım, Merve Görgülü — Department of Data Science and Analytics,
Karamanoğlu Mehmetbey University.

## What is here

```
manuscript/     main.tex, supporting.tex, references.bib, figures/, tables/
                check_consistency.py — pre-submission checks
notebooks/      the pipeline, 22 notebooks, in run order
data/           the three source tables, 7,255 compounds
manifest_stage_inputs.csv
results.zip, explain.zip, models_*.zip — the stored artefacts, see below
```

## Archives

The stored artefacts are committed as archives because of the upload size limit. Unpack
them beside `data/`, `manuscript/` and `notebooks/`, so that the pipeline finds them where
it expects:

| Archive | Unpacks to | Holds |
| --- | --- | --- |
| `results.zip` | `results/` | the fold assignments, the selected hyperparameter configurations and every result file the analyses wrote |
| `explain.zip` | `explain/` | atom-level attribution scores for the graph models |
| `models_gin.zip` | `models/` | the twenty GIN attribution models and the five fitted on each corrected partition |
| `models_gat.zip` | `models/` | the twenty GAT attribution models |
| `models_gcn1.zip`, `models_gcn2.zip` | `models/` | the twenty GCN attribution models, split across two archives |

The four `models_*` archives unpack into the same `models/` folder.

The designated partition is in `results/primary_train.csv`, `primary_valid.csv` and
`primary_test.csv`: 5,804, 725 and 726 compounds, 55.6%, 53.7% and 46.3% mutagenic.

## Still to be added

- `requirements.txt` — from `pip freeze` in the environment that ran the pipeline
- `manifest.csv` — see below

The atom-level TreeSHAP values were not retained, which the manuscript states.

## The data

`data/` holds `train.csv`, `valid.csv` and `test.csv`: 7,255 compounds, 54.5% mutagenic,
no unparseable structure and no duplicate on the canonical SMILES.

The split inside these three files is **not** the partition the analyses use. Part 1
concatenates them and draws its own scaffold partition with `PRIMARY_SPLIT_SEED = 101`,
giving 5,804 training, 725 validation and 726 test compounds. Anyone reproducing the
results should take the designated partition from `results/primary_*.csv` rather than
from the split in `data/`.

## Running the pipeline

Every notebook expects `WORK = "/content/drive/MyDrive/ames_pipeline"` with `data/`,
`results/`, `models/` and `explain/` beneath it. Run order and the dependency between
parts are in `notebooks/README.md`.

Versions are not pinned in the notebooks. The recorded environment is rdkit 2026.03.5
and torch_geometric 2.8.0.

## The manifest

`manifest_stage_inputs.csv` maps each of 122 result files to the notebook that produced
it and to the files that notebook read. It fills the `stage` and `inputs` columns of the
manifest the manuscript describes; `seed` and the file hashes are added when the manifest
is generated against the populated repository.

## Known gaps

Three defects in the pipeline, none of which affects a published value:

1. Part 12 does not compute `r_with_degree_overlap` for GIN, so that cell of
   `tab_architectures` is empty. The published value is 0.824.
2. Part 16 records `n = 1` for the random ranking in `table77_auroc.csv`. Twenty
   independent rankings were drawn; the published value is 20.
3. Part 17 computes `table88_regimes_by_partition.csv` but does not write it: its
   `cached()` helper refuses a frame whose note column is non-empty.

The LaTeX fragments under `manuscript/tables/` were written by a rendering stage that is
not in this repository. All 38 of them use a float convention (`table`, `[htbp]`) that none of
the notebooks here produces, so none came from this code as it stands. `part20` rebuilds
seven of them from the stored results, five byte for byte against the shipped copy; the
numbers in all of them are in `manuscript/tables/manuscript_numbers.csv`.

## Verification

From `manuscript/`:

```
python3 check_consistency.py
```

It checks the prose against `tables/manuscript_numbers.csv`, the 854 quantities quoted
in the text, and reports placeholders, cross-document references and unreferenced floats.
Bare integers in the prose are outside its scope.
