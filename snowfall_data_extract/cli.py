#!/usr/bin/env python3
import argparse
import asyncio
import logging
from pathlib import Path

import httpcore

from .config import Config, load_config
from .db import WeatherDatabase
from .noaa import NOAAClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_station_data(
    station_id: str,
    client: NOAAClient,
    db: WeatherDatabase,
    config: Config,
    debug: bool = False,
) -> None:
    """Fetch and store data for a single station"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
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
            return
        except httpcore.ReadError as e:
            retry_count += 1
            if retry_count >= max_retries:
                e_str = f"Error processing station {station_id} after {max_retries} retries"
                logger.error(f"{e_str}: {str(e)}")
                raise

            wait_time = 2**retry_count  # backoff
            retry_str = f"ReadError for {station_id}, retrying in {wait_time}s"
            attempt_str = f"(attempt {retry_count}/{max_retries})"
            logger.warning(f"{retry_str} {attempt_str}")
            await asyncio.sleep(wait_time)

        except Exception as e:
            logger.error(f"Error processing station {station_id}: {str(e)}", exc_info=True)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Snowfall Analytics CLI")
    parser.add_argument(
        "--station", help="Single station ID to fetch (defaults to config file)"
    )
    parser.add_argument("--debug", action="store_true", help="Show detailed debug information")
    parser.add_argument(
        "--data-dir", type=Path, default=Path("data"), help="Directory for database storage"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file (defaults to data-dir/config.json)",
        default=None,
        required=False,
    )

    args = parser.parse_args()

    try:
        config = load_config(data_dir=args.data_dir)
        stations = [args.station] if args.station else config.stations.stations

        if not stations:
            logger.error("No stations specified in config or command line")
            exit(1)

        with WeatherDatabase(config.db_path) as db:

            async def run() -> None:
                async with NOAAClient() as client:
                    try:
                        await asyncio.gather(
                            *(
                                fetch_station_data(s, client, db, config, args.debug)
                                for s in stations
                            )
                        )
                    except Exception as e:
                        logger.error(f"Error in run: {str(e)}", exc_info=True)
                        raise

            asyncio.run(run())

        logger.info("Data fetch completed successfully")

    except Exception as e:
        logger.error(f"Error during data fetch: {str(e)}", exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
