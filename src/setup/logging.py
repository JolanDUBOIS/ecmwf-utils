import logging
import logging.config
from datetime import datetime
from pathlib import Path

import yaml


def setup_logging(config_file: Path, logging_path: Path | None = None, timestamped: bool = True) -> None:
    """Set up logging configuration from a YAML file, optionally overriding log file paths.
    
    If timestamped=True, appends a timestamp after the .log extension.
    """
    with config_file.open("r") as f:
        config = yaml.safe_load(f)

    if logging_path:
        for handler in config.get("handlers", {}).values():
            if handler.get("class") == "logging.FileHandler":
                filename = Path(logging_path)
                if timestamped:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = filename.with_name(f"{filename.name}.{ts}")
                handler["filename"] = str(filename)

    logging.config.dictConfig(config)


ecmwfapi_logger = logging.getLogger("ecmwfapi")

def ecmwf_log(msg: str) -> None:
    """ Custom logger function to integrate ECMWF API logs into the main logging system. """
    try:
        level_str, real_msg = msg.split(" - ")[1].strip().upper(), msg.split(" - ")[-1].strip()
        if level_str == "INFO":
            ecmwfapi_logger.info(f"{real_msg}")
        elif level_str == "WARNING" or level_str == "WARN":
            ecmwfapi_logger.warning(f"{real_msg}")
        elif level_str == "ERROR" or level_str == "ERR":
            ecmwfapi_logger.error(f"{real_msg}")
        else:
            raise ValueError("Unknown log level")
    except Exception:
        ecmwfapi_logger.debug(f"{msg}")
