from pathlib import Path
from datetime import timedelta

from ecmwfapi import ECMWFService

from . import logger
from .setup import Config, Query
from .utils.geometry import get_smallest_bounding_box
from .setup.query import PointCloud
from .setup.logging import ecmwf_log
from .storage import StorageManager, RetrievalMeta



class ECMWFClient:
    """ Client for retrieving ECMWF data. """

    def __init__(self, output_folder: Path):
        logger.info("Initializing ECMWF Client...")
        self.server = ECMWFService("mars", log=ecmwf_log)
        self.storage_manager = StorageManager(output_folder)
        self.output_folder = output_folder
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.index_file = self.output_folder / "index.csv"

    def get_forecast(
        self,
        config: Config,
        query: Query,
        level: str,
        dry_run: bool = False
    ) -> None:
        """ Retrieve forecast data for given points and date range. """
        logger.info(
            f"Retrieving forecast data for points: {query.points}, "
            f"from {query.time_range.start} to {query.time_range.end}"
        )

        base_request = self._build_base_request(config, query, level)
        current_dt = query.time_range.start
        while current_dt <= query.time_range.end:
            logger.info(f"Processing date: {current_dt.date()}")
            for issued_time in ["00", "12"]: # TODO - Find a way to get 06 and 18 as well (currently not working)
                request = base_request.copy()
                request["date"] = current_dt.strftime("%Y-%m-%d")
                request["time"] = issued_time

                issued = request["date"] + f" {issued_time}:00"

                retrieval_meta = self._make_retrieval_meta(
                    issued, query, config, level
                )
                ticket = self.storage_manager.allocate(retrieval_meta)

                try:
                    logger.debug(f"ECMWF request: {request}")
                    self.server.execute(request, ticket.data_file_path)
                    if not dry_run:
                        logger.debug(f"Finalizing retrieval for {ticket.data_file_path}")
                        self.storage_manager.finalize(ticket, query, success=True)
                    else:
                        logger.info(f"Dry run enabled, skipping finalize for {ticket.data_file_path}")
                        self.storage_manager.finalize(ticket, query, success=False)
                except Exception as e:
                    logger.error(f"Error retrieving data for {issued}: {e}")
                    self.storage_manager.finalize(ticket, query, success=False)

            current_dt += timedelta(days=1)

    def _build_base_request(self, config: Config, query: Query, level: str) -> dict:
        grid_res = 0.1
        area_str, grid_str = self.get_area_grid(query.points, grid_res)

        step_str = f"0/to/{config.lookback}/by/{config.step_granularity}"

        base = {
            "class": "od",
            "stream": "oper",
            "expver": "1",
            "type": "fc",
            "step": step_str,
            "area": area_str,
            "grid": grid_str,
            "format": "netcdf",
        }

        if level == "surface":
            base.update({"levtype": "sfc", "param": config.variables.surface})
        elif level == "model":
            base.update({
                "levtype": "ml",
                "levelist": "130/to/137",
                "param": config.variables.model,
            })
        else:
            raise ValueError("level_type must be 'sfc' or 'ml'")

        logger.debug(f"Base request: {base}")
        return base

    def _make_retrieval_meta(
        self, issued: str, query: Query, config: Config, level: str
    ) -> RetrievalMeta:
        return RetrievalMeta(
            issued=issued,
            level=level,
            min_lat=min(query.points.lats),
            max_lat=max(query.points.lats),
            min_lon=min(query.points.lons),
            max_lon=max(query.points.lons),
            grid_res=0.1,
            lookback=config.lookback,
            step_granularity=config.step_granularity,
        )

    @staticmethod
    def get_area_grid(points: PointCloud, grid_res: float) -> tuple[str, str]:
        lat_min, lat_max, lon_min, lon_max = get_smallest_bounding_box(points, grid_res)
        area_str = f"{lat_max}/{lon_min}/{lat_min}/{lon_max}"
        grid_str = f"{grid_res}/{grid_res}"
        return area_str, grid_str
