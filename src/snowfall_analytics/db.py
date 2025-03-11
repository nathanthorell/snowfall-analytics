import types
from pathlib import Path
from typing import List

import duckdb

from .noaa import WeatherData, WeatherStation
from .sql_loader import SQLLoader


class WeatherDatabase:
    """Handles database operations for weather data using DuckDB"""

    def __init__(self, db_path: Path, sql_dir: Path | None = None):
        """
        Initialize database connection and schema

        Args:
            db_path: Path to DuckDB database file
            sql_dir: Path to SQL files directory
        """
        self.conn = duckdb.connect(str(db_path))

        if sql_dir is None:
            sql_dir = Path(__file__).parent / "sql"
        self.sql = SQLLoader(sql_dir)

        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize database schema from SQL files"""
        schema_files = ["schema/weather_station", "schema/weather_data"]
        for name in schema_files:
            self.conn.execute(self.sql.get_query(name))

    def upsert_station(self, station: WeatherStation) -> None:
        """
        Insert or update weather station information

        Args:
            station: WeatherStation object containing station information
        """
        self.conn.execute(
            self.sql.get_query("queries/upsert_weather_station"),
            (
                station.station_id,
                station.name,
                station.latitude,
                station.longitude,
                station.elevation,
            ),
        )

    def upsert_weather_data(self, data: List[WeatherData]) -> None:
        """
        Insert weather data records

        Args:
            data: List of WeatherData objects to insert
        """
        if not data:
            return

        # Convert data to list of tuples for bulk insert
        values = [
            (
                record.station_id,
                record.date,
                record.precipitation,
                record.precipitation_attributes,
                record.snowfall,
                record.snowfall_attributes,
                record.snow_depth,
                record.snow_depth_attributes,
                record.temp_max,
                record.temp_max_attributes,
                record.temp_min,
                record.temp_min_attributes,
            )
            for record in data
        ]

        self.conn.executemany(self.sql.get_query("queries/upsert_weather_data"), values)

    def close(self) -> None:
        """Close the database connection"""
        self.conn.close()

    def __enter__(self) -> "WeatherDatabase":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        self.close()
