#!/usr/bin/env python3
import argparse
import asyncio
import logging
from pathlib import Path

from snowfall_analytics.config import load_config
from snowfall_analytics.db import WeatherDatabase
from snowfall_analytics.noaa import NOAAClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_station_data(
    station_id: str, client: NOAAClient, db: WeatherDatabase, debug: bool = False
) -> None:
    """Fetch and store data for a single station"""
    try:
        config = load_config()
        weather_data, station_info = await client.get_station_data(
            station_id, config.stations.start_date, config.stations.end_date
        )

        if station_info:
            db.upsert_station(station_info)
            logger.info(f"Upserted station info for {station_id}")

        if weather_data:
            db.upsert_weather_data(weather_data)
            logger.info(f"Upserted {len(weather_data)} records for {station_id}")

            if debug:
                print(f"\nSample data for {station_id}:")
                for record in weather_data[:5]:  # Show first 5 records
                    print(f"Date: {record.date}")
                    print(f"Snowfall: {record.snowfall or 'N/A'}")
                    print(f"Snow Depth: {record.snow_depth or 'N/A'}")
                    print(f"Temp Max: {record.temp_max or 'N/A'}")
                    print(f"Temp Min: {record.temp_min or 'N/A'}")
                    print("-" * 40)

    except Exception as e:
        logger.error(f"Error processing station {station_id}: {str(e)}")
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Snowfall Analytics CLI")
    parser.add_argument(
        "--station", help="Single station ID to fetch (defaults to config file)"
    )
    parser.add_argument("--debug", action="store_true", help="Show detailed debug information")
    parser.add_argument(
        "--data-dir", type=Path, default="data", help="Directory for data storage"
    )

    args = parser.parse_args()

    try:
        args.data_dir.mkdir(parents=True, exist_ok=True)

        config = load_config(data_dir=args.data_dir)
        stations = [args.station] if args.station else config.stations.stations

        with WeatherDatabase(config.db_path) as db:

            async def run() -> None:
                async with NOAAClient() as client:
                    await asyncio.gather(
                        *(fetch_station_data(s, client, db, args.debug) for s in stations)
                    )

            asyncio.run(run())

        logger.info("Data fetch completed successfully")

    except Exception as e:
        logger.error(f"Error during data fetch: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
