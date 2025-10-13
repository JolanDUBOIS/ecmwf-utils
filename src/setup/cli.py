import argparse
from pathlib import Path

from ..constants import DEFAULT_CONFIG_PATH, DEFAULT_QUERY_PATH, ALLOWED_LEVELS


def parse_args(default_landing: Path, default_staging: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Main entry point for the ECMWF Data Processing System.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Retrieval pipeline ===
    retrieval_parser = subparsers.add_parser("retrieval", help="Run the data retrieval pipeline.")
    retrieval_parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help="Path to the configuration file"
    )
    retrieval_parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging"
    ) # Not implemented yet
    retrieval_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Perform a dry run without saving any files"
    )
    retrieval_parser.add_argument(
        "--query-path",
        type=str,
        default=DEFAULT_QUERY_PATH,
        help="Path to the JSON file containing the list of time ranges and points"
    )
    retrieval_parser.add_argument(
        "--level",
        type=str,
        choices=ALLOWED_LEVELS,
        default="surface",
        help="Level type (surface or model)"
    )

    # === Preprocessing pipeline ===
    preprocess_parser = subparsers.add_parser("preprocess", help="Run the data preprocessing pipeline.")
    preprocess_parser.add_argument(
        "--landing-folder",
        type=str,
        default=str(default_landing),
        help="Folder containing raw data files to preprocess"
    )
    preprocess_parser.add_argument(
        "--staging-file",
        type=str,
        default=str(default_staging),
        help="Folder to save preprocessed data"
    )

    return parser.parse_args()
