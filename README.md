# GiniCast Phase 1 Data Acquisition

This repository contains the data acquisition pipeline (Phase 1) for the GiniCast project. It automates the extraction of 30+ macroeconomic and socioeconomic metrics from various sources (FRED, BLS, Census, OECD, WIID) and standardizes them into long-format CSVs.

## Setup Instructions

1. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install the package:**
   ```bash
   pip install -e .
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your API keys (e.g., `FRED_API_KEY`, `BLS_API_KEY`).

## Usage

The pipeline exposes a CLI tool: `ginicast-data`.

- **Check setup and environment:**
  ```bash
  ginicast-data doctor
  ```

- **Pull Core 19 Metrics:**
  ```bash
  ginicast-data pull --core
  ```

- **Pull All Configured Metrics:**
  ```bash
  ginicast-data pull --all
  ```

- **Generate Metadata Audit Report:**
  ```bash
  ginicast-data audit
  ```

### Manual Scripts

You can also use the convenience shell scripts provided in `scripts/`:
- `./scripts/run_core19.sh`
- `./scripts/run_all.sh`
- `python scripts/validate_env.py`

## Directory Structure & Outputs
- `data/raw/`: Contains the raw pulls for each metric, separated by source.
- `data/metadata/`: Contains `.json` metadata files for each pull.
- `data/standardized/`: Contains long-format standardized CSVs (`date, value, metric, source, frequency, units`).
- `data/audit/`: Contains the generated audit reports summarizing coverage and gaps.
- `data/raw_manual/`: Place manual dataset downloads here (e.g., Census/WIID files) for parsing.

## Adding New Metrics
To add a new metric, simply edit `config/metrics.yaml`. Provide a `metric_id`, `source`, and the specific `source_series_id` if known. If a source is complicated to automate, you can set the source to `manual` and drop a CSV file into `data/raw_manual/`.

## Manual Ingest
For metrics where direct API access is difficult (e.g., Census tables, WIID), download the files manually and place them in `data/raw_manual/<source>/`. When the pipeline runs, it will attempt to process files from this folder if a respective fetching logic handles it.
