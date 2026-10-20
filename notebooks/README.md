# Kaggle notebook handoff

`ieee_cis_random_vs_time_reproduction.ipynb` is the standalone source for a **new independent** IEEE-CIS random-versus-chronological comparison. It does not recover the unavailable original notebook or reproduce its claimed historical metrics.

Attach the official IEEE-CIS competition dataset in Kaggle after accepting its rules. Run all cells top-to-bottom. The notebook writes only aggregate metrics and source provenance to `/kaggle/working/ieee_cis_split_comparison.json`; source CSVs are not published by this project.

## Current evidence

The checked-in notebook currently has no saved executed outputs. Its underlying study has separately run successfully on all 590,540 training transactions in GitHub Actions. A Kaggle publication must be authenticated, executed and read back before a public URL or successful Kaggle execution is claimed.

- [Executed full-source GitHub comparison](../docs/research/KAGGLE_FULL_SOURCE_VALIDATION_2026-10-17.md)
- [Method and interpretation](../docs/research/RANDOM_VS_TIME_SPLIT_REPRODUCTION.md)
- [Kaggle operations runbook](../docs/runbooks/KAGGLE_RESEARCH_RUNBOOK.md)
- [Current publication/access status](../docs/RELEASE_STATUS.md)

Keep credentials out of notebook cells, metadata and output. GitHub Actions authentication and local Kaggle authentication are independent. The project uses free CPU execution; paid accelerators and commercial deployment are out of scope.
