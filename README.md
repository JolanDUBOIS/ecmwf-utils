# ECMWF Forecast Retrieval

A small utility to retrieve ECMWF forecast data for lists of geographic points and time ranges, and to store the results as NetCDF (.nc) files together with metadata.

Key features
- Build and execute ECMWF requests for a set of coordinates and a time range
- Compute the smallest bounding box for requested points and choose an appropriate grid resolution
- Save retrieved NetCDF files and store retrieval metadata and queries in a simple index (index.csv)
- Provide a small CLI and configuration via YAML (and optional environment overrides)

## Installation & Requirements

### Requirements

- Python 3.11
- Poetry (recommended) to install and manage dependencies
- ECMWF API credentials (for example `~/.ecmwfapirc`) so `ecmwfapi` can authenticate

Refer to `pyproject.toml` for exact dependency versions.

### Installation

Install dependencies with Poetry:

```bash
poetry install
```

Ensure ECMWF credentials are available. Typically, `ecmwfapi` uses `~/.ecmwfapirc`. If you use environment variables or a different credentials file, document that mapping here.

## Configuration

### YAML configuration file

Configuration is read from `./config/config.yml`. Important settings are:

- `model`: string — ECMWF model to query, e.g. hres or ens
- `level`: string — the level to query (currently only surface supported)
- `variables`: list — ECMWF parameter codes to request (e.g. `['2t', '10u', '10v']`)
- `lookback`: integer — forecast window (hours)
- `step_granularity`: integer — step interval in hours (e.g. `1` for hourly output)

Here is an example for `config/config.yml`:

```yaml
model: hres # str, either 'hres' or 'ens'
level: surface # str, only surface is supported for now

variables: ['2t', '10u', '10v', 'msl', 'tp', '2d'] 
# variables: ['2t', '10u', '10v', 'msl', '2d', 'tp', 'sf', 'cp', 'lsp', 'sd'] # Everything that can be retrieved is here

lookback: 48 # int, in hours, e.g. 48 means forecasts from the last 48 hours
step_granularity: 1 # int, in hours, e.g. 1 means every hour, 3 means every 3 hours
```

This configuration requests the HRES model at surface level with six specific variables, retrieves forecasts from the last 48 hours, and uses a 1-hour step interval.

### Environment variables

Three environment variables can be defined:
- `LOG_FILE_PATH`: override the default value for the log file (DEBUG level)
- `LANDING_PATH`: path to the landing directory
- `STAGING_PATH`: path to the staging file path (CSV file, parquet accepted in a future update)

To define those variables, either use a `.env` file or run the following command directly into your terminal:

```bash
export LOG_FILE_PATH="./logs/DEBUG_test.log"
export LANDING_PATH="./data/landing/"
export STAGING_PATH="./data/staging/main.csv"
```

If you're using a `.env` file, don't forget to run:

```bash
source .env
```

### CLI / Usage

The package exposes a module-based CLI that now uses subcommands. There are two primary subcommands:

- `retrieval` — run the data retrieval pipeline
- `preprocess` — run the data preprocessing pipeline (WIP)

Examples:

```bash
# Retrieval: run the default query ./queries/default.json
poetry run python -m src retrieval

# Retrieval: run a specific query
poetry run python -m src retrieval --query-path ./queries/example.json

# Retrieval: run a specific query with a specific model 
poetry run python -m src retrieval --query-path ./queries/example.json --model ens

# Retrieval dry run (allocates paths but does not finalize saved entries)
poetry run python -m src retrieval --dry-run

# Preprocess (using env variables)
poetry run python -m src preprocess

# Preprocess (overrides env variables)
poetry run python -m src preprocess --landing-path ./data/landing/ --staging-path ./data/staging/main.csv
```

Retrieval options (summary):

- `--model` : model type (`hres` or `ens`)
- `--level` : level type (only `surface` is implemented)
- `--query-path` : path to the query JSON
- `--landing-path` : path to the folder where retrieved data files are saved (overrides `LANDING_PATH` env variable)
- `--dry-run` : simulate retrievals without finalizing saved entries
- `--verbose` : enable more verbose logging (not implemented yet)

Preprocess options (WIP):

- `--landing-path` : folder with raw retrieved files (overrides `LANDING_PATH` env variable)
- `--staging-path` : output file path for preprocessed data (overrides `STAGING_PATH` env variable)

CLI parsing lives in `src/setup/cli.py`.

### Configuration sources & precedence

The CLI parameters override environment variables and evnironment variables override YAML configuration values. The table below is a summary of all configuration variable the user has access to:

| Parameter           | YAML config file | Environment variable | CLI | Default |
|----------------------|------------------|----------------------|-----|----------|
| Model                | Y               | -                   | Y  | HRES |
| Level                | Y               | -                   | Y  | surface (only one implemented) |
| Variables            | Y               | -                   | -  | - |
| Lookback (window)    | Y               | -                   | -  | - |
| Step granularity     | Y               | -                   | -  | - |
| Logging file path    | -               | Y                   | -  | `./logs/DEBUG.log` |
| Logging verbosity    | -               | -                   | Y  | `INFO` |
| Query path           | -               | -                   | Y  | `./queries/default.json` |
| Landing path         | -               | Y                   | Y  | `./data/landing/` |
| Staging path         | -               | Y                   | Y  | `./data/staging/` |
| Dry run              | -               | -                   | Y  | `False` |
| …                    | …                | …                    | …   | … |


## Query file

A query is a JSON file with a `time_range` (ISO 8601 strings) and a `points` array of `[lat, lon]` pairs. Example:

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

The query is parsed by `src/query.py` into `Query`, `PointCloud` and `TimeRange` dataclasses.

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
- `src/query.py` — query dataclasses and parsing

## Storage layout

By default the output folder is at `./data/landing/` and can be defined using the environment variable `LANDING_PATH` or the CLI flag `--landing-path`. The layout created by `StorageManager` is:

```
landing/
├── index.csv
├── queries/
│   ├── query_A.json
│   ├── query_B.json
│	  └── ...
└── data/
	  ├── ecmwf_hres_sfc_YYYY-mm-DD HH:MM_timestamp1.nc
	  ├── ecmwf_hres_sfc_YYYY-mm-DD HH:MM_timestam2.nc
	  ├── ecmwf_ens_sfc_YYYY-mm-DD HH:MM_timestam3.nc
	  ├── ecmwf_ens_sfc_YYYY-mm-DD HH:MM_timestam4.nc
	  └── ...
```

Each retrieval is described by a `RetrievalMeta` and `RetrievalTicket` and includes deterministic IDs (SHA-256 truncated) used in the index.

## Logging

Logging is configured in `config/logging.yml` and is set up at program start (see `src/__main__.py`). Important points:

- Console handler prints INFO+ messages by default
- A debug file handler writes DEBUG logs to `logs/DEBUG.log` (can be overridden by env variable `LOG_FILE_PATH`)
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
