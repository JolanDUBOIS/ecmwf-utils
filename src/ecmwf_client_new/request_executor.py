import traceback

from ecmwfapi import ECMWFService

from . import logger
from ..query import Query
from ..setup import PipelineConfig
from ..storage import StorageManager, RetrievalMeta
from ..setup.logging import ecmwf_log


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
    ) -> None:
        """ Retrieve forecast data for given points and date range. """
        logger.info(f"Retrieving forecast with request: {request}")
        meta = RetrievalMeta.from_request(request, self.config)
        ticket = self.storage_manager.allocate(meta, self.query)

        try:
            logger.debug(f"ECMWF request: {request}")
            self.server.execute(request, ticket.data_file_path)
            if not dry_run:
                logger.debug(f"Finalizing retrieval for {ticket.data_file_path}")
                self.storage_manager.finalize(ticket, self.query, success=True)
            else:
                logger.info(f"Dry run enabled, skipping finalize for {ticket.data_file_path}")
                self.storage_manager.finalize(ticket, self.query, success=False)
        except Exception as e:
            logger.error(f"Error retrieving data for: {e}")
            logger.debug(traceback.format_exc())
            self.storage_manager.finalize(ticket, self.query, success=False)
