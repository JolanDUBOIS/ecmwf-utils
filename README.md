# ECMWF Forecast Retrieval

A small utility to retrieve ECMWF forecast data for lists of geographic points and time ranges, and to store the results as NetCDF (.nc) files together with metadata.

Key features

- Build and execute ECMWF requests for a set of coordinates and a time range
- Compute the smallest bounding box for requested points and choose an appropriate grid resolution
- Save retrieved NetCDF files and store retrieval metadata and queries in a simple index (index.csv)
- Provide a small CLI and configuration via YAML (and optional environment overrides)

## Installation & Requirements

### Requirements

- Python 3.12
- Mamba (recommended) to create and manage the environment

Refer to `requirements.txt` for the exact dependency list and versions.

### Installation

Create the environment with Mamba:

```bash
mamba create -n ecmwf-utils python=3.11
```

Install dependencies into the environment:

```bash
mamba run -n ecmwf-utils pip install -r requirements.txt
# or
mamba env create -n ecmwf-utils -f environment.yml
```

### ECMWF Credentials

To run any commands in this project, it is necessary to have ECMWF API credentials. These can be set as environment variables or they can be set in an `.ecmwfapirc` file. The logic is as follows:

- Step 1: the environment is checked for variables `ECMWF_API_KEY`,
  `ECMWF_API_URL`, `ECMWF_API_EMAIL`. To use add these in a `.env` file within project root.

  - If all found, and not empty, return their values in Python tuple
    format.
  - If only some found, and not empty, assume an incomplete API key, and
    raise APIKeyFetchError.
  - If none found, or found but empty, assume no API key available in the
    environment, and continue to the next step.

- Step 2: the environment is checked for variable `ECMWF_API_RC_FILE`, meant
  to point to a user defined API key file. To use add this in a `.env` file within project root.

  - If found, but pointing to a file not found, raise APIKeyNotFoundError.
  - If found, and the file it points to exists, but cannot not be read, or
    contains an invalid API key, raise APIKeyFetchError.
  - If found, and the file it points to exists, can be read, and contains
    a valid API key, return the API key in Python tuple format.
  - If not found, or empty, assume no user provided API key file and
    continue to the next step.

- Step 3: try the default `~/.ecmwfapirc` file. To use add file within home folder.

  - Same as step 2, except for when `~/.ecmwfapirc` is not found, where we
    continue to the next step.

- Step 4: No API key found, so fall back to anonymous access. This will fail since we request MARS which is access controlled.

## Configuration

### YAML configuration file

Configuration is read from `./config/config.yml`. Important settings are:

- `name`: string — optional identifier for the configuration, stored in the retrieval index for traceability. Defaults to `default` if not provided.
- `model`: string — ECMWF model to query (either `hres` or `ens`)
- `level`: string — the level to query (currently only `surface` supported)
- `retrieval_mode`: string — whether to retrieve a grid or a single point (either `grid` or `point`)
- `batch_issue`: bool or int — controls batching of issue datetimes during retrieval.
  - If `False`, each issue datetime is queried independently (one request per issue).
  - If an integer `N > 0`, issue datetimes are grouped into batches spanning `N` consecutive days, and each batch is retrieved in a single request. This reduces the number of API calls at the cost of larger individual requests.
- `format`: string — the format of the output files (either `netcdf` for `.nc` files or `grib2` for `.grib` files)
- `variables`: list of string — ECMWF parameter codes to request (e.g. `['2t', '10u', '10v']`)
- `issue_hours`: list of string — hours of the day to retrieve the issued forecasts (e.g. `["00", "12"]` for model `hres` or `["00", "06", "12", "18"]` for model `ens`)
- `lookback`: integer — forecast window (hours)
- `step_granularity`: integer — step interval in hours (e.g. `1` for hourly output)

Here is an example for `config/config.yml`:

```yaml
name: default

model: hres # str, either 'hres' or 'ens'
level: surface # str, only surface is supported for now
retrieval_mode: point # str, either 'point' or 'grid'
batch_issue: 10 # bool or int, if False, process each issue hour separately; if int, process that many issue day at once

format: grib2 # str, either 'grib2' or 'netcdf'

variables: ["2t", "10u", "10v", "msl", "2d", "tp", "sf", "cp", "lsp", "sd"]

issue_hours: ["00", "06", "12", "18"]
lookback: 48 # int, in hours
step_granularity: 1 # int, in hours
```

This configuration requests the HRES model at surface level with six specific variables, retrieves forecasts from the last 48 hours, and uses a 1-hour step interval.

More on the **variables** can be found at the end of this README.

### Environment variables

Three environment variables can be defined:

- `LOG_FILE_PATH`: override the default value for the log file (DEBUG level)
- `LANDING_PATH`: path to the landing directory
- `STAGING_PATH`: path to the staging file path (CSV file, parquet accepted in a future update)

To define those variables, either use a `.env` file or run the following command directly into your terminal:

```bash
export LOG_FILE_PATH="./logs/DEBUG.log"
export LANDING_PATH="./data/landing/"
export STAGING_PATH="./data/staging/main.csv"
```

If you're using a `.env` file, keep it in the root of this repository as best practice.

### CLI / Usage

The package exposes a module-based CLI that now uses subcommands. There are two primary subcommands:

- `retrieval` — run the data retrieval pipeline
- `preprocess` — run the data preprocessing pipeline (WIP)

Examples:

```bash
# Retrieval: run the default query ./queries/default.json
mamba run -n ecmwf-utils python -m src retrieval

# Retrieval: run a specific query
mamba run -n ecmwf-utils python -m src retrieval --query-path ./queries/example.json

# Retrieval: run a specific query & a specific config file
mamba run -n ecmwf-utils python -m src retrieval --query-path ./queries/example.json --config-path ./config/config_example.yml

# Retrieval: run a specific query with a specific model in parallel processing
mamba run -n ecmwf-utils python -m src retrieval --query-path ./queries/example.json --model ens --concurrent-jobs 5

# Retrieval: dry run (performs queries but does not save any files)
mamba run -n ecmwf-utils python -m src retrieval --dry-run

# Retrieval: cost-only mode (runs only cost query, no data query or save)
mamba run -n ecmwf-utils python -m src retrieval --skip-query

# Retrieval: skip cost estimation (directly runs data queries)
mamba run -n ecmwf-utils python -m src retrieval --skip-cost

# Preprocess (using env variables)
mamba run -n ecmwf-utils python -m src preprocess

# Preprocess (overrides env variables)
mamba run -n ecmwf-utils python -m src preprocess --landing-path ./data/landing/ --staging-path ./data/staging/main.csv
```

Retrieval options (summary):

- `--model` : model type (`hres` or `ens`)
- `--level` : level type (only `surface` is implemented)
- `--query-path` : path to the query JSON
- `--landing-path` : path to the folder where retrieved data files are saved (overrides `LANDING_PATH` env variable)
- `--config-path` : path to the configuration file to use. Overrides the default config path (`./config/config.yml`).
- `--dry-run` : simulate retrievals without finalizing saved entries
- `--skip-cost`: skip the cost query step entirely.
- `--skip-query`: skip the actual data retrieval (no save occurs, even if `--dry-run` is not set).
- `--concurrent-jobs` : maximum number of simultaneous API requests to execute. Use >1 for parallel execution (e.g., 5). Default is 1 (sequential).
- `--verbose` : enable more verbose logging (not implemented yet)

Preprocess options (WIP):

- `--landing-path` : folder with raw retrieved files (overrides `LANDING_PATH` env variable)
- `--staging-path` : output file path for preprocessed data (overrides `STAGING_PATH` env variable)

CLI parsing lives in `src/setup/cli.py`.

### Configuration sources & precedence

The CLI parameters override environment variables and evnironment variables override YAML configuration values. The table below is a summary of all configuration variable the user has access to:

| Parameter         | YAML config file | Environment variable | CLI | Default                          | Type        |
| ----------------- | ---------------- | -------------------- | --- | -------------------------------- | ----------- |
| Model             | Y                | -                    | Y   | `hres`                           | str         |
| Level             | Y                | -                    | Y   | `surface` (only one implemented) | str         |
| Retrieval Mode    | Y                | -                    | -   | `point`                          | str         |
| Batch Issue       | Y                | -                    | -   | `False`                          | bool or int |
| Format            | Y                | -                    | -   | `netcdf`                         | str         |
| Variables         | Y                | -                    | -   | `[]` (empty list)                | list of str |
| Issue Hours       | Y                | -                    | -   | `[]` (empty list)                | list of str |
| Lookback (window) | Y                | -                    | -   | `48`                             | int         |
| Step granularity  | Y                | -                    | -   | `1`                              | int         |
| Logging file path | -                | Y                    | -   | `./logs/DEBUG.log`               | Path        |
| Concurrent Jobs   | -                | -                    | Y   | `1`                              | int         |
| Logging verbosity | -                | -                    | Y   | `INFO`                           | str         |
| Query path        | -                | -                    | Y   | `./queries/default.json`         | Path        |
| Landing path      | -                | Y                    | Y   | `./data/landing/`                | Path        |
| Staging path      | -                | Y                    | Y   | `./data/staging/`                | Path        |
| Dry run           | -                | -                    | Y   | `False`                          | bool        |
| …                 | …                | …                    | …   | …                                | …           |

## Query file

A query is a JSON file with a `time_range` (ISO 8601 strings) and a `points` array of `[lat, lon]` pairs (and an optional `name`, with default empty str). Example:

```json
{
  "name": "default",
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
2. Build a base MARS request using for instance `variables`, `lookback` and `step-granularity`
3. Create requests for each issued time for the ECMWF API:
   - If the retrieval mode is `grid`, compute the smallest bounding box for the given points and generate the appropriate `area` and `grid` request parameters
   - If the retrieval mode is `point`, create one request per point in the query
4. Iterate over the requested dates and issued hours (`issue_hours`) and request forecasts
5. Allocate storage paths, write the NetCDF file returned by ECMWF, save the query JSON alongside it, and add an entry to `index.csv`

Key modules:

- `src/ecmwf_client` — manages the builder and executer of MARS requests
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

## ECMWF Weather Variables

Here is a non exhaustif mapping of variables that can be retrieved from one or the other model.

| Short Name | Long Name                                                | Field Code | Available in HRES | Available in ENS |
| ---------- | -------------------------------------------------------- | ---------- | ----------------- | ---------------- |
| `mx2t3`    | Maximum 2 m temperature (last 3 h)                       | 26.228     | Not tested        | Not tested       |
| `mn2t3`    | Minimum 2 m temperature (last 3 h)                       | 27.228     | Not tested        | Not tested       |
| `10fg3`    | Maximum 10 m wind gust (last 3 h)                        | 28.228     | Not tested        | Not tested       |
| `10fg`     | Maximum 10 m wind gust                                   | 49.128     | Not tested        | Not tested       |
| `mx2t6`    | Maximum 2 m temperature (last 6 h)                       | 121.128    | Not tested        | Not tested       |
| `mn2t6`    | Minimum 2 m temperature (last 6 h)                       | 122.128    | Not tested        | Not tested       |
| `10fg6`    | Maximum 10 m wind gust (last 6 h)                        | 123.128    | Not tested        | Not tested       |
| `sd`       | Snow depth                                               | 141.228    | Yes               | Not tested       |
| `sf`       | Snow fall                                                | 144.128    | Yes               | Not tested       |
| `cp`       | Convective precipitation                                 | 143.128    | Yes               | Not tested       |
| `lsp`      | Large scale precipitation                                | 142.128    | Yes               | Not tested       |
| `msl`      | Mean sea level pressure                                  | 151.128    | Yes               | Not tested       |
| `10u`      | 10-metre eastward wind component                         | 165.128    | Yes               | Yes              |
| `10v`      | 10-metre northward wind component                        | 166.128    | Yes               | Yes              |
| `2t`       | 2 metre temperature                                      | 167.128    | Yes               | Yes              |
| `2d`       | 2 metre dewpoint temperature                             | 168.128    | Yes               | Yes              |
| `mx2t`     | Maximum 2 m temperature (since previous post-processing) | 201.128    | Yes               | Not tested       |
| `mn2t`     | Minimum 2 m temperature (since previous post-processing) | 202.128    | Yes               | Not tested       |
| `tp`       | Total precipitation                                      | 228.128    | Yes               | Not tested       |
| `100u`     | 100 m eastward wind component                            | 246.228    | Yes               | Yes              |
| `100v`     | 100 m northward wind component                           | 247.228    | Yes               | Yes              |

**Note:**

The number following the dot (e.g., `.128`, `.228`) refers to the GRIB parameter table from which the variable originates. In most practical cases, the table number does not affect data retrieval, as the short name (e.g., `10u`, `tp`) uniquely identifies the field within ECMWF’s datasets. However, it can matter when working directly with raw GRIB files or older data streams, where identical parameter numbers may exist in different tables.

**Disclaimer:**

Availability of variables in the ENS dataset has not been fully verified. Some entries are marked as “Not tested” because ENS data requests can take several hours to complete. If you test any of these variables and confirm whether they work (or don’t), feel free to update this README so future users can benefit from your results.

## Developer notes & TODOs

- Consider adding a guard to prevent extremely large queries (too many points) that could overload the API or hit request limits
- Model-level `levelist` used in `src/ecmwf_client.py` is a placeholder — confirm the correct levels for your use case
- Issued times currently use `00` and `12`. If 06/18 are required confirm availability and support in the `ecmwfapi` client
- Add grid resolution to config if you want it configurable per-run

## Warnings (dev only)

_WARNING: The preprocessing part might have been broken with the recent features to the retrieval pipeline._
