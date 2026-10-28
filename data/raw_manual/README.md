# Manual input contract and provenance

Census, WIID, OECD, and generic manual adapters read exactly:

```text
data/raw_manual/<source>/<metric_id>.csv
```

A raw downloaded Census table, Excel workbook, Stata file, or OECD export cannot be dropped in unchanged. Select the intended geography, population, definition, and measure first; reshape it into a UTF-8 CSV with `date,value` columns. Extra columns are ignored. Use ISO `YYYY-MM-DD` dates (January 1 for an annual observation), one row per date, plain numeric values in the configured units, and an empty value field only for a known missing observation. Do not include thousands separators, percent signs, `N/A`, `NaN`, or other nonnumeric tokens. Invalid/missing dates, duplicate dates, malformed values, and all-missing series fail validation. A missing file or header-only CSV is a failed metric, not a successful acquisition.

Example shape only:

```csv
date,value
2020-01-01,1.5
2021-01-01,
2022-01-01,1.7
```

For every real dataset, maintain an accompanying `<metric_id>.provenance.json` or equivalent reviewed record with:

- Original publisher, dataset title/version and source download URL.
- Table/series identifiers, geography, population, units, and frequency.
- Access date, original file name and checksum, and applicable reuse terms.
- Exact filters, selected columns, transformations, and missing-value handling.
- Prepared CSV checksum and any caveats about revisions or comparability.

The CLI records the prepared file path and SHA-256 hash, and labels manual provenance as unverified. It does **not** read or verify the accompanying provenance record, download the original dataset, or establish that the configured definition matches the data. Review provenance before analysis or publication.

`census/gini_coefficient.csv` and `wiid/palma_ratio.csv` predate this contract and lack an original-download/transformation record. Their origin and values have not been verified. Keep that limitation attached to them until primary-source evidence is supplied; do not cite the source name in a config file as proof of provenance. Do not derive a claimed real-data result from the synthetic fixtures under `examples/offline/`.
