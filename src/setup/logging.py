import logging
import logging.config
from pathlib import Path

import yaml


def setup_logging(config_file: Path):
    """ Set up logging configuration from a YAML file. """
    with config_file.open(mode='r') as f:
        config = yaml.safe_load(f.read())
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
