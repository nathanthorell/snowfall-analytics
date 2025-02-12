from datetime import date
from pathlib import Path
from typing import List

from pydantic import BaseModel, DirectoryPath, Field


class StationConfig(BaseModel):
    """Config for weather stations to collect data from"""

    stations: List[str] = Field(description="List of NOAA station IDs")
    start_date: date = Field(description="Start date for data collection")
    end_date: date = Field(description="End date for data collection")


class Config(BaseModel):
    """Main config for the snowfall analytics application"""

    data_dir: DirectoryPath = Field(
        default=Path("data"),
        description="Directory for storing DuckDB database and other data files",
    )
    stations: StationConfig

    @property
    def db_path(self) -> Path:
        """Get the path to the DuckDB database file"""
        return self.data_dir / "snowfall.duckdb"

    @classmethod
    def from_files(
        cls,
        data_dir: Path | str = "data",
        stations_config: Path | str = "config/config.json",
    ) -> "Config":
        """
        Load config from files

        Args:
            data_dir: Path to data directory
            stations_config: Path to stations configuration JSON file
        """
        stations = StationConfig.model_validate_json(Path(stations_config).read_text())
        return cls(data_dir=Path(data_dir), stations=stations)
