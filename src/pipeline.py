from pathlib import Path

from . import logger
from .setup import Config, Query
from .ecmwf_client import ECMWFClient

def run_retrieval(
    config: Config,
    query: Query,
    output_folder: Path,
    level: str,
    dry_run: bool = False,
    verbose: bool = False # Not yet implemented
):
    logger.info("Starting pipeline...")
    logger.debug(f"Output folder: {output_folder}")
    client = ECMWFClient(output_folder=output_folder)
    client.get_forecast(
        config=config,
        query=query,
        level=level,
        dry_run=dry_run
    )
