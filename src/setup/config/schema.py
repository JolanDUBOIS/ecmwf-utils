from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from .defaults import (
    DEFAULT_LOG_PATH, DEFAULT_QUERY_PATH,
    DEFAULT_LANDING_PATH, DEFAULT_STAGING_PATH,
    DEFAULT_MODEL, DEFAULT_LEVEL, ALLOWED_MODELS,
    DEFAULT_LOOKBACK, DEFAULT_STEP_GRANULARITY,
    DEFAULT_RETRIEVAL_MODE, ALLOWED_RETRIEVAL_MODES,
    DEFAULT_FORMAT, ALLOWED_FORMATS,
)


@dataclass
class PipelineConfig:
    # Pipeline settings
    model: str = DEFAULT_MODEL
    level: str = DEFAULT_LEVEL
    landing_path: Path = Path(DEFAULT_LANDING_PATH)
    staging_path: Path = Path(DEFAULT_STAGING_PATH)
    
    # Logging settings
    logging_path: Path = Path(DEFAULT_LOG_PATH)

    # Query settings
    retrieval_mode: str = DEFAULT_RETRIEVAL_MODE
    format: str = DEFAULT_FORMAT
    query_path: Path = Path(DEFAULT_QUERY_PATH)
    variables: list[str] = field(default_factory=list)
    issue_hours: list[str] = field(default_factory=list)
    lookback: int = DEFAULT_LOOKBACK
    step_granularity: int = DEFAULT_STEP_GRANULARITY

    def __post_init__(self):
        # Ensure paths are Path objects
        if not isinstance(self.landing_path, Path):
            self.landing_path = Path(self.landing_path)
        if not isinstance(self.staging_path, Path):
            self.staging_path = Path(self.staging_path)
        if not isinstance(self.logging_path, Path):
            self.logging_path = Path(self.logging_path)
        if not isinstance(self.query_path, Path):
            self.query_path = Path(self.query_path)
        
        # Validate model
        if self.model not in ALLOWED_MODELS:
            raise ValueError(f"Model '{self.model}' is not allowed. Choose from {ALLOWED_MODELS}.")

        # Validate retrieval mode
        if self.retrieval_mode not in ALLOWED_RETRIEVAL_MODES:
            raise ValueError(f"Retrieval mode '{self.retrieval_mode}' is not allowed. Choose from {ALLOWED_RETRIEVAL_MODES}.")

        # Validate format
        if self.format not in ALLOWED_FORMATS:
            raise ValueError(f"Format '{self.format}' is not allowed. Choose from {ALLOWED_FORMATS}.")
