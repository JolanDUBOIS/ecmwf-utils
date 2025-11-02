import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Main entry point for the ECMWF Data Processing System.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Retrieval pipeline ===
    retrieval_parser = subparsers.add_parser("retrieval", help="Run the data retrieval pipeline.")
    retrieval_parser.add_argument(
        "--model",
        type=str,
        help="Model type (hres or ens)"
    )
    retrieval_parser.add_argument(
        "--level",
        type=str,
        help="Level type (surface or model)"
    )
    retrieval_parser.add_argument(
        "--query-path",
        type=str,
        help="Path to the JSON file containing the list of time ranges and points"
    )
    retrieval_parser.add_argument(
        "--landing-path",
        type=str,
        help="Path to the folder where retrieved data files will be saved"
    )
    retrieval_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Perform a dry run without saving any files"
    )
    retrieval_parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging"
    ) # Not implemented yet

    # === Preprocessing pipeline ===
    preprocess_parser = subparsers.add_parser("preprocess", help="Run the data preprocessing pipeline.")
    preprocess_parser.add_argument(
        "--landing-path",
        type=str,
        help="Path to the folder containing raw data files to preprocess"
    )
    preprocess_parser.add_argument(
        "--staging-path",
        type=str,
        help="..."
    )

    return parser.parse_args()
