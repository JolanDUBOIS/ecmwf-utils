import os
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import run_pipeline
from .constants import DEFAULT_OUTPUT_FOLDER
from .setup import parse_args, setup_logging, Query, Config


load_dotenv()
OUTPUT_FOLDER_PATH = Path(os.getenv("OUTPUT_FOLDER_PATH", DEFAULT_OUTPUT_FOLDER))

if __name__ == "__main__":
    logging_config_path = Path(__file__).parent.parent / "config" / "logging.yml"
    setup_logging(logging_config_path)
    
    args = parse_args()
    query = Query.from_json(args.query_path)
    config = Config.from_yaml(args.config)
    
    run_pipeline(
        config=config,
        query=query,
        output_folder=OUTPUT_FOLDER_PATH,
        level=args.level,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
