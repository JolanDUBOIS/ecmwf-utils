from . import logger
from .setup import PipelineConfig
from .query import Query
from .ecmwf_client_new import ECMWFRequestsExecutor, ECMWFRequestsBuilder

def run_retrieval(
    config: PipelineConfig,
    dry_run: bool = False,
    verbose: bool = False # Not yet implemented
):
    logger.info("Starting pipeline...")

    query = Query.from_json(config.query_path)
    builder = ECMWFRequestsBuilder(config, query)
    executor = ECMWFRequestsExecutor(config, query)

    requests = builder.build_requests()
    for request in requests:
        executor.get_forecast(
            request=request,
            dry_run=dry_run
        )

    logger.info("Pipeline finished.")
