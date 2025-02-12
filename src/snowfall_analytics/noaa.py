import types
from datetime import date as Date
from decimal import Decimal
from typing import List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

from snowfall_analytics.config import StationConfig


class WeatherStation(BaseModel):
    """Model for a weather station"""

    station_id: str = Field(alias="STATION")
    name: str = Field(alias="NAME")
    latitude: Decimal = Field(alias="LATITUDE")
    longitude: Decimal = Field(alias="LONGITUDE")
    elevation: Decimal = Field(alias="ELEVATION")


class WeatherData(BaseModel):
    """Model for daily weather data"""

    station_id: str = Field(alias="STATION")
    date: Date = Field(alias="DATE")
    precipitation: Optional[Decimal] = Field(default=None, alias="PRCP")
    precipitation_attributes: Optional[str] = Field(default=None, alias="PRCP_ATTRIBUTES")
    snowfall: Optional[Decimal] = Field(default=None, alias="SNOW")
    snowfall_attributes: Optional[str] = Field(default=None, alias="SNOW_ATTRIBUTES")
    snow_depth: Optional[Decimal] = Field(default=None, alias="SNWD")
    snow_depth_attributes: Optional[str] = Field(default=None, alias="SNWD_ATTRIBUTES")
    temp_max: Optional[int] = Field(default=None, alias="TMAX")
    temp_max_attributes: Optional[str] = Field(default=None, alias="TMAX_ATTRIBUTES")
    temp_min: Optional[int] = Field(default=None, alias="TMIN")
    temp_min_attributes: Optional[str] = Field(default=None, alias="TMIN_ATTRIBUTES")


class NOAAClient:
    """Client for NOAA's Climate Data API"""

    def __init__(
        self,
        base_url: str = "https://www.ncei.noaa.gov/access/services/data/v1",
        timeout: float = 30.0,
    ):
        """
        Initialize the NOAA API client

        Args:
            base_url: Base URL for the NOAA API
            timeout: Timeout for HTTP requests in seconds
        """
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)

    async def get_station_data(
        self, station_id: str, start_date: Date, end_date: Date
    ) -> Tuple[List[WeatherData], Optional[WeatherStation]]:
        """
        Fetch weather data for a specific station and date range

        Args:
            station_id: NOAA station identifier
            start_date: Start date for data collection
            end_date: End date for data collection

        Returns:
            Tuple of (weather data list, station information)
        """
        params = {
            "dataset": "daily-summaries",
            "stations": station_id,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dataTypes": "SNOW,PRCP,SNWD,TAVG,TMAX,TMIN",
            "includeStationLocation": "1",
            "includeStationName": "true",
            "includeAttributes": "true",
            "format": "json",
        }

        response = await self.client.get(self.base_url, params=params)
        response.raise_for_status()

        data = response.json()
        if not data:
            return [], None

        weather_data = [WeatherData.model_validate(row) for row in data]
        station_info = WeatherStation.model_validate(data[0]) if data else None

        return weather_data, station_info

    async def get_all_stations_data(
        self, config: StationConfig
    ) -> List[Tuple[List[WeatherData], Optional[WeatherStation]]]:
        """
        Fetch weather data for all stations in config

        Args:
            config: Station config containing stations and date range

        Returns:
            List of (weather data, station info) tuples for each station
        """
        results = []
        for station_id in config.stations:
            station_data = await self.get_station_data(
                station_id, config.start_date, config.end_date
            )
            results.append(station_data)
        return results

    async def close(self) -> None:
        """Close the HTTP client session"""
        await self.client.aclose()

    async def __aenter__(self) -> "NOAAClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.close()
