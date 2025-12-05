from __future__ import annotations
import time
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass

import pandas as pd

from . import logger
from .query import Query
from .setup import PipelineConfig


@dataclass
class RetrievalMeta:
    # Configuration parameters
    model: str
    level: str
    retrieval_mode: str
    format: str
    variables: list[str]
    issue_hours: list[str]
    lookback: int
    step_granularity: int
    issued: str
    area: str
    grid: str

    @classmethod
    def from_request(cls, request: dict, config: PipelineConfig) -> RetrievalMeta:
        return cls(
            model=config.model,
            level=config.level,
            retrieval_mode=config.retrieval_mode,
            format=config.format,
            variables=config.variables,
            issue_hours=config.issue_hours,
            lookback=config.lookback,
            step_granularity=config.step_granularity,
            issued=request["date"] + f" {request['time']}:00",
            area=request["area"],
            grid=request["grid"],
        )

    @property
    def id(self) -> str:
        hash_input = (
            f"{self.model}_{self.level}_{self.retrieval_mode}_"
            f"{','.join(self.variables)}_{','.join(self.issue_hours)}_"
            f"{self.lookback}_{self.step_granularity}_{self.issued}_"
            f"{self.area}_{self.grid}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

@dataclass
class RetrievalTicket:
    meta: RetrievalMeta
    data_file_path: Path
    query_file_path: Path
    cost_check_file_path: Path
    now: int

    @property
    def id(self) -> str:
        hash_input = (f"{self.meta.id}_{self.now}_{self.data_file_path}_{self.query_file_path}")
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

class StorageManager:

    def __init__(self, base_folder: Path):
        self.base_folder = base_folder
        self.base_folder.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_folder / "index.csv"

    def allocate(self, meta: RetrievalMeta, query: Query) -> RetrievalTicket:
        """ Allocate storage for a new retrieval based on its metadata. """
        data_subfolder = self.base_folder / "data"
        queries_subfolder = self.base_folder / "queries"
        queries_cost_subfolder = self.base_folder / "queries_cost"
        data_subfolder.mkdir(parents=True, exist_ok=True)
        queries_subfolder.mkdir(parents=True, exist_ok=True)
        queries_cost_subfolder.mkdir(parents=True, exist_ok=True)

        now_timestamp = int(time.time())

        if meta.format == "netcdf":
            logger.debug("Allocating .nc data file")
            data_file_path = data_subfolder / f"ecmwf_{meta.model}_{meta.level}_{meta.issued.replace('/', '_')}_{now_timestamp}.nc"
        elif meta.format == "grib2":
            logger.debug("Allocating .grib data file")
            data_file_path = data_subfolder / f"ecmwf_{meta.model}_{meta.level}_{meta.issued.replace('/', '_')}_{now_timestamp}.grib"
        else:
            logger.error(f"Unsupported format: {meta.format}")
            raise NotImplementedError(f"Format {meta.format} not supported")
        logger.debug(f"Allocating data storage at {data_file_path}")

        query_file_path = queries_subfolder / f"query_{query.id}.json"
        cost_check_file_path = queries_cost_subfolder / f"ecmwf_cost_{meta.model}_{meta.level}_{meta.issued.replace('/', '_')}_{now_timestamp}.txt"

        if data_file_path.exists():
            logger.error(f"File {data_file_path} already exists. Allocation failed.")
            raise FileExistsError(f"File {data_file_path} already exists.")
        if query_file_path.exists():
            logger.debug(f"File {query_file_path} already exists.")

        return RetrievalTicket(
            meta=meta,
            data_file_path=data_file_path,
            query_file_path=query_file_path,
            cost_check_file_path=cost_check_file_path,
            now=now_timestamp
        )

    def finalize(self, ticket: RetrievalTicket, query: Query, success: bool) -> None:
        """ Finalize the storage of a retrieval, updating the index. """
        if success:
            logger.info(f"Success, finalizing storage for {ticket.data_file_path}")
            self._save_query(query, ticket)
            self._add_index_entry(query, ticket)
        else:
            logger.info(f"Removing potential incomplete file {ticket.data_file_path}")
            if ticket.data_file_path.exists():
                ticket.data_file_path.unlink()

    def _save_query(self, query: Query, ticket: RetrievalTicket) -> None:
        """ Save the query metadata to a JSON file. """
        query_data = query.to_dict()
        with ticket.query_file_path.open("w") as f:
            json.dump(query_data, f, indent=4)
        logger.debug(f"Query saved at {ticket.query_file_path}")

    def _add_index_entry(self, query: Query, ticket: RetrievalTicket) -> None:
        """ Add an entry to the index file. """
        entry = {
            # File paths
            "data_file": str(ticket.data_file_path.relative_to(self.base_folder)),
            "query_file": str(ticket.query_file_path.relative_to(self.base_folder)),
            "cost_check_file": str(ticket.cost_check_file_path.relative_to(self.base_folder)),

            # IDs
            "retrieval_id": ticket.meta.id,
            "entry_id": ticket.id,
            "query_id": query.id,

            # Metadata (config)
            "model": ticket.meta.model,
            "level": ticket.meta.level,
            "retrieval_mode": ticket.meta.retrieval_mode,
            "issued": ticket.meta.issued,
            "lookback_hours": ticket.meta.lookback,
            "step_granularity": ticket.meta.step_granularity,
            "variables": ",".join(ticket.meta.variables),

            # Metadata (query computed)
            "grid": ticket.meta.grid,

            # Retrieval timestamp
            "timestamp": ticket.now,
        }
        df_entry = pd.DataFrame([entry])

        if self.index_file.exists():
            df_index = pd.read_csv(self.index_file)
            df_index = pd.concat([df_index, df_entry], ignore_index=True)
        else:
            df_index = df_entry

        df_index.to_csv(self.index_file, index=False)
        logger.debug(f"Index updated at {self.index_file}")
