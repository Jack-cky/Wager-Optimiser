# Changelog

## [3.1.1] - 2026-08-16

Updated the new season schedule and migrated the database away from the unstable host.

### Added
- Added a `make pull` target to fetch the pipeline image explicitly before execution.

### Changed
- Updated the GitHub Actions pipeline workflow to pull the image first, then run the pipeline without re-triggering Docker image pulls during execution.
- Adjusted the Makefile workflow to separate image retrieval from pipeline execution for more reliable scheduled runs.
- Switched the application database from MySQL to TiDB after the previous host, Layerbase, proved unstable and unreliable.

### Fixed
- Stabilised the weekly pipeline schedule by avoiding the race-prone `--pull missing` behaviour and reducing intermittent deployment failures.

## [3.0.1] - 2026-07-26

Rebuilt the project as an end-to-end MLOps workflow with a Dagster pipeline and a Taipy simulator.

### Added
- Orchestrated the weekly workflow with Dagster assets: ingestion, cleansing, feature engineering, publishing, monitoring, training, and deployment.
- Added drift detection with NannyML, gating retraining on detected degeneration.
- Added champion/challenger model promotion via MLflow aliases on the Unity Catalog registry, serving the champion from a Databricks endpoint.
- Added operational metrics and simulator usage telemetry pushed to Grafana Cloud.
- Added Docker Compose services with a Makefile wrapper and a scheduled GitHub Actions pipeline run.

### Changed
- Switched the data source from Football-Data to Forebet, scraped through rotating free proxies.
- Replaced the FastAPI backend and Streamlit frontend with a single Taipy simulator reading features from MySQL and predicting via the Databricks endpoint.
- Replaced H2O AutoML with an XGBoost classifier tuned by Optuna on mRMR-selected features.

### Fixed
- Consolidated scattered legacy scripts into one `betsim` package with shared configuration loaded from `config/.env` and `config/config.toml`.

## [2.0.1] - 2024-08-23

Revamped the model training process and model inference.

### Added
- Leveraged MLflow to track model experiments.
- Hosted the models' API with FastAPI at the backend server.
- Built a frontend interface using Streamlit to productionise the workflow.

### Changed
- Switched the data source from using TotalCorner to Football-Data.
- Used H2O AutoML to replace manual model tuning.

## [1.0.1] - 2022-11-26

Initial repository.
