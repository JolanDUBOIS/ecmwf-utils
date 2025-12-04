from pathlib import Path

from .setup import parse_args, setup_logging, load_config


LOGGING_CONFIG_PATH = Path(__file__).parent.parent / "config" / "logging.yml"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yml"

if __name__ == "__main__":

    args = parse_args()
    config = load_config(CONFIG_PATH, args)
    setup_logging(LOGGING_CONFIG_PATH, config.logging_path)

    if args.command == "retrieval":
        from .pipeline import run_retrieval
        run_retrieval(
            config=config,
            **vars(args)
        )

    elif args.command == "preprocess":
        from .preprocessing import run_preprocessing
        run_preprocessing(
            config=config,
        )
