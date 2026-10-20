# Kaggle notebooks

| Notebook | Role and evidence |
|---|---|
| [Independent comparison](ieee_cis_random_vs_time_reproduction.ipynb) | Maintained 150-estimator random/chronological study, with aggregate tables, charts, source digest and environment versions |
| [Recovered original](archive/original_ieee_cis_leakage.ipynb) | Unchanged 600-estimator historical source; previous provider execution was recovered, not rerun |

Provider links and measured status are recorded in [Kaggle recovery evidence](../docs/research/KAGGLE_RECOVERY_2026-10-20.md). The original is public and reports COMPLETE. The independent companion is also public and COMPLETE; aggregate metrics and both figures were downloaded and inspected on 20 October 2026.

## Reproduce the maintained companion

Attach the official IEEE-CIS competition dataset and accept its rules. Run all notebook cells top-to-bottom, or use `kaggle kernels push -p notebooks` with authenticated credentials. [kernel-metadata.json](kernel-metadata.json) selects free CPU execution, no GPU/TPU, no notebook internet, and the official competition source.

The notebook writes aggregate metrics/source provenance and two comparison figures to `/kaggle/working/`. Raw CSVs, transaction-level results and credentials are not exported. Its full-source assertions prohibit labeling a smoke subset as a full-data result.

The embedded analysis is checked against `scripts/compare_random_time_holdout.py` by an AST equivalence regression. Publication and execution do not promote the study into the separately published dashboard model. The recovered original has stronger causal/customer wording and different preprocessing; retain the limitations in the recovery report when citing it.

See [research methods](../docs/research/RANDOM_VS_TIME_SPLIT_REPRODUCTION.md), [canonical F03/F04 evidence](../docs/research/KAGGLE_CANONICAL_STABLE_RESEARCH_2026-10-17.md), [Kaggle runbook](../docs/runbooks/KAGGLE_RESEARCH_RUNBOOK.md) and [release status](../docs/RELEASE_STATUS.md).
