from datetime import date
from decimal import Decimal

import httpx
import pytest
import respx

from snowfall_analytics.noaa import NOAAClient, WeatherData, WeatherStation


@pytest.fixture
def mock_station_response() -> list[dict[str, str]]:
    """Sample station response data"""
    return [
        {
            "STATION": "USW00014838",
            "NAME": "MINNEAPOLIS-ST PAUL INTERNATIONAL AIRPORT, MN US",
            "LATITUDE": "44.8831",
            "LONGITUDE": "-93.2289",
            "ELEVATION": "265.8",
            "DATE": "2024-01-01",
            "PRCP": "0.02",
            "PRCP_ATTRIBUTES": ",,",
            "SNOW": "0.5",
            "SNOW_ATTRIBUTES": ",,",
            "SNWD": "4.0",
            "SNWD_ATTRIBUTES": ",,",
            "TMAX": "28",
            "TMAX_ATTRIBUTES": ",,",
            "TMIN": "15",
            "TMIN_ATTRIBUTES": ",,",
        }
    ]


@pytest.mark.asyncio
async def test_get_station_data(mock_station_response: list[dict[str, str]]) -> None:
    """Test fetching station data"""
    with respx.mock() as respx_mock:
        # Mock NOAA API
        route = respx_mock.get("https://www.ncei.noaa.gov/access/services/data/v1").mock(
            return_value=httpx.Response(200, json=mock_station_response)
        )

        async with NOAAClient() as client:
            weather_data, station_info = await client.get_station_data(
                "USW00014838", date(2024, 1, 1), date(2024, 1, 1)
            )

        # Verify request parameters
        assert route.called
        params = dict(route.calls[0].request.url.params)
        assert params["dataset"] == "daily-summaries"
        assert params["stations"] == "USW00014838"
        assert params["startDate"] == "2024-01-01"
        assert params["endDate"] == "2024-01-01"

        # Verify weather data
        assert len(weather_data) == 1
        data = weather_data[0]
        assert isinstance(data, WeatherData)
        assert data.station_id == "USW00014838"
        assert data.date == date(2024, 1, 1)
        assert data.snowfall == Decimal("0.5")
        assert data.snow_depth == Decimal("4.0")
        assert data.temp_max == 28
        assert data.temp_min == 15

        # Verify station info
        assert isinstance(station_info, WeatherStation)
        assert station_info.station_id == "USW00014838"
        assert station_info.name == "MINNEAPOLIS-ST PAUL INTERNATIONAL AIRPORT, MN US"
        assert station_info.latitude == Decimal("44.8831")
        assert station_info.longitude == Decimal("-93.2289")
        assert station_info.elevation == Decimal("265.8")


@pytest.mark.asyncio
async def test_get_station_data_empty_response() -> None:
    """Test handling empty response from API"""
    with respx.mock() as respx_mock:
        respx_mock.get("https://www.ncei.noaa.gov/access/services/data/v1").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with NOAAClient() as client:
            weather_data, station_info = await client.get_station_data(
                "NONEXISTENT", date(2024, 1, 1), date(2024, 1, 1)
            )

        assert weather_data == []
        assert station_info is None


@pytest.mark.asyncio
async def test_get_station_data_error() -> None:
    """Test handling API errors"""
    with respx.mock() as respx_mock:
        respx_mock.get("https://www.ncei.noaa.gov/access/services/data/v1").mock(
            return_value=httpx.Response(500)
        )

        with pytest.raises(httpx.HTTPStatusError):
            async with NOAAClient() as client:
                await client.get_station_data(
                    "USW00014838", date(2024, 1, 1), date(2024, 1, 1)
                )
