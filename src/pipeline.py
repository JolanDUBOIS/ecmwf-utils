import concurrent.futures

from . import logger
from .setup import PipelineConfig
from .query import Query
from .ecmwf_client_new import ECMWFRequestsExecutor, ECMWFRequestsBuilder

def run_retrieval(
    config: PipelineConfig,
    concurrent_jobs: int = 1,
    **kwargs
):
    logger.info("Starting pipeline...")

    query = Query.from_json(config.query_path)
    builder = ECMWFRequestsBuilder(config, query)
    executor = ECMWFRequestsExecutor(config, query)

    requests = builder.build_requests()

    if concurrent_jobs > 1:
        logger.info(f"Running with up to {concurrent_jobs} concurrent jobs...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_jobs) as thread_pool:
            future_to_request = {
                thread_pool.submit(executor.get_forecast, req, **kwargs): req 
                for req in requests
            }

            for future in concurrent.futures.as_completed(future_to_request):
                original_request = future_to_request[future]

                try:
                    success = future.result()
                    if success:
                        logger.info(f"Successfully completed request: {original_request}")
                    else:
                        logger.warning(f"Request failed: {original_request}")
                except Exception as e:
                    logger.error(f"Unexpected error durring execution: {e}")
            
    else:
        logger.info("Running sequentially...")

        for request in requests:
            executor.get_forecast(
                request=request,
                **kwargs
            )

    logger.info("Pipeline finished.")
