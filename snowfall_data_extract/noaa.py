import asyncio
import logging
import time
import types
from datetime import date as Date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import httpx
from httpx import ConnectError, HTTPStatusError, RemoteProtocolError, TransportError
from pydantic import BaseModel, Field

from .config import StationConfig

logger = logging.getLogger(__name__)


class RateLimit:
    """Simple rate limiter to prevent API throttling"""

    def __init__(self, calls_per_minute: int = 5):
        """
        Initialize rate limiter

        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # seconds between calls
        self.last_call_time = 0.0

    async def wait(self) -> None:
        """Wait if needed to maintain the rate limit"""
        current_time = time.time()
        elapsed = current_time - self.last_call_time

        if elapsed < self.min_interval and self.last_call_time > 0:
            wait_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

        self.last_call_time = time.time()


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
        timeout: float = 60.0,
        max_retries: int = 3,
        calls_per_minute: int = 5,
    ):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries
        self.rate_limiter = RateLimit(calls_per_minute)

    async def _make_request(self, params: Dict[str, Any]) -> httpx.Response:
        retry_count = 0
        last_exception: Exception | None = None

        while retry_count <= self.max_retries:
            try:
                # Wait if needed to respect rate limits
                await self.rate_limiter.wait()

                # Make the request
                response = await self.client.get(self.base_url, params=params)
                response.raise_for_status()
                return response

            except (RemoteProtocolError, ConnectError, TransportError) as e:
                retry_count += 1
                last_exception = e

                if retry_count > self.max_retries:
                    break

                # Exponential backoff with jitter
                wait_time = 2**retry_count + (retry_count * 0.1)
                logger.warning(
                    f"Connection error, retrying in {wait_time:.2f}s "
                    f"(attempt {retry_count}/{self.max_retries}): {str(e)}"
                )
                await asyncio.sleep(wait_time)

            except HTTPStatusError as e:
                # Don't retry client errors (except 429 Too Many Requests)
                if e.response.status_code == 429:
                    retry_count += 1
                    last_exception = e

                    # Rate limit hit - back off significantly
                    wait_time = 30 * retry_count  # 30, 60, 90 seconds
                    logger.warning(f"Rate limit hit, backing off for {wait_time}s")
                    await asyncio.sleep(wait_time)

                    # Continue to retry
                    if retry_count <= self.max_retries:
                        continue

                # For 5xx errors, retry with backoff
                if 500 <= e.response.status_code < 600:
                    retry_count += 1
                    last_exception = e

                    if retry_count > self.max_retries:
                        break

                    wait_time = 2**retry_count
                    logger.warning(
                        f"Server error {e.response.status_code}, retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # Other client errors - don't retry
                    raise

        # If we got here, all retries failed
        if last_exception:
            raise last_exception

        # This should never happen, but just in case
        raise RuntimeError("Request failed with no exception")

    async def get_station_data(
        self, station_id: str, start_date: Date, end_date: Date
    ) -> Tuple[List[WeatherData], Optional[WeatherStation]]:
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

        try:
            response = await self._make_request(params)
            data = response.json()

            if not data:
                return [], None

            weather_data = [WeatherData.model_validate(row) for row in data]
            station_info = WeatherStation.model_validate(data[0]) if data else None

            return weather_data, station_info

        except Exception as e:
            logger.error(f"Failed to fetch data for station {station_id}: {str(e)}")
            raise

    async def get_all_stations_data(
        self, config: StationConfig
    ) -> List[Tuple[List[WeatherData], Optional[WeatherStation]]]:
        results: List[Tuple[List[WeatherData], Optional[WeatherStation]]] = []
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
