from . import logger
from .setup import PipelineConfig
from .query import Query
from .ecmwf_client import ECMWFClient

def run_retrieval(
    config: PipelineConfig,
    dry_run: bool = False,
    verbose: bool = False # Not yet implemented
):
    logger.info("Starting pipeline...")
    client = ECMWFClient(output_folder=config.landing_path)
    query = Query.from_json(config.query_path)
    client.get_forecast(
        config=config,
        query=query,
        dry_run=dry_run
    )
