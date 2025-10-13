import os
from pathlib import Path

from dotenv import load_dotenv

from .pipeline import run_retrieval
from .setup import parse_args, setup_logging
from .constants import DEFAULT_LANDING_FOLDER, DEFAULT_STAGING_FILE


load_dotenv(override=True)
LANDING_FOLDER_PATH = Path(os.getenv("LANDING_FOLDER_PATH", DEFAULT_LANDING_FOLDER)).resolve()
STAGING_FILE_PATH = Path(os.getenv("STAGING_FILE_PATH", DEFAULT_STAGING_FILE)).resolve()
print(LANDING_FOLDER_PATH)
print(STAGING_FILE_PATH)

if __name__ == "__main__":
    logging_config_path = Path(__file__).parent.parent / "config" / "logging.yml"
    setup_logging(logging_config_path)
    
    args = parse_args(default_landing=LANDING_FOLDER_PATH, default_staging=STAGING_FILE_PATH)
    
    if args.command == "retrieval":
        from .setup import Query, Config

        query = Query.from_json(args.query_path)
        config = Config.from_yaml(args.config)

        run_retrieval(
            config=config,
            query=query,
            output_folder=LANDING_FOLDER_PATH,
            level=args.level,
            dry_run=args.dry_run,
            verbose=args.verbose
        )

    elif args.command == "preprocess":
        from .preprocessing import run_preprocessing

        run_preprocessing(
            landing_folder=Path(args.landing_folder),
            staging_file_path=Path(args.staging_file)
        )
