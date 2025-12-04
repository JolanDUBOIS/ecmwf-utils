import traceback

from ecmwfapi import ECMWFService

from . import logger
from ..query import Query
from ..setup import PipelineConfig
from ..storage import StorageManager, RetrievalMeta, RetrievalTicket
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
        dry_run: bool = False,
        skip_cost: bool = False,
        skip_query: bool = False,
        **kwargs
    ) -> bool:
        """ Retrieve forecast data for given points and date range. """
        logger.info(f"Retrieving forecast with request: {request}")
        meta = RetrievalMeta.from_request(request, self.config)
        ticket = self.storage_manager.allocate(meta, self.query)

        success = False
        try:
            # === COST CHECK PHASE ===
            if not skip_cost:
                self._run_cost_check(request, ticket)
            else:
                logger.info("Skipping cost check as requested (--skip-cost)")

            # === DATA RETRIEVAL PHASE ===
            if not skip_query:
                self._run_data_query(request, ticket, dry_run)
                success = True
            else:
                logger.info("Skipping data query as requested (--skip-query)")
                self.storage_manager.finalize(ticket, self.query, success=False)
            
        except Exception as e:
            logger.error(f"Error during retrieval process: {e}")
            logger.debug(traceback.format_exc())
            self.storage_manager.finalize(ticket, self.query, success=False)
            success = False

        return success           

    def _run_cost_check(self, request: dict, ticket: RetrievalTicket) -> None:
        """Run the ECMWF cost estimation query."""
        try:
            cost_req = ECMWFRequestsBuilder.make_cost_check_request(request)
            logger.debug(f"Running cost check request: {cost_req}")
            self.server.execute(cost_req, ticket.cost_check_file_path)
            logger.info(f"Cost check saved to {ticket.cost_check_file_path}")
        except Exception as e:
            logger.warning(f"Cost check failed (continuing anyway): {e}")
            logger.debug(traceback.format_exc())

    def _run_data_query(self, request: dict, ticket: RetrievalTicket, dry_run: bool) -> None:
        """Run the actual ECMWF data retrieval."""
        logger.debug(f"Running ECMWF data request: {request}")
        self.server.execute(request, ticket.data_file_path)

        if dry_run:
            logger.info(f"Dry run: retrieval simulated, skipping save for {ticket.data_file_path}")
            self.storage_manager.finalize(ticket, self.query, success=False)
        else:
            logger.debug(f"Finalizing successful retrieval for {ticket.data_file_path}")
            self.storage_manager.finalize(ticket, self.query, success=True)
