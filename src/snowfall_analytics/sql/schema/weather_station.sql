CREATE TABLE IF NOT EXISTS weather_station (
    station_id VARCHAR NOT NULL,
    station_name VARCHAR NOT NULL,
    latitude DECIMAL,
    longitude DECIMAL,
    elevation DECIMAL,
    PRIMARY KEY (station_id)
);
