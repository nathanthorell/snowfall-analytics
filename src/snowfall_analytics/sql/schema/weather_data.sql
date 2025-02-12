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
