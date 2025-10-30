import os
import argparse
from pathlib import Path

import yaml
from dotenv import load_dotenv

from .schema import PipelineConfig


def load_config(path: str | Path, args: argparse.Namespace = None) -> PipelineConfig:
    # Load YAML configuration
    path = Path(path)
    with path.open("r") as f:
        config_dict = yaml.safe_load(f)

    # Load environment variables
    load_dotenv(override=True)
    env_config = {
        "logging_path": os.getenv("LOG_FILE_PATH"),
        "landing_path": os.getenv("LANDING_PATH"),
        "staging_path": os.getenv("STAGING_PATH"),
    }
    env_config = {k: v for k, v in env_config.items() if v is not None}

    # CLI configuration
    cli_config = vars(args) if args else {}
    cli_config = {k: v for k, v in cli_config.items() if v is not None}

    # Merge configurations with precedence: CLI > Env > YAML > Defaults
    final_config = {**config_dict, **env_config, **cli_config}
    pipeline_config = {k: v for k, v in final_config.items() if k in PipelineConfig.__dataclass_fields__}

    return PipelineConfig(**pipeline_config)
