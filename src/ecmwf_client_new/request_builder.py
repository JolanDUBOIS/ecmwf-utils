from __future__ import annotations
from datetime import timedelta

from . import logger
from ..setup import PipelineConfig
from ..query import Query, PointCloud
from ..utils.geometry import get_smallest_bounding_box


class ECMWFRequestsBuilder:
    """
    Builds ECMWF MARS request dictionaries for the given configuration and query.

    Each request corresponds to a combination of:
        - a spatial subset (grid or individual point)
        - a forecast issuance time
        - a date in the specified time range.

    Returns a list of requests ready to be passed to ECMWF data services.
    """

    grid_resolution: float = 0.1
    point_resolution: float = 0.01

    def __init__(self, config: PipelineConfig, query: Query):
        self.config = config
        self.query = query

        self._base_request = None

    @property
    def base_request(self) -> dict:
        """ TODO """
        if self._base_request is not None:
            return self._base_request

        step_str = f"0/to/{self.config.lookback}/by/{self.config.step_granularity}"
        base = {
            "class": "od",
            "format": "netcdf",
            "levtype": "sfc",
            "step": step_str,
            "param": self.config.variables
        }

        if self.config.model == "hres":
            base.update({
                "stream": "oper",
                "type": "fc"
            })
        elif self.config.model == "ens":
            base.update({
                "stream": "enfo",
                "type": "pf",
                "number": "1/to/50/by/1",
            })
        else:
            logger.error(f"Unsupported model: {self.config.model}")
            raise NotImplementedError(f"Model {self.config.model} not supported")

        if self.config.level != "surface":
            logger.error(f"Unsupported level type: {self.config.level}")
            raise ValueError(f"Unsupported level type: {self.config.level}")

        self._base_request = base
        logger.debug(f"Base request: {self._base_request}")
        return self._base_request

    def build_requests(self) -> list[dict]:
        """ TODO """
        requests = []
        grid_requests = self._build_grid_requests()

        current_dt = self.query.time_range.start
        while current_dt <= self.query.time_range.end:
            logger.debug(f"Building requests for datetime: {current_dt.date()}")
            request_date = current_dt.strftime("%Y-%m-%d")
            
            for issued_time in self.config.issue_times:            
                for req in grid_requests:
                    requests.append({**req, "date": request_date, "time": issued_time})
            
            current_dt += timedelta(days=1)

        return requests

    def _build_grid_requests(self) -> list[dict]:
        """ Return static ECMWF requests for all points or grids. """
        base = self.base_request.copy()
        mode = self.config.retrieval_mode

        if mode == "grid":
            grid_res = self.grid_resolution
            area_str, grid_str = self.get_area_grid(self.query.points, grid_res)
            return [{**base, "area": area_str, "grid": grid_str}]

        elif mode == "point":
            point_res = self.point_resolution
            return [
                {**base, "area": f"{p.lat}/{p.lon}/{p.lat}/{p.lon}", "grid": f"{point_res}/{point_res}"}
                for p in self.query.points.points
            ]

        logger.error(f"Unsupported retrieval mode: {mode}")
        raise NotImplementedError(f"Retrieval mode {mode} not supported")

    @staticmethod
    def get_area_grid(points: PointCloud, grid_res: float) -> tuple[str, str]:
        """ TODO """
        lat_min, lat_max, lon_min, lon_max = get_smallest_bounding_box(points, grid_res)
        area_str = f"{lat_max}/{lon_min}/{lat_min}/{lon_max}"
        grid_str = f"{grid_res}/{grid_res}"
        return area_str, grid_str
