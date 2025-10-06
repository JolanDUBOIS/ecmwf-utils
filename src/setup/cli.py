import argparse

from ..constants import DEFAULT_CONFIG_PATH, DEFAULT_QUERY_PATH, ALLOWED_LEVELS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ECMWF Data Retrieval CLI")
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the configuration file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging"
    ) # Not implemented yet
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Perform a dry run without saving any files"
    )
    parser.add_argument(
        "--query-path",
        type=str,
        default=DEFAULT_QUERY_PATH,
        help="Path to the JSON file containing the list of time ranges and points"
    )
    parser.add_argument(
        "--level",
        type=str,
        choices=ALLOWED_LEVELS,
        default="surface",
        help="Level type (surface or model)"
    )
    return parser.parse_args()
