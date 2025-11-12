import traceback

from ecmwfapi import ECMWFService

from . import logger
from ..query import Query
from ..setup import PipelineConfig
from ..storage import StorageManager, RetrievalMeta
from ..setup.logging import ecmwf_log
from .request_builder import ECMWFRequestsBuilder


class ECMWFRequestsExecutor:
    """ TODO """

    def __init__(self, config: PipelineConfig, query: Query):
        logger.info("Initializing ECMWF Client...")
        self.server = ECMWFService("mars", log=ecmwf_log)
        self.config = config
        self.query = query
        self.storage_manager = StorageManager(config.landing_path)

    def get_forecast(
        self,
        request: dict,
        dry_run: bool = False
    ) -> bool:
        """ Retrieve forecast data for given points and date range. """
        logger.info(f"Retrieving forecast with request: {request}")
        meta = RetrievalMeta.from_request(request, self.config)
        ticket = self.storage_manager.allocate(meta, self.query)

        try:
            # First, run a cost-check request and save its output to the ticket
            try:
                cost_req = ECMWFRequestsBuilder.make_cost_check_request(request)
                logger.debug(f"Running cost check request: {cost_req}")
                # Write the cost check response to the allocated cost_check_file_path
                self.server.execute(cost_req, ticket.cost_check_file_path)
                logger.info(f"Cost check saved to {ticket.cost_check_file_path}")
            except Exception as ce:
                # Log and continue to attempt the main retrieval
                logger.error(f"Cost check failed: {ce}")
                logger.debug(traceback.format_exc())

            logger.debug(f"ECMWF request: {request}")
            self.server.execute(request, ticket.data_file_path)
            if not dry_run:
                logger.debug(f"Finalizing retrieval for {ticket.data_file_path}")
                self.storage_manager.finalize(ticket, self.query, success=True)
                return True
            else:
                logger.info(f"Dry run enabled, skipping finalize for {ticket.data_file_path}")
                self.storage_manager.finalize(ticket, self.query, success=False)
                return True
        except Exception as e:
            logger.error(f"Error retrieving data for: {e}")
            logger.debug(traceback.format_exc())
            self.storage_manager.finalize(ticket, self.query, success=False)
            return False
