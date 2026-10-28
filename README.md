# GiniCast · Phase 1 data acquisition

A Python CLI for fetching, validating, and recording economic time series. This repository demonstrates the acquisition layer: a configuration registry, source adapters, long-format CSV normalization, bounded HTTP retries, and explicit batch outcomes.

The registry currently lists **49 metrics, including 19 core metrics**. These are configured targets, not a claim of complete or verified coverage. FRED and BLS have HTTP adapters; Census, WIID, OECD, and `manual` use prepared local CSVs. Some series definitions and mappings still require review. Forecasting, model evaluation, dashboards, and production operation are outside this Phase 1 scope.

## Quick start: deterministic offline validation

Prerequisites: Python 3.11+ and [uv](https://docs.astral.sh/uv/) (the CI uses uv 0.12.15). From the repository root:

```bash
bash scripts/validate.sh
```

This installs the dependencies pinned in `uv.lock` into `.venv-validation/`, runs Ruff and the offline tests, and verifies the synthetic demo against committed expected CSVs. The first install needs package-index access; the tests and demo make no external data API calls and need no credentials. An existing `.venv/` is left alone. Generated environments and outputs are ignored by Git.

To run just the demo after installation:

```bash
.venv-validation/bin/python scripts/demo.py
# Keep artifacts in a NEW directory for inspection:
.venv-validation/bin/python scripts/demo.py --output-dir /tmp/ginicast-example
```

The fixture in `examples/offline/` contains **synthetic values, not economic observations**. Expected result: two successful metrics, five rows, one explicitly missing observation, and byte-for-byte matching standardized CSVs. Metadata timestamps, run IDs, and absolute paths vary. Without `--output-dir`, the temporary demo workspace is removed on completion.

## Local setup and live acquisition

```bash
UV_PROJECT_ENVIRONMENT=.venv-validation uv sync --locked --extra dev
cp .env.example .env
# Edit .env only if you intend to use live APIs; never commit keys.
.venv-validation/bin/ginicast-data doctor
.venv-validation/bin/ginicast-data pull --core
# Or: .venv-validation/bin/ginicast-data pull --all
.venv-validation/bin/ginicast-data audit
```

Run from the repository root. To use another data/config workspace, set `GINICAST_ROOT=/absolute/workspace`; it must contain `config/metrics.yaml` and `config/sources.yaml`. This also supports a wheel installation: configuration and manual inputs belong to the workspace, not site-packages. The repository's logging configuration writes under that workspace; when it is absent, logging goes to the console.

`doctor` checks installed runtime distributions and configuration structure without making requests. It reports whether API key variables appear present, with validity explicitly unverified. Its exit status covers **local config/dependencies only**. It cannot establish credential validity, network access, source availability, series semantics, coverage, or provenance. FRED needs `FRED_API_KEY`; BLS can run without a key, with a shorter request window. `scripts/validate_env.py` checks key presence only, not validity.

Live smoke testing is separate and opt-in, can make an external request, and requires your own FRED key:

```bash
FRED_API_KEY=... .venv-validation/bin/python -m pytest -m live tests/test_fred_fetch_smoke.py
```

The default test command excludes `live` even when a key happens to be present. CI runs deterministic offline tests and lint on Python 3.11 and 3.12; no secrets are configured or required by the workflow. A committed workflow is not evidence that a hosted CI run has passed.

## Outcomes and output safety

Every normally completed pull writes a unique `data/runs/<run_id>.json` manifest. It records selection, timestamps, each metric's `success`, `failed`, or `skipped` outcome, row/missing counts, output paths, summary counts, and exit code. Successful metadata includes the same run ID. Missing inputs, empty responses, malformed data, and adapter/write errors are failures; disabled sources are explicit skips. The command continues through remaining metrics. Exit **0** means every selected metric succeeded; exit **1** means a failure, skip, empty selection, or fatal command error. Error reports avoid raw exception text that might include credential-bearing URLs; unexpected errors are identified by exception class.

CSV validation rejects missing/invalid dates, duplicate dates, invalid numeric tokens, infinity, and series without any numeric observations. Valid gaps remain blank and are counted. Standardized rows are sorted by date with columns:

```text
date,value,metric,source,frequency,units
```

Validation finishes before any output for that metric is replaced. Each CSV/JSON write uses a temporary file in the destination directory and an atomic replacement. **The three metric files are not a single transaction.** A later write failure can leave some newly replaced files. Failed metrics may also retain older files. Read the manifest and metadata run IDs before consuming outputs; file existence alone is not evidence of a successful current run. There is no concurrent-run coordination or versioned dataset store. Manifest write failure is a fatal command error; process termination can leave no final manifest.

HTTP GET/POST calls use a 10-second request timeout and at most four attempts, with exponential waits of 2, 2, and 4 seconds. Only connection errors, timeouts, HTTP 429, and 5xx responses are retried; permanent errors such as 401/404 fail immediately. Source `rate_limit_*` settings remain descriptive hints: there is no shared quota scheduler, and `Retry-After` is not interpreted. Batches run sequentially. BLS uses a single recent request window (20 inclusive calendar years with a key, 10 without), excludes M13 annual averages from monthly data, and does not backfill the full historical series.

## Sources and manual CSVs

See [manual input requirements and provenance](data/raw_manual/README.md). The two legacy Census/WIID CSVs in this repository have no accompanying original-download or transformation record; **their provenance is unverified**. Do not treat them as authoritative observations or as evidence of validated core coverage. They are preserved for review; the offline demo uses separate synthetic fixtures.

Source metadata records the configured source, series ID, units, expected frequency, retrieval timestamp, observation bounds, and row counts. Manual ingestion additionally records the input path and SHA-256 hash, with provenance marked unverified. A hash identifies bytes; it does not verify their origin or meaning. Configuration notes and claimed series mappings still need source-by-source validation, particularly tax-related definitions and frequency/units. Normalization does not resample, interpolate, align vintages, adjust for revisions, or prove metric comparability.

## Repository layout

| Path | Purpose |
| --- | --- |
| `config/` | Metric targets, source settings, logging |
| `src/ginicast_data/` | CLI, registry, fetch, normalize, write, audit |
| `examples/offline/` | Synthetic input/config and expected outputs |
| `tests/` | Offline behavior tests and opt-in FRED smoke |
| `data/raw_manual/` | Prepared manual inputs; provenance requirements |
| `data/raw/`, `data/standardized/`, `data/metadata/` | Ignored acquisition outputs |
| `data/runs/` | Ignored per-run manifests |
| `data/audit/` | CSV/Markdown summaries of files on disk |

The audit command summarizes existing standardized files, including older ones; it does not establish current-run success or verify source coverage. Add targets in `config/metrics.yaml`, supply matching source settings and reviewed source definitions, then add fixture tests before depending on a new adapter or format.
