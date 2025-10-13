import time
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass

import pandas as pd

from . import logger
from .setup import Query


@dataclass
class RetrievalMeta:
    issued: str
    grid_res: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    lookback: int
    step_granularity: int
    level: str

    @property
    def id(self) -> str:
        hash_input = (
            f"{self.issued}_{self.grid_res}_{self.min_lat}_{self.max_lat}_"
            f"{self.min_lon}_{self.max_lon}_{self.lookback}_{self.step_granularity}_{self.level}"
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

@dataclass
class RetrievalTicket:
    meta: RetrievalMeta
    data_file_path: Path
    query_file_path: Path
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
        data_subfolder = self.base_folder / "data" / meta.level
        queries_subfolder = self.base_folder / "queries"
        data_subfolder.mkdir(parents=True, exist_ok=True)
        queries_subfolder.mkdir(parents=True, exist_ok=True)

        now_timestamp = int(time.time())

        data_file_path = data_subfolder / f"ecmwf_fc_{meta.level}_{meta.issued}_{now_timestamp}.nc"
        logger.debug(f"Allocating data storage at {data_file_path}")
        query_file_path = queries_subfolder / f"query_{query.id}.json"

        if data_file_path.exists():
            logger.error(f"File {data_file_path} already exists. Allocation failed.")
            raise FileExistsError(f"File {data_file_path} already exists.")
        if query_file_path.exists():
            logger.debug(f"File {query_file_path} already exists.")

        return RetrievalTicket(
            meta=meta,
            data_file_path=data_file_path,
            query_file_path=query_file_path,
            now=now_timestamp
        )

    def finalize(self, ticket: RetrievalTicket, query: Query, success: bool) -> None:
        """ Finalize the storage of a retrieval, updating the index. """
        if success:
            logger.info(f"Success, finalizing storage for {ticket.data_file_path}")
            self._save_query(query, ticket)
            self._add_index_entry(query, ticket)
        else:
            logger.info(f"Failure, removing potential incomplete file {ticket.data_file_path}")
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
            "data_file": str(ticket.data_file_path.relative_to(self.base_folder)),
            "query_file": str(ticket.query_file_path.relative_to(self.base_folder)),
            "issued": ticket.meta.issued,
            "data_type": "fc",
            "level_type": ticket.meta.level,
            "lat_min": ticket.meta.min_lat,
            "lat_max": ticket.meta.max_lat,
            "lon_min": ticket.meta.min_lon,
            "lon_max": ticket.meta.max_lon,
            "grid_res": ticket.meta.grid_res,
            "lookback_hours": ticket.meta.lookback,
            "step_granularity": ticket.meta.step_granularity,
            "timestamp": ticket.now,
            "retrieval_id": ticket.meta.id,
            "entry_id": ticket.id,
            "query_id": query.id,
        }
        df_entry = pd.DataFrame([entry])

        if self.index_file.exists():
            df_index = pd.read_csv(self.index_file)
            df_index = pd.concat([df_index, df_entry], ignore_index=True)
        else:
            df_index = df_entry

        df_index.to_csv(self.index_file, index=False)
        logger.debug(f"Index updated at {self.index_file}")
