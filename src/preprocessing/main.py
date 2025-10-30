from pathlib import Path

import numpy as np
import xarray as xr
import pandas as pd

from . import logger
from ..setup import PipelineConfig
from ..query import Query


def run_preprocessing(
    config: PipelineConfig,
):
    """ TODO """
    landing_folder = Path(config.landing_path)
    staging_file_path = landing_folder / "main.csv"

    # Validate paths and read data
    if staging_file_path.suffix != ".csv":
        logger.error(f"Staging file {staging_file_path} is not a .csv file.")
        raise ValueError(f"Staging file {staging_file_path} is not a .csv file.")
    try:
        staging_df = pd.read_csv(staging_file_path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        logger.info(f"Initializing empty staging file at {staging_file_path}.")
        staging_file_path.parent.mkdir(parents=True, exist_ok=True)
        staging_file_path.touch(exist_ok=True)
        staging_df = pd.DataFrame(columns=['entry_id'])
    logger.info(f"Read {len(staging_df)} entries from staging file {staging_file_path}.")

    index_file = landing_folder / "index.csv"
    if not index_file.exists():
        logger.error(f"Index file {index_file} does not exist. Cannot preprocess.")
        raise FileNotFoundError(f"Index file {index_file} does not exist. Cannot preprocess.")
    index_df = pd.read_csv(index_file)
    logger.info(f"Read {len(index_df)} entries from index file {index_file}.")

    # Iterate over index
    for _, row in index_df.iterrows():
        try:
            if row['entry_id'] in staging_df['entry_id'].values:
                logger.debug(f"Entry {row['entry_id']} already in staging. Skipping.")
                continue
            
            query_path = landing_folder / row['query_file']
            if not query_path.exists():
                logger.error(f"Query file {query_path} does not exist. Skipping entry {row['entry_id']}.")
                continue
            query = Query.from_json(query_path)
            logger.debug(f"Loaded query {query.id} from {query_path}.")

            data_path = landing_folder / row['data_file']
            if not data_path.exists():
                logger.error(f"Data file {data_path} does not exist. Skipping entry {row['entry_id']}.")
                continue
            data = xr.open_dataset(data_path)
            logger.debug(f"Opened data file {data_path} with variables: {list(data.data_vars)}.")

            # Interpolation
            lats, lons = np.array(query.points.lats), np.array(query.points.lons)
            data_interpolated = data.interp(
                latitude=xr.DataArray(lats, dims="points"),
                longitude=xr.DataArray(lons, dims="points"),
            )
            df = data_interpolated.to_dataframe().reset_index()

            # Add metadata
            df['entry_id'] = row['entry_id']
            df['query_id'] = row['entry_id']
            df['retrieval_id'] = row['retrieval_id']
            df['issued'] = row['issued']
            df['level'] = row['level_type']
            df['data_type'] = row['data_type']
            df['lookback_hours'] = row['lookback_hours']
            df['step_granularity'] = row['step_granularity']
            df['timestamp'] = row['timestamp']

            # Concatenate to staging
            staging_df = pd.concat([staging_df, df], ignore_index=True)
            logger.info(f"Processed entry {row['entry_id']} and added {len(df)} rows to staging.")
            data.close()
        
        except Exception as e:
            logger.error(f"Error processing entry {row['entry_id']}: {e}")
            raise e

    # Save staging
    staging_df.to_csv(staging_file_path, index=False)
    logger.info(f"Saved {len(staging_df)} total entries to staging file {staging_file_path}.")
