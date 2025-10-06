from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import yaml

from . import logger


@dataclass
class VariablesConfig:
    surface: list[str]
    model: list[str]

@dataclass
class Config:
    """Configuration for ECMWF requests."""
    variables: VariablesConfig
    lookback: int
    step_granularity: int # yaml key: step-granularity

    overwrite: bool = True # Not yet implemented
    max_points_per_request: int = 2000 # Not yet implemented

    def __post_init__(self):
        if self.lookback <= 0:
            logger.error("Lookback must be a positive integer.")
            raise ValueError("Lookback must be a positive integer.")
        if self.lookback > 240:
            logger.error("Lookback cannot exceed 240 hours (10 days).")
            raise ValueError("Lookback cannot exceed 240 hours (10 days).") 
        if self.step_granularity <= 0:
            logger.error("Step granularity must be a positive integer.")
            raise ValueError("Step granularity must be a positive integer.")

    @staticmethod
    def from_dict(config_dict: dict) -> Config:
        variables = VariablesConfig(**config_dict.get("variables", {}))
        lookback = config_dict["lookback"]
        step_granularity = config_dict["step-granularity"]
        overwrite = config_dict.get("overwrite", True)
        max_points_per_request = config_dict.get("max-points-per-request", 2000)
        return Config(
            variables=variables,
            lookback=lookback,
            step_granularity=step_granularity,
            overwrite=overwrite,
            max_points_per_request=max_points_per_request
        )

    @staticmethod
    def from_yaml(path: str | Path) -> Config:
        path = Path(path)
        with path.open("r") as f:
            config_dict = yaml.safe_load(f)

        return Config.from_dict(config_dict)
