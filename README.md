# ECMWF Forecast Retrieval

A small utility to retrieve ECMWF forecast data for lists of geographic points and time ranges, and to store the results as NetCDF (.nc) files together with metadata.

This project focuses on forecast output (not analysis/reanalysis) and supports two level types:

- surface (sfc)
- model levels (ml)

Highlights

- Build and execute ECMWF requests for a set of coordinates and a time range
- Compute a smallest bounding box for the requested points and use an appropriate grid resolution
- Save retrieved NetCDF files and store retrieval metadata and queries in a simple index
- Provide a small CLI and configuration via YAML

## Requirements

- Python 3.11
- Poetry (recommended) to install and manage dependencies
- ECMWF API credentials (for example `~/.ecmwfapirc`) so `ecmwfapi` can authenticate

Refer to `pyproject.toml` for exact dependency versions.

## Installation

Install dependencies with Poetry:

```bash
poetry install
```

Make sure ECMWF credentials are available (e.g. `~/.ecmwfapirc`), or set the appropriate environment variables for your environment.

## Configuration

Configuration is read from `config/config.yml` by default. Important settings:

- `variables.surface` / `variables.model`: lists of ECMWF parameter codes to request for each level type
- `lookback`: integer (hours) for the forecast step window
- `step-granularity`: step interval (hours)

You can pass a different config file with the `--config` CLI option.

Here is an example for `config/config.yml`:

```yaml
variables:
    surface: ['2t', '10u', '10v', 'msl', 'tp', '2d']
    model: ['u', 'v', 't', 'q']
lookback: 48            # int, in hours, e.g. 48 means forecasts from the last 48 hours
step-granularity: 1     # int, in hours, e.g. 1 means every hour, 3 means every 3 hours
```

This configuration requests common surface and model-level variables, retrieves forecasts from the last 48 hours, and uses a 1-hour step interval.

## Query file format

A query is a JSON file with a `time_range` (ISO 8601 strings) and a `points` list of `[lat, lon]` pairs. Example:

```json
{
  "time_range": {
    "start": "2016-01-01T00:00:00Z",
    "end": "2016-01-15T00:00:00Z"
  },
  "points": [
    [55.902502, -2.306389],
    [55.900008, -2.301268]
  ]
}
```

The query is parsed by `src/setup/query.py` into `Query`, `PointCloud` and `TimeRange` dataclasses.

## CLI / Usage

The package exposes a module-based CLI that now uses subcommands. There are two primary subcommands:

- `retrieval` — run the data retrieval pipeline
- `preprocess` — run the data preprocessing pipeline

Examples:

```bash
# Retrieval: run a retrieval with the example query
poetry run python -m src retrieval --query-path ./queries/penmanshiel.json

# Retrieval with explicit level and config
poetry run python -m src retrieval --query-path ./queries/penmanshiel.json --level surface --config config/config.yml

# Retrieval dry run (allocates paths but does not finalize saved entries)
poetry run python -m src retrieval --query-path ./queries/penmanshiel.json --dry-run

# Preprocess: run preprocessing on a landing folder and write to a staging file
poetry run python -m src preprocess --landing-folder ./data/first-test --staging-file ./data/first-test/interpolated_concatenated_data_2016.csv
```

Subcommand options (brief):

retrieval:

- `--config` : path to YAML configuration (default `config/config.yml`)
- `--query-path` : path to the JSON query file
- `--level` : `surface` or `model` (default `surface`)
- `--dry-run` : simulate retrievals without finalizing saved entries
- `--verbose` : (reserved) enable more verbose logging (placeholder)

preprocess:

- `--landing-folder` : folder containing raw data files to preprocess (default comes from the program's landing path)
- `--staging-file` : file path to save preprocessed/staged data

CLI parsing lives in `src/setup/cli.py`.

## What happens when you run it

Core steps performed by the code:

1. Load configuration and parse the query JSON
2. Compute a smallest bounding box for the given points and generate `area` and `grid` strings for ECMWF requests
3. Build a base MARS request using `lookback` and `step-granularity`
4. Iterate over the requested dates and issued times (currently `00` and `12`) and request forecasts
5. Allocate storage paths, write the NetCDF file returned by ECMWF, save the query JSON alongside it, and add an entry to `index.csv`

Key modules:

- `src/ecmwf_client.py` — builds MARS requests and executes them via `ecmwfapi`
- `src/storage.py` — manages allocation, finalization and the `index.csv`
- `src/setup/query.py` — query dataclasses and parsing

## Storage layout

By default the output folder is determined by the `LANDING_FOLDER_PATH` environment variable or a project default. The layout created by `StorageManager` is:

```
<output_folder>/
  surface/
    data/
      ecmwf_fc_surface_<issued>_<timestamp>.nc
    queries/
      query_<query_id>_<timestamp>.json
  model/
    data/
    queries/
  index.csv
```

Each retrieval is described by a `RetrievalMeta` and `RetrievalTicket` and includes deterministic IDs (SHA-256 truncated) used in the index.

## Logging

Logging is configured in `config/logging.yml` and is set up at program start (see `src/__main__.py`). Important points:

- Console handler prints INFO+ messages by default
- A rotating debug file handler writes DEBUG logs to `logs/DEBUG.log`
- Module loggers (e.g. `src`, `src.setup`, `ecmwfapi`) are configured to use both handlers

Adjust `config/logging.yml` to change handler levels or formats. The `--verbose` flag is reserved for enabling more verbose console output but currently only exists as a placeholder flag in the CLI.

## Error handling and dry runs

- If a retrieval fails an error is logged and partial files (if any) are removed by the storage manager
- `--dry-run` exercises allocation and request construction but finalization into `index.csv` is skipped

## Developer notes & TODOs

- Consider adding a guard to prevent extremely large queries (too many points) that could overload the API or hit request limits
- Model-level `levelist` used in `src/ecmwf_client.py` is a placeholder — confirm the correct levels for your use case
- Issued times currently use `00` and `12`. If 06/18 are required confirm availability and support in the `ecmwfapi` client
- Add grid resolution to config if you want it configurable per-run

## Tests

If tests exist under `tests/` you can run them with pytest:

```bash
poetry run pytest -q
```

*WARNING: Tests are not implemented yet.*
