import tempfile
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Generator

import duckdb
import pytest

from snowfall_analytics.db import WeatherDatabase
from snowfall_analytics.noaa import WeatherData, WeatherStation


@pytest.fixture
def sql_dir(tmp_path: Path) -> Path:
    """Create temporary SQL directory with required files"""
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()

    # Create schema directory and files
    schema_dir = sql_dir / "schema"
    schema_dir.mkdir()

    (schema_dir / "weather_station.sql").write_text("""
    CREATE TABLE IF NOT EXISTS weather_station (
        station_id VARCHAR NOT NULL,
        station_name VARCHAR NOT NULL,
        latitude DECIMAL,
        longitude DECIMAL,
        elevation DECIMAL,
        PRIMARY KEY (station_id)
    );
    """)

    (schema_dir / "weather_data.sql").write_text("""
    CREATE TABLE IF NOT EXISTS weather_data (
        station_id VARCHAR NOT NULL,
        date DATE NOT NULL,
        precipitation DECIMAL,
        precipitation_attributes VARCHAR,
        snowfall DECIMAL,
        snowfall_attributes VARCHAR,
        snow_depth DECIMAL,
        snow_depth_attributes VARCHAR,
        temp_max INTEGER,
        temp_max_attributes VARCHAR,
        temp_min INTEGER,
        temp_min_attributes VARCHAR,
        PRIMARY KEY (station_id, date)
    );
    """)

    # Create queries directory and files
    queries_dir = sql_dir / "queries"
    queries_dir.mkdir()

    (queries_dir / "upsert_weather_station.sql").write_text("""
    INSERT OR REPLACE INTO weather_station (
        station_id,
        station_name,
        latitude,
        longitude,
        elevation
    ) VALUES (?, ?, ?, ?, ?);
    """)

    (queries_dir / "upsert_weather_data.sql").write_text("""
    INSERT OR REPLACE INTO weather_data (
        station_id,
        date,
        precipitation,
        precipitation_attributes,
        snowfall,
        snowfall_attributes,
        snow_depth,
        snow_depth_attributes,
        temp_max,
        temp_max_attributes,
        temp_min,
        temp_min_attributes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """)

    return sql_dir


@pytest.fixture
def sample_station() -> WeatherStation:
    """Create sample weather station data"""
    return WeatherStation(
        STATION="USW00014838",
        NAME="MINNEAPOLIS-ST PAUL INTERNATIONAL AIRPORT, MN US",
        LATITUDE=Decimal("44.883"),
        LONGITUDE=Decimal("-93.229"),
        ELEVATION=Decimal("265.800"),
    )


@pytest.fixture
def sample_weather_data() -> list[WeatherData]:
    """Create sample weather data records"""
    return [
        WeatherData(
            STATION="USW00014838",
            DATE=date(2024, 1, 1),
            PRCP=Decimal("0.02"),
            PRCP_ATTRIBUTES=",,",
            SNOW=Decimal("0.5"),
            SNOW_ATTRIBUTES=",,",
            SNWD=Decimal("4.0"),
            SNWD_ATTRIBUTES=",,",
            TMAX=28,
            TMAX_ATTRIBUTES=",,",
            TMIN=15,
            TMIN_ATTRIBUTES=",,",
        ),
        WeatherData(
            STATION="USW00014838",
            DATE=date(2024, 1, 2),
            PRCP=Decimal("0.00"),
            PRCP_ATTRIBUTES=",,",
            SNOW=Decimal("0.0"),
            SNOW_ATTRIBUTES=",,",
            SNWD=Decimal("4.0"),
            SNWD_ATTRIBUTES=",,",
            TMAX=32,
            TMAX_ATTRIBUTES=",,",
            TMIN=20,
            TMIN_ATTRIBUTES=",,",
        ),
    ]


@pytest.fixture
def db(sql_dir: Path) -> Generator[WeatherDatabase, None, None]:
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    # Close and remove the file so DuckDB can create a fresh database
    tmp_path.unlink(missing_ok=True)

    # Create and yield the database
    db = WeatherDatabase(tmp_path, sql_dir)
    yield db

    # Cleanup
    db.close()
    tmp_path.unlink(missing_ok=True)


def test_init_schema(db: WeatherDatabase) -> None:
    """Test database schema initialization"""
    # Check that tables were created
    result = db.conn.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN ('weather_station', 'weather_data')
    """).fetchall()

    assert len(result) == 2
    table_names = {row[0] for row in result}
    assert "weather_station" in table_names
    assert "weather_data" in table_names


def test_upsert_station(db: WeatherDatabase, sample_station: WeatherStation) -> None:
    """Test upserting station data"""
    # Insert station
    db.upsert_station(sample_station)

    # Verify insertion
    result = db.conn.execute(
        """
        SELECT station_id, station_name, latitude, longitude, elevation
        FROM weather_station
        WHERE station_id = ?
    """,
        [sample_station.station_id],
    ).fetchone()

    assert result is not None
    assert result[0] == sample_station.station_id
    assert result[1] == sample_station.name
    assert Decimal(str(result[2])) == sample_station.latitude
    assert Decimal(str(result[3])) == sample_station.longitude
    assert Decimal(str(result[4])) == sample_station.elevation


def test_upsert_weather_data(
    db: WeatherDatabase, sample_weather_data: list[WeatherData]
) -> None:
    """Test upserting weather data"""
    # Insert weather data
    db.upsert_weather_data(sample_weather_data)

    # Verify insertion
    result = db.conn.execute(
        """
        SELECT station_id, date, precipitation, snowfall, snow_depth, temp_max, temp_min
        FROM weather_data
        WHERE station_id = ?
        ORDER BY date
    """,
        [sample_weather_data[0].station_id],
    ).fetchall()

    assert len(result) == 2

    # Check first record
    assert result[0][0] == sample_weather_data[0].station_id
    assert result[0][1] == sample_weather_data[0].date
    assert Decimal(str(result[0][2])) == sample_weather_data[0].precipitation
    assert Decimal(str(result[0][3])) == sample_weather_data[0].snowfall
    assert Decimal(str(result[0][4])) == sample_weather_data[0].snow_depth
    assert result[0][5] == sample_weather_data[0].temp_max
    assert result[0][6] == sample_weather_data[0].temp_min

    # Check second record
    assert result[1][0] == sample_weather_data[1].station_id
    assert result[1][1] == sample_weather_data[1].date
    assert Decimal(str(result[1][2])) == sample_weather_data[1].precipitation
    assert Decimal(str(result[1][3])) == sample_weather_data[1].snowfall
    assert Decimal(str(result[1][4])) == sample_weather_data[1].snow_depth
    assert result[1][5] == sample_weather_data[1].temp_max
    assert result[1][6] == sample_weather_data[1].temp_min


def test_upsert_weather_data_empty(db: WeatherDatabase) -> None:
    """Test upserting empty weather data list"""
    # Should not raise any errors
    db.upsert_weather_data([])

    # Verify no data was inserted
    result = db.conn.execute("SELECT COUNT(*) FROM weather_data").fetchone()
    assert result is not None
    assert result[0] == 0


def test_database_context_manager(sql_dir: Path) -> None:
    """Test database context manager"""
    with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as tmp:
        db_path = Path(tmp.name)

    # Close and remove the file so DuckDB can create fresh database
    db_path.unlink(missing_ok=True)

    try:
        # Use context manager to create and close database
        with WeatherDatabase(db_path, sql_dir) as db:
            # Verify connection works
            result = db.conn.execute("SELECT 1").fetchone()
            assert result is not None
            assert result[0] == 1

        # Verify connection is closed
        with pytest.raises(duckdb.ConnectionException):
            db.conn.execute("SELECT 1")
    finally:
        # Clean up the database file
        db_path.unlink(missing_ok=True)
