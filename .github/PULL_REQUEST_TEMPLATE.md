## What changed and why

<!-- Describe the change and the motivation. Include the milestone or issue reference. -->

## Pipeline / schema affected

<!-- Which pipeline(s) and schema(s) are touched? (e.g. pr_<n>_medallion_pipeline, sdp_dev) -->

## Validation steps run

- [ ] `ruff check .` passed locally
- [ ] `pytest` passed locally
- [ ] Bundle deployed (`databricks bundle deploy`)
- [ ] Pipeline executed (`databricks bundle run`)
- [ ] Row counts validated (`python scripts/validate_counts.py`)

## Databricks run screenshot

<!-- Paste a screenshot of the completed pipeline run from the Databricks UI. -->

